from __future__ import annotations

from agent.text2sql.generator import (
    build_schema_context_v1,
    execute_generated_question,
    validate_intent_contract,
)
from agent.text2sql.llm_client import (
    MockSqlGenerationClient,
    SqlGenerationRequest,
    SqlGenerationResponse,
)
from agent.text2sql.provider import (
    HttpJsonSqlGenerationClient,
    Text2SqlProviderConfigError,
    get_sql_generation_provider,
    parse_sql_generation_response,
)
from agent.text2sql.schema_catalog import find_best_intent_for_question
from agent.text2sql.validator import (
    Text2SqlValidationError,
    extract_select_output_names,
    validate_generated_sql,
)


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


def test_validate_generated_sql_rejects_unknown_column_before_db_execution() -> None:
    try:
        validate_generated_sql(
            """
            select objective, avg(roas) as avg_roas
            from ai_native.ai_campaign_roi_summary
            group by objective
            """
        )
    except Text2SqlValidationError as exc:
        assert "unknown column: objective" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlValidationError")


def test_validate_generated_sql_accepts_known_qualified_join_columns() -> None:
    result = validate_generated_sql(
        """
        select
            monitor.campaign_id,
            roi.roas_performance_tier,
            monitor.absolute_roas_prediction_error
        from marts.mart_campaign_roas_prediction_monitor as monitor
        join ai_native.ai_campaign_roi_summary as roi
          on monitor.campaign_id = roi.campaign_id
        order by monitor.absolute_roas_prediction_error desc
        limit 10
        """
    )

    assert result.referenced_tables == (
        "marts.mart_campaign_roas_prediction_monitor",
        "ai_native.ai_campaign_roi_summary",
    )
    assert "monitor.campaign_id" in result.referenced_columns


def test_validate_generated_sql_rejects_non_aggregate_without_limit_or_order_by() -> None:
    try:
        validate_generated_sql("select campaign_id from ai_native.ai_campaign_roi_summary")
    except Text2SqlValidationError as exc:
        assert "deterministic ORDER BY" in str(exc)
    else:
        raise AssertionError("Expected Text2SqlValidationError")


def test_validate_generated_sql_allows_ordered_broad_list_without_limit() -> None:
    result = validate_generated_sql(
        """
        select creator_username, total_posts, sponsored_candidate_posts
        from ai_native.ai_creator_sponsored_summary
        where total_posts >= 2
          and sponsored_candidate_posts = 0
        order by total_posts desc, creator_username asc
        """
    )

    assert result.limit is None


def test_validate_generated_sql_allows_aggregate_without_limit() -> None:
    result = validate_generated_sql(
        """
        select count(*) as campaign_count
        from ai_native.ai_campaign_roi_summary
        """
    )

    assert result.limit is None


def test_extract_select_output_names_includes_aliases_and_qualified_columns() -> None:
    output_names = extract_select_output_names(
        """
        select
            monitor.campaign_id,
            roi.roas_performance_tier,
            count(*) as campaign_count,
            avg(monitor.absolute_roas_prediction_error) as mae
        from marts.mart_campaign_roas_prediction_monitor as monitor
        join ai_native.ai_campaign_roi_summary as roi
          on monitor.campaign_id = roi.campaign_id
        group by roi.roas_performance_tier
        """
    )

    assert "campaign_id" in output_names
    assert "roas_performance_tier" in output_names
    assert "campaign_count" in output_names
    assert "mae" in output_names


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


def test_generator_retries_once_after_column_preflight_failure() -> None:
    class FakeColumn:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeCursor:
        description = [
            FakeColumn("campaign_objective"),
            FakeColumn("avg_roas"),
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
            return [("conversion", 1.2)]

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()

        def cursor(self):
            return self.cursor_instance

    class RetryClient:
        def __init__(self) -> None:
            self.requests: list[SqlGenerationRequest] = []

        def generate_sql(self, request: SqlGenerationRequest) -> SqlGenerationResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                return SqlGenerationResponse(
                    answerability="answerable",
                    sql=(
                        "select objective, avg(roas) as avg_roas "
                        "from ai_native.ai_campaign_roi_summary "
                        "group by objective"
                    ),
                    expected_tables=("ai_native.ai_campaign_roi_summary",),
                    reason="unit test first attempt with hallucinated column",
                )

            return SqlGenerationResponse(
                answerability="answerable",
                sql=(
                    "select campaign_objective, avg(roas) as avg_roas "
                    "from ai_native.ai_campaign_roi_summary "
                    "group by campaign_objective"
                ),
                expected_tables=("ai_native.ai_campaign_roi_summary",),
                reason="unit test regenerated SQL",
            )

    client = RetryClient()
    result = execute_generated_question(
        question="Show average ROAS by campaign objective.",
        conn=FakeConnection(),
        client=client,
    )

    assert len(client.requests) == 2
    assert "Validator Retry Instruction" in client.requests[1].schema_context
    assert result.sql.startswith("select campaign_objective")


def test_generator_retries_after_intent_contract_failure() -> None:
    class FakeColumn:
        def __init__(self, name: str) -> None:
            self.name = name

    class FakeCursor:
        description = [
            FakeColumn("creator_username"),
            FakeColumn("has_engagement_signal"),
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
            return [("creator_1", True)]

    class FakeConnection:
        def __init__(self) -> None:
            self.cursor_instance = FakeCursor()

        def cursor(self):
            return self.cursor_instance

    class RetryClient:
        def __init__(self) -> None:
            self.requests: list[SqlGenerationRequest] = []

        def generate_sql(self, request: SqlGenerationRequest) -> SqlGenerationResponse:
            self.requests.append(request)
            if len(self.requests) == 1:
                return SqlGenerationResponse(
                    answerability="answerable",
                    sql=(
                        "select creator_username, total_posts "
                        "from ai_native.ai_creator_sponsored_summary "
                        "where has_engagement_signal = true "
                        "order by creator_username asc "
                        "limit 20"
                    ),
                    expected_tables=("ai_native.ai_creator_sponsored_summary",),
                    reason="unit test first attempt missing expected output column",
                )

            return SqlGenerationResponse(
                answerability="answerable",
                sql=(
                    "select creator_username, has_engagement_signal "
                    "from ai_native.ai_creator_sponsored_summary "
                    "where has_engagement_signal = true "
                    "order by creator_username asc "
                    "limit 20"
                ),
                expected_tables=("ai_native.ai_creator_sponsored_summary",),
                reason="unit test regenerated SQL",
            )

    client = RetryClient()
    result = execute_generated_question(
        question="Show the first 20 creators that have engagement signals available.",
        conn=FakeConnection(),
        client=client,
    )

    assert len(client.requests) == 2
    assert "missing required SELECT column" in client.requests[1].schema_context
    assert "has_engagement_signal" in result.sql


def test_objective_mae_question_routes_to_mae_summary_intent() -> None:
    intent = find_best_intent_for_question(
        "최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘."
    )

    assert intent is not None
    assert intent.minor == "objective_mae_summary"


def test_sponsored_candidate_rate_intent_requires_total_posts() -> None:
    intent = find_best_intent_for_question(
        "Which influencers have the top 10 sponsored candidate rates?"
    )

    assert intent is not None
    assert intent.minor == "sponsored_candidate_rate_top10_with_total_posts"
    assert "total_posts" in intent.required_columns

    try:
        validate_intent_contract(
            """
            select creator_username, sponsored_candidate_rate
            from ai_native.ai_creator_sponsored_summary
            order by sponsored_candidate_rate desc, total_posts desc
            limit 10
            """,
            intent,
        )
    except Exception as exc:
        assert "missing required SELECT column(s): total_posts" in str(exc)
    else:
        raise AssertionError("intent contract should require total_posts in SELECT")


def test_korean_ad_rate_intent_keeps_original_output_contract() -> None:
    intent = find_best_intent_for_question("광고 의심 비율이 높은 작성자 Top 10은 누구야?")

    assert intent is not None
    assert intent.minor == "ad_suspicion_top10"
    assert intent.required_columns == ("creator_username", "sponsored_candidate_rate")


def test_intent_contract_accepts_alias_qualified_mae_and_bias() -> None:
    intent = find_best_intent_for_question(
        "최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘."
    )

    assert intent is not None
    validate_intent_contract(
        """
        select
            roi.roas_performance_tier,
            count(*) as campaign_count,
            avg(monitor.absolute_roas_prediction_error) as mae,
            avg(monitor.roas_prediction_error) as bias
        from marts.mart_campaign_roas_prediction_monitor as monitor
        join ai_native.ai_campaign_roi_summary as roi
          on monitor.campaign_id = roi.campaign_id
        where monitor.scoring_snapshot_date = (
            select max(scoring_snapshot_date)
            from marts.mart_campaign_roas_prediction_monitor
        )
        group by roi.roas_performance_tier
        order by mae desc, roi.roas_performance_tier asc
        """,
        intent,
    )


def test_schema_context_includes_positive_criteria_rulebook() -> None:
    schema_context = build_schema_context_v1()

    assert "Actual Allowed Table and Column Catalog" in schema_context
    assert "Natural-Language Intent Routing Catalog" in schema_context
    assert "major category -> middle category -> minor intent" in schema_context
    assert "Canonical SQL Templates" in schema_context
    assert "Question-ID Canonical SQL Contracts" in schema_context
    assert "p5_q009" in schema_context
    assert "No default LIMIT for benchmark broad-list question" in schema_context
    assert "include every listed output column explicitly in SELECT" in schema_context
    assert "absolute_roas_prediction_error, not signed roas_prediction_error" in schema_context
    assert "campaign_count_avg_roas_by_objective_and_tier" in schema_context
    assert "review_campaign_count_avg_roas_by_region" in schema_context
    assert "objective_mae_summary" in schema_context
    assert "order by avg_roas desc, campaign_objective asc, roas_performance_tier asc" in schema_context
    assert "count(*) as review_campaign_count" in schema_context
    assert "Text2SQL Positive Criteria Rulebook" in schema_context
    assert "text2sql_positive_criteria_rulebook.md" in schema_context
    assert "Text2SQL LLM Decision Guide" in schema_context
    assert "text2sql_llm_decision_guide.md" in schema_context
    assert "Sponsored candidate post" in schema_context
    assert "views is not available" in schema_context
    assert "scoring_snapshot_date = (select max(scoring_snapshot_date)" in schema_context


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
            "usage_attempts": [
                {
                    "provider": "gemini",
                    "model": "unit-test-gemini",
                    "input_tokens": 900,
                    "cached_input_tokens": 700,
                    "output_tokens": 100,
                    "total_tokens": 1000,
                    "estimated_cost_usd": 0.0002175,
                    "elapsed_ms": 4000.0,
                },
                {
                    "provider": "openai",
                    "model": "unit-test-openai",
                    "input_tokens": 1000,
                    "cached_input_tokens": 400,
                    "output_tokens": 200,
                    "total_tokens": 1200,
                    "estimated_cost_usd": 0.00138,
                    "elapsed_ms": 2500.0,
                },
            ],
            "fallback_reason": "primary_sql_validation_failed:unit test",
        }
    )

    assert response.answerability == "answerable"
    assert response.expected_tables == ("ai_native.ai_campaign_roi_summary",)
    assert [usage.provider for usage in response.usage_attempts] == ["gemini", "openai"]
    assert response.fallback_reason == "primary_sql_validation_failed:unit test"
