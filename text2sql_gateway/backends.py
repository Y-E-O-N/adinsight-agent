from __future__ import annotations

import json
import os
import random
import time
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent.text2sql.generator import validate_intent_contract
from agent.text2sql.llm_client import (
    MockSqlGenerationClient,
    SqlGenerationRequest,
    SqlGenerationResponse,
)
from agent.text2sql.provider import Text2SqlProviderConfigError, parse_sql_generation_response
from agent.text2sql.schema_catalog import find_best_intent_for_question
from agent.text2sql.usage import LlmUsage, build_llm_usage
from agent.text2sql.validator import validate_generated_sql

DEFAULT_BACKEND = "mock"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"
DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TEMPERATURE = 0.0
DEFAULT_SEED = 7
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_INITIAL_DELAY_SECONDS = 1.0
DEFAULT_RETRY_MAX_DELAY_SECONDS = 8.0
RETRYABLE_HTTP_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
CONTENT_SAFETY_REFUSAL_REASON = (
    "The request is outside the allowed neutral analytics scope."
)
CONTENT_SAFETY_SIGNAL_TERMS = (
    "stupid",
    "loser",
    "losers",
    "abusive",
    "insult",
    "insulting",
    "sexually explicit",
    "sexual",
    "violent threat",
    "violent threats",
    "violent",
    "멍청",
    "조롱",
    "성적인",
    "폭력",
    "위협",
)

TEXT2SQL_CONTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "answerability": {
            "type": "string",
            "enum": ["answerable", "not_answerable"],
        },
        "sql": {
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ],
        },
        "expected_tables": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reason": {"type": "string"},
    },
    "required": ["answerability", "sql", "expected_tables", "reason"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class GatewayGeneration:
    response: SqlGenerationResponse
    mode: str


class GatewayBackendError(RuntimeError):
    pass


def generate_sql_with_backend(
    request: SqlGenerationRequest,
    env: Mapping[str, str] | None = None,
) -> GatewayGeneration:
    resolved_env = os.environ if env is None else env
    backend = resolved_env.get("TEXT2SQL_GATEWAY_BACKEND", DEFAULT_BACKEND).lower()

    if backend == "mock":
        return GatewayGeneration(
            response=MockSqlGenerationClient().generate_sql(request),
            mode="text2sql_gateway_mock_v1",
        )

    if backend == "ollama":
        return generate_with_ollama(request, resolved_env)

    if backend == "openai":
        return generate_with_openai(request, resolved_env)

    if backend == "gemini":
        return generate_with_gemini(request, resolved_env)

    if backend in {"dual", "gemini_openai_fallback"}:
        return generate_with_gemini_openai_fallback(request, resolved_env)

    raise GatewayBackendError(
        "Unsupported TEXT2SQL_GATEWAY_BACKEND="
        f"{backend!r}; expected 'mock', 'ollama', 'openai', 'gemini', or 'dual'."
    )


def generate_with_ollama(
    request: SqlGenerationRequest,
    env: Mapping[str, str],
) -> GatewayGeneration:
    url = env.get("TEXT2SQL_OLLAMA_URL", DEFAULT_OLLAMA_URL)
    model = env.get("TEXT2SQL_OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    timeout_seconds = int(env.get("TEXT2SQL_OLLAMA_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    payload = {
        "model": model,
        "prompt": build_text2sql_prompt(request),
        "stream": False,
        "format": "json",
        "options": build_ollama_options(env),
    }
    http_request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started_at = perf_counter()
    try:
        with urlopen(http_request, timeout=timeout_seconds) as response:
            model_payload = json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise GatewayBackendError(
            f"Local model request timed out after {timeout_seconds}s"
        ) from exc
    except URLError as exc:
        raise GatewayBackendError(f"Local model request failed: {exc.reason}") from exc

    elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
    usage = build_llm_usage(
        provider="ollama",
        model=model,
        payload=model_payload,
        elapsed_ms=elapsed_ms,
        env=env,
    )
    return GatewayGeneration(
        response=with_usage(
            sanitize_refusal_reason(parse_model_payload(model_payload), request.question),
            usage,
        ),
        mode="text2sql_gateway_ollama_v1",
    )


def generate_with_openai(
    request: SqlGenerationRequest,
    env: Mapping[str, str],
) -> GatewayGeneration:
    api_key = env.get("TEXT2SQL_OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    if not api_key:
        raise GatewayBackendError("TEXT2SQL_OPENAI_API_KEY or OPENAI_API_KEY is required.")

    url = env.get("TEXT2SQL_OPENAI_URL", DEFAULT_OPENAI_URL)
    model = env.get("TEXT2SQL_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    timeout_seconds = int(env.get("TEXT2SQL_OPENAI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    retry_policy = build_retry_policy(env, "OPENAI")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_text2sql_system_prompt()},
            {"role": "user", "content": build_text2sql_user_prompt(request)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "adinsight_text2sql_generation",
                "strict": True,
                "schema": TEXT2SQL_CONTRACT_SCHEMA,
            },
        },
    }
    if "TEXT2SQL_OPENAI_TEMPERATURE" in env:
        payload["temperature"] = float(env["TEXT2SQL_OPENAI_TEMPERATURE"])
    http_request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    model_payload, elapsed_ms = post_json(http_request, timeout_seconds, retry_policy)
    usage = build_llm_usage(
        provider="openai",
        model=model,
        payload=model_payload,
        elapsed_ms=elapsed_ms,
        env=env,
    )
    return GatewayGeneration(
        response=with_usage(
            sanitize_refusal_reason(parse_model_payload(model_payload), request.question),
            usage,
        ),
        mode="text2sql_gateway_openai_v1",
    )


def generate_with_gemini(
    request: SqlGenerationRequest,
    env: Mapping[str, str],
) -> GatewayGeneration:
    api_key = env.get("TEXT2SQL_GEMINI_API_KEY") or env.get("GEMINI_API_KEY")
    if not api_key:
        raise GatewayBackendError("TEXT2SQL_GEMINI_API_KEY or GEMINI_API_KEY is required.")

    url = env.get("TEXT2SQL_GEMINI_URL", DEFAULT_GEMINI_URL)
    model = env.get("TEXT2SQL_GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    timeout_seconds = int(env.get("TEXT2SQL_GEMINI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    retry_policy = build_retry_policy(env, "GEMINI")
    payload = {
        "model": model,
        "input": f"{build_text2sql_system_prompt()}\n\n{build_text2sql_user_prompt(request)}",
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": TEXT2SQL_CONTRACT_SCHEMA,
        },
    }
    http_request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    model_payload, elapsed_ms = post_json(http_request, timeout_seconds, retry_policy)
    usage = build_llm_usage(
        provider="gemini",
        model=model,
        payload=model_payload,
        elapsed_ms=elapsed_ms,
        env=env,
    )
    return GatewayGeneration(
        response=with_usage(
            sanitize_refusal_reason(parse_model_payload(model_payload), request.question),
            usage,
        ),
        mode="text2sql_gateway_gemini_v1",
    )


def generate_with_gemini_openai_fallback(
    request: SqlGenerationRequest,
    env: Mapping[str, str],
) -> GatewayGeneration:
    usage_attempts: list[LlmUsage] = []
    fallback_reason: str

    try:
        primary_generation = generate_with_gemini(request, env)
        usage_attempts.extend(response_usage_attempts(primary_generation.response))
        fallback_reason_candidate = find_gateway_fallback_reason(
            primary_generation.response,
            request,
        )
        if fallback_reason_candidate is None:
            return GatewayGeneration(
                response=with_fallback_metadata(
                    primary_generation.response,
                    usage_attempts,
                    fallback_reason=None,
                ),
                mode="text2sql_gateway_gemini_openai_fallback_v1",
            )
        fallback_reason = fallback_reason_candidate
    except GatewayBackendError as exc:
        fallback_reason = f"primary_provider_error:{exc}"

    fallback_generation = generate_with_openai(request, env)
    usage_attempts.extend(response_usage_attempts(fallback_generation.response))
    return GatewayGeneration(
        response=with_fallback_metadata(
            fallback_generation.response,
            usage_attempts,
            fallback_reason=fallback_reason,
        ),
        mode="text2sql_gateway_gemini_openai_fallback_v1",
    )


def find_gateway_fallback_reason(
    response: SqlGenerationResponse,
    request: SqlGenerationRequest,
) -> str | None:
    if response.answerability != "answerable" or response.sql is None:
        if has_content_safety_signal(request.question, response.reason):
            return "primary_content_safety_refusal"
        return None

    try:
        validate_generated_sql(response.sql)
        validate_intent_contract(response.sql, find_best_intent_for_question(request.question))
    except Exception as exc:
        return f"primary_sql_validation_failed:{exc}"

    return None


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int
    initial_delay_seconds: float
    max_delay_seconds: float


def build_retry_policy(env: Mapping[str, str], provider_prefix: str) -> RetryPolicy:
    return RetryPolicy(
        max_retries=int(
            env.get(
                f"TEXT2SQL_{provider_prefix}_MAX_RETRIES",
                env.get("TEXT2SQL_PROVIDER_MAX_RETRIES", DEFAULT_MAX_RETRIES),
            )
        ),
        initial_delay_seconds=float(
            env.get(
                f"TEXT2SQL_{provider_prefix}_RETRY_INITIAL_DELAY_SECONDS",
                env.get(
                    "TEXT2SQL_PROVIDER_RETRY_INITIAL_DELAY_SECONDS",
                    DEFAULT_RETRY_INITIAL_DELAY_SECONDS,
                ),
            )
        ),
        max_delay_seconds=float(
            env.get(
                f"TEXT2SQL_{provider_prefix}_RETRY_MAX_DELAY_SECONDS",
                env.get(
                    "TEXT2SQL_PROVIDER_RETRY_MAX_DELAY_SECONDS",
                    DEFAULT_RETRY_MAX_DELAY_SECONDS,
                ),
            )
        ),
    )


def post_json(
    http_request: Request,
    timeout_seconds: int,
    retry_policy: RetryPolicy | None = None,
) -> tuple[object, float]:
    resolved_retry_policy = retry_policy or RetryPolicy(
        max_retries=0,
        initial_delay_seconds=DEFAULT_RETRY_INITIAL_DELAY_SECONDS,
        max_delay_seconds=DEFAULT_RETRY_MAX_DELAY_SECONDS,
    )
    started_at = perf_counter()
    attempt = 0
    last_error: Exception | None = None
    while attempt <= resolved_retry_policy.max_retries:
        try:
            with urlopen(http_request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, round((perf_counter() - started_at) * 1000, 3)
        except TimeoutError:
            last_error = GatewayBackendError(
                f"Provider request timed out after {timeout_seconds}s"
            )
        except HTTPError as exc:
            error_detail = exc.read().decode("utf-8", errors="replace")[:500]
            last_error = GatewayBackendError(
                f"Provider request failed with HTTP {exc.code}: {error_detail}"
            )
            if exc.code not in RETRYABLE_HTTP_STATUS_CODES:
                raise last_error from exc
        except URLError as exc:
            last_error = GatewayBackendError(f"Provider request failed: {exc.reason}")

        if attempt >= resolved_retry_policy.max_retries:
            break
        sleep_before_retry(attempt, resolved_retry_policy)
        attempt += 1

    if last_error is not None:
        raise last_error
    raise GatewayBackendError("Provider request failed for an unknown reason.")


def sleep_before_retry(attempt: int, retry_policy: RetryPolicy) -> None:
    delay = min(
        retry_policy.initial_delay_seconds * (2 ** attempt),
        retry_policy.max_delay_seconds,
    )
    jittered_delay = delay * (1 + random.random())
    time.sleep(jittered_delay)


def build_text2sql_system_prompt() -> str:
    return """
You are a Text2SQL generator for AdInsight.
Return only one JSON object with this exact shape:
{
  "answerability": "answerable" or "not_answerable",
  "sql": "SELECT ..." or null,
  "expected_tables": ["schema.table"],
  "reason": "short reason"
}

Rules:
- Generate PostgreSQL SQL only.
- First route the question through the schema context's Natural-Language Intent
  Routing Catalog: major category -> middle category -> minor intent.
- Use the selected minor intent's table, required output columns, and limit policy.
- Use only allowed tables and columns from the schema context's Actual Allowed
  Table and Column Catalog.
- Do not treat rulebook concept names as SQL column names unless they are listed
  in the actual column catalog.
- Before generating SQL, apply the Text2SQL Positive Criteria Rulebook section
  from the schema context when it is present.
- Before generating SQL, apply the Text2SQL LLM Decision Guide section from
  the schema context when it is present.
- Use SELECT or WITH only.
- Add LIMIT only when the selected intent policy or user question calls for it.
- For latest prediction-monitor questions, filter to max(scoring_snapshot_date).
- Use deterministic ORDER BY columns before LIMIT.
- If the user asks for MAE, compute avg(absolute_roas_prediction_error) as mae.
- If the user asks for bias, compute avg(roas_prediction_error) as bias.
- If the requested metric is unavailable, such as views, impressions, or clicks,
  return not_answerable instead of inventing a proxy.
- Refuse if the question is outside the schema context, asks for unsafe SQL, or asks for abusive/sexual/violent content classification.
- For abusive, sexual, or violent content-safety refusals, do not quote or repeat user-provided unsafe wording. Use a generic neutral reason.

Examples:
Question: Which campaigns have the highest ROAS?
JSON: {"answerability":"answerable","sql":"select campaign_id, campaign_name, roas, net_payment_amount_krw from ai_native.ai_campaign_roi_summary order by roas desc, net_payment_amount_krw desc limit 5","expected_tables":["ai_native.ai_campaign_roi_summary"],"reason":"Orders campaign ROI summary by ROAS."}

Question: 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘.
JSON: {"answerability":"answerable","sql":"select model_name, avg(absolute_roas_prediction_error) as mae, avg(roas_prediction_error) as bias from marts.mart_campaign_roas_prediction_monitor where scoring_snapshot_date = (select max(scoring_snapshot_date) from marts.mart_campaign_roas_prediction_monitor) group by model_name order by model_name","expected_tables":["marts.mart_campaign_roas_prediction_monitor"],"reason":"Computes latest prediction error metrics."}

Question: Delete campaigns with negative ROAS from the database.
JSON: {"answerability":"not_answerable","sql":null,"expected_tables":[],"reason":"Unsafe write SQL is not allowed."}
""".strip()


def build_text2sql_user_prompt(request: SqlGenerationRequest) -> str:
    return f"""
Schema context:
{request.schema_context}

Question:
{request.question}
""".strip()


def build_text2sql_prompt(request: SqlGenerationRequest) -> str:
    return f"""
{build_text2sql_system_prompt()}

Schema context:
{request.schema_context}

Question:
{request.question}
""".strip()


def build_ollama_options(env: Mapping[str, str]) -> dict[str, int | float]:
    return {
        "temperature": float(env.get("TEXT2SQL_OLLAMA_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "seed": int(env.get("TEXT2SQL_OLLAMA_SEED", DEFAULT_SEED)),
    }


def parse_model_payload(payload: object) -> SqlGenerationResponse:
    if not isinstance(payload, dict):
        return not_answerable("Model response was not a JSON object.")

    candidate = extract_contract_candidate(payload)
    try:
        return parse_sql_generation_response(candidate)
    except Text2SqlProviderConfigError as exc:
        return not_answerable(f"Model did not return a valid Text2SQL contract: {exc}")


def extract_contract_candidate(payload: dict[str, object]) -> object:
    if "answerability" in payload:
        return payload

    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return parse_json_text(output_text)

    steps = payload.get("steps")
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            content_parts = step.get("content")
            if not isinstance(content_parts, list):
                continue
            for content_part in content_parts:
                if not isinstance(content_part, dict):
                    continue
                text = content_part.get("text")
                if isinstance(text, str):
                    return parse_json_text(text)

    response_text = payload.get("response")
    if isinstance(response_text, str):
        return parse_json_text(response_text)

    message = payload.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return parse_json_text(content)

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            choice_message = first_choice.get("message")
            if isinstance(choice_message, dict):
                content = choice_message.get("content")
                if isinstance(content, str):
                    return parse_json_text(content)

    return payload


def parse_json_text(text: str) -> object:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned.removeprefix("json").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"answerability": "not_answerable", "sql": None, "expected_tables": [], "reason": ""}


def not_answerable(reason: str) -> SqlGenerationResponse:
    return SqlGenerationResponse(
        answerability="not_answerable",
        sql=None,
        expected_tables=(),
        reason=reason,
    )


def sanitize_refusal_reason(
    response: SqlGenerationResponse,
    question: str,
) -> SqlGenerationResponse:
    if response.answerability != "not_answerable":
        return response
    if not has_content_safety_signal(question, response.reason):
        return response

    return SqlGenerationResponse(
        answerability=response.answerability,
        sql=response.sql,
        expected_tables=response.expected_tables,
        reason=CONTENT_SAFETY_REFUSAL_REASON,
        usage=response.usage,
        usage_attempts=response.usage_attempts,
        fallback_reason=response.fallback_reason,
    )


def has_content_safety_signal(question: str, reason: str) -> bool:
    combined = f"{question}\n{reason}".casefold()
    return any(term.casefold() in combined for term in CONTENT_SAFETY_SIGNAL_TERMS)


def with_usage(response: SqlGenerationResponse, usage: LlmUsage) -> SqlGenerationResponse:
    return SqlGenerationResponse(
        answerability=response.answerability,
        sql=response.sql,
        expected_tables=response.expected_tables,
        reason=response.reason,
        usage=usage,
        usage_attempts=response.usage_attempts,
        fallback_reason=response.fallback_reason,
    )


def response_usage_attempts(response: SqlGenerationResponse) -> tuple[LlmUsage, ...]:
    if response.usage_attempts:
        return response.usage_attempts
    if response.usage is not None:
        return (response.usage,)
    return ()


def with_fallback_metadata(
    response: SqlGenerationResponse,
    usage_attempts: list[LlmUsage],
    fallback_reason: str | None,
) -> SqlGenerationResponse:
    return SqlGenerationResponse(
        answerability=response.answerability,
        sql=response.sql,
        expected_tables=response.expected_tables,
        reason=response.reason,
        usage=response.usage,
        usage_attempts=tuple(usage_attempts),
        fallback_reason=fallback_reason,
    )
