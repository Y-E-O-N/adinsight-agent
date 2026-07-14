from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agent.text2sql.llm_client import (
    MockSqlGenerationClient,
    SqlGenerationClient,
    SqlGenerationRequest,
    SqlGenerationResponse,
)
from agent.text2sql.usage import LlmUsage

DEFAULT_PROVIDER_KIND = "mock"
DEFAULT_HTTP_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class SqlGenerationProvider:
    kind: str
    mode: str
    client: SqlGenerationClient


class Text2SqlProviderConfigError(ValueError):
    pass


class HttpJsonSqlGenerationClient:
    """Adapter for an external Text2SQL gateway that returns the v2 JSON contract."""

    def __init__(
        self,
        url: str,
        api_key: str | None = None,
        timeout_seconds: int = DEFAULT_HTTP_TIMEOUT_SECONDS,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def generate_sql(self, request: SqlGenerationRequest) -> SqlGenerationResponse:
        body = json.dumps(
            {
                "question": request.question,
                "schema_context": request.schema_context,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        http_request = Request(
            self.url,
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(http_request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            error_detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise Text2SqlProviderConfigError(
                f"Text2SQL provider request failed with HTTP {exc.code}: {error_detail}"
            ) from exc
        except URLError as exc:
            raise Text2SqlProviderConfigError(
                f"Text2SQL provider request failed: {exc.reason}"
            ) from exc

        return parse_sql_generation_response(payload)


def get_sql_generation_provider(
    env: Mapping[str, str] | None = None,
) -> SqlGenerationProvider:
    resolved_env = os.environ if env is None else env
    kind = resolved_env.get("TEXT2SQL_PROVIDER", DEFAULT_PROVIDER_KIND).lower()

    if kind == "mock":
        return SqlGenerationProvider(
            kind=kind,
            mode="llm_generated_sql_v2_mock",
            client=MockSqlGenerationClient(),
        )

    if kind == "http_json":
        url = resolved_env.get("TEXT2SQL_PROVIDER_URL")
        if not url:
            raise Text2SqlProviderConfigError(
                "TEXT2SQL_PROVIDER_URL is required when TEXT2SQL_PROVIDER=http_json."
            )

        timeout_seconds = int(
            resolved_env.get("TEXT2SQL_PROVIDER_TIMEOUT_SECONDS", DEFAULT_HTTP_TIMEOUT_SECONDS)
        )
        return SqlGenerationProvider(
            kind=kind,
            mode="llm_generated_sql_v2_http_json",
            client=HttpJsonSqlGenerationClient(
                url=url,
                api_key=resolved_env.get("TEXT2SQL_PROVIDER_API_KEY"),
                timeout_seconds=timeout_seconds,
            ),
        )

    raise Text2SqlProviderConfigError(
        f"Unsupported TEXT2SQL_PROVIDER={kind!r}; expected 'mock' or 'http_json'."
    )


def parse_sql_generation_response(payload: object) -> SqlGenerationResponse:
    if not isinstance(payload, dict):
        raise Text2SqlProviderConfigError("Text2SQL provider response must be a JSON object.")

    answerability = payload.get("answerability")
    if answerability not in {"answerable", "not_answerable"}:
        raise Text2SqlProviderConfigError(
            "Text2SQL provider response must include answerability="
            "'answerable' or 'not_answerable'."
        )

    sql = payload.get("sql")
    if sql is not None and not isinstance(sql, str):
        raise Text2SqlProviderConfigError("Text2SQL provider response sql must be a string or null.")

    expected_tables = payload.get("expected_tables", [])
    if not isinstance(expected_tables, list) or not all(
        isinstance(table_name, str) for table_name in expected_tables
    ):
        raise Text2SqlProviderConfigError(
            "Text2SQL provider response expected_tables must be a list of strings."
        )

    reason = payload.get("reason", "")
    if not isinstance(reason, str):
        raise Text2SqlProviderConfigError("Text2SQL provider response reason must be a string.")

    return SqlGenerationResponse(
        answerability=answerability,
        sql=sql,
        expected_tables=tuple(expected_tables),
        reason=reason,
        usage=parse_usage(payload.get("usage")),
        usage_attempts=parse_usage_attempts(payload.get("usage_attempts")),
        fallback_reason=parse_optional_str(payload.get("fallback_reason")),
    )


def parse_usage_attempts(payload: object) -> tuple[LlmUsage, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise Text2SqlProviderConfigError(
            "Text2SQL provider response usage_attempts must be a list."
        )
    attempts: list[LlmUsage] = []
    for item in payload:
        usage = parse_usage(item)
        if usage is not None:
            attempts.append(usage)
    return tuple(attempts)


def parse_usage(payload: object) -> LlmUsage | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise Text2SqlProviderConfigError("Text2SQL provider response usage must be an object.")

    return LlmUsage(
        provider=str(payload.get("provider", "")),
        model=payload.get("model") if isinstance(payload.get("model"), str) else None,
        input_tokens=parse_optional_int(payload.get("input_tokens")),
        cached_input_tokens=parse_optional_int(payload.get("cached_input_tokens")),
        output_tokens=parse_optional_int(payload.get("output_tokens")),
        total_tokens=parse_optional_int(payload.get("total_tokens")),
        estimated_cost_usd=parse_optional_float(payload.get("estimated_cost_usd")),
        elapsed_ms=parse_optional_float(payload.get("elapsed_ms")),
        pricing_source=(
            payload.get("pricing_source") if isinstance(payload.get("pricing_source"), str) else None
        ),
    )


def parse_optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def parse_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def parse_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None
