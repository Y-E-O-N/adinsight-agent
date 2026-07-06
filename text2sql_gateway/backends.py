from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent.text2sql.llm_client import (
    MockSqlGenerationClient,
    SqlGenerationRequest,
    SqlGenerationResponse,
)
from agent.text2sql.provider import Text2SqlProviderConfigError, parse_sql_generation_response

DEFAULT_BACKEND = "mock"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-5.5"
DEFAULT_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_TEMPERATURE = 0.0
DEFAULT_SEED = 7

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

    raise GatewayBackendError(
        "Unsupported TEXT2SQL_GATEWAY_BACKEND="
        f"{backend!r}; expected 'mock', 'ollama', 'openai', or 'gemini'."
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

    try:
        with urlopen(http_request, timeout=timeout_seconds) as response:
            model_payload = json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise GatewayBackendError(
            f"Local model request timed out after {timeout_seconds}s"
        ) from exc
    except URLError as exc:
        raise GatewayBackendError(f"Local model request failed: {exc.reason}") from exc

    return GatewayGeneration(
        response=parse_model_payload(model_payload),
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
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": build_text2sql_system_prompt()},
            {"role": "user", "content": build_text2sql_user_prompt(request)},
        ],
        "temperature": float(env.get("TEXT2SQL_OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "adinsight_text2sql_generation",
                "strict": True,
                "schema": TEXT2SQL_CONTRACT_SCHEMA,
            },
        },
    }
    http_request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    model_payload = post_json(http_request, timeout_seconds)
    return GatewayGeneration(
        response=parse_model_payload(model_payload),
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

    model_payload = post_json(http_request, timeout_seconds)
    return GatewayGeneration(
        response=parse_model_payload(model_payload),
        mode="text2sql_gateway_gemini_v1",
    )


def post_json(http_request: Request, timeout_seconds: int) -> object:
    try:
        with urlopen(http_request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except TimeoutError as exc:
        raise GatewayBackendError(
            f"Provider request timed out after {timeout_seconds}s"
        ) from exc
    except HTTPError as exc:
        raise GatewayBackendError(
            f"Provider request failed with HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        raise GatewayBackendError(f"Provider request failed: {exc.reason}") from exc


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
- Use only allowed tables from the schema context.
- Use SELECT or WITH only.
- Add an explicit LIMIT for non-aggregate list queries.
- For latest prediction-monitor questions, filter to max(scoring_snapshot_date).
- Use deterministic ORDER BY columns before LIMIT.
- If the user asks for MAE, compute avg(absolute_roas_prediction_error) as mae.
- If the user asks for bias, compute avg(roas_prediction_error) as bias.
- Refuse if the question is outside the schema context, asks for unsafe SQL, or asks for abusive/sexual/violent content classification.

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
        return not_answerable("Local model response was not a JSON object.")

    candidate = extract_contract_candidate(payload)
    try:
        return parse_sql_generation_response(candidate)
    except Text2SqlProviderConfigError as exc:
        return not_answerable(f"Local model did not return a valid Text2SQL contract: {exc}")


def extract_contract_candidate(payload: dict[str, object]) -> object:
    if "answerability" in payload:
        return payload

    output_text = payload.get("output_text")
    if isinstance(output_text, str):
        return parse_json_text(output_text)

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
