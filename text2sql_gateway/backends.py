from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import URLError
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
DEFAULT_TIMEOUT_SECONDS = 60


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

    raise GatewayBackendError(
        f"Unsupported TEXT2SQL_GATEWAY_BACKEND={backend!r}; expected 'mock' or 'ollama'."
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
    except URLError as exc:
        raise GatewayBackendError(f"Local model request failed: {exc.reason}") from exc

    return GatewayGeneration(
        response=parse_model_payload(model_payload),
        mode="text2sql_gateway_ollama_v1",
    )


def build_text2sql_prompt(request: SqlGenerationRequest) -> str:
    return f"""
You are a Text2SQL generator for AdInsight.
Return only one JSON object with this exact shape:
{{
  "answerability": "answerable" or "not_answerable",
  "sql": "SELECT ..." or null,
  "expected_tables": ["schema.table"],
  "reason": "short reason"
}}

Rules:
- Generate PostgreSQL SQL only.
- Use only allowed tables from the schema context.
- Use SELECT or WITH only.
- Add an explicit LIMIT for non-aggregate list queries.
- Refuse if the question is outside the schema context.

Schema context:
{request.schema_context}

Question:
{request.question}
""".strip()


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
