from __future__ import annotations

from agent.text2sql.generator import execute_generated_question
from agent.text2sql.llm_client import MockSqlGenerationClient, SqlGenerationRequest
from agent.text2sql.provider import (
    HttpJsonSqlGenerationClient,
    Text2SqlProviderConfigError,
    get_sql_generation_provider,
    parse_sql_generation_response,
)
from agent.text2sql.validator import Text2SqlValidationError, validate_generated_sql


def test_validate_generated_sql_accepts_allowlisted_select_with_limit() -> None:
    result = validate_generated_sql(
        """
        select campaign_id, roas
        from ai_native.ai_campaign_roi_summary
        order by roas desc
        limit 5
        """
    )

    assert result.referenced_tables == ("ai_native.ai_campaign_roi_summary",)
    assert result.limit == 5


def test_validate_generated_sql_rejects_write_statement() -> None:
    try:
        validate_generated_sql("delete from ai_native.ai_campaign_roi_summary")
    except Text2SqlValidationError as exc:
        assert "Only SELECT or WITH" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlValidationError")


def test_validate_generated_sql_rejects_disallowed_table() -> None:
    try:
        validate_generated_sql("select * from raw.ig_posts limit 5")
    except Text2SqlValidationError as exc:
        assert "disallowed table" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlValidationError")


def test_validate_generated_sql_rejects_non_aggregate_without_limit() -> None:
    try:
        validate_generated_sql("select campaign_id from ai_native.ai_campaign_roi_summary")
    except Text2SqlValidationError as exc:
        assert "explicit LIMIT" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlValidationError")


def test_validate_generated_sql_allows_aggregate_without_limit() -> None:
    result = validate_generated_sql(
        """
        select count(*) as campaign_count
        from ai_native.ai_campaign_roi_summary
        """
    )

    assert result.limit is None


def test_mock_generator_executes_valid_generated_sql() -> None:
    class FakeColumn:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeCursor:
        description = [
            FakeColumn("campaign_id"),
            FakeColumn("campaign_name"),
            FakeColumn("roas"),
        ]

        def __init__(self) -> None:
            self.executed_sql: list[str] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def execute(self, sql: str) -> None:
            self.executed_sql.append(sql)

        def fetchmany(self, limit: int):
            return [("camp_000029", "beauty_kr_conversion_000029", 0.5969)]

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()

        def cursor(self):
            return self.cursor_instance

    conn = FakeConnection()

    result = execute_generated_question(
        question="Which campaigns have the highest ROAS?",
        conn=conn,
        client=MockSqlGenerationClient(),
    )

    assert result.mode == "llm_generated_sql_v2_mock"
    assert result.row_count == 1
    assert result.rows[0]["campaign_id"] == "camp_000029"
    assert result.validation.referenced_tables == ("ai_native.ai_campaign_roi_summary",)
    assert conn.cursor_instance.executed_sql[0] == "set local statement_timeout = 5000"


def test_mock_provider_supports_campaign_objective_aggregation() -> None:
    response = MockSqlGenerationClient().generate_sql(
        SqlGenerationRequest(
            question="Show average ROAS and net payment amount by campaign objective.",
            schema_context="unit test schema",
        )
    )

    assert response.answerability == "answerable"
    assert response.expected_tables == ("ai_native.ai_campaign_roi_summary",)
    assert "group by campaign_objective" in response.sql


def test_provider_factory_defaults_to_mock() -> None:
    provider = get_sql_generation_provider({})

    assert provider.kind == "mock"
    assert provider.mode == "llm_generated_sql_v2_mock"
    assert isinstance(provider.client, MockSqlGenerationClient)


def test_provider_factory_builds_http_json_client() -> None:
    provider = get_sql_generation_provider(
        {
            "TEXT2SQL_PROVIDER": "http_json",
            "TEXT2SQL_PROVIDER_URL": "https://example.test/text2sql",
            "TEXT2SQL_PROVIDER_API_KEY": "unit-test-key",
            "TEXT2SQL_PROVIDER_TIMEOUT_SECONDS": "7",
        }
    )

    assert provider.kind == "http_json"
    assert provider.mode == "llm_generated_sql_v2_http_json"
    assert isinstance(provider.client, HttpJsonSqlGenerationClient)
    assert provider.client.url == "https://example.test/text2sql"
    assert provider.client.api_key == "unit-test-key"
    assert provider.client.timeout_seconds == 7


def test_provider_factory_requires_http_json_url() -> None:
    try:
        get_sql_generation_provider({"TEXT2SQL_PROVIDER": "http_json"})
    except Text2SqlProviderConfigError as exc:
        assert "TEXT2SQL_PROVIDER_URL is required" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlProviderConfigError")


def test_parse_sql_generation_response_validates_contract() -> None:
    response = parse_sql_generation_response(
        {
            "answerability": "answerable",
            "sql": "select campaign_id from ai_native.ai_campaign_roi_summary limit 5",
            "expected_tables": ["ai_native.ai_campaign_roi_summary"],
            "reason": "unit test",
        }
    )

    assert response.answerability == "answerable"
    assert response.expected_tables == ("ai_native.ai_campaign_roi_summary",)
