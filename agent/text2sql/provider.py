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
    )
