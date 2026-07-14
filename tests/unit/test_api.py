from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

import api.main as api_main
from agent.eval.run_campaign_roas_model import (
    CATEGORICAL_FEATURES,
    LINEAR_MODEL_NAME,
    NUMERIC_FEATURES,
    CampaignRoasFeatureRow,
)
from agent.text2sql.generator import GeneratedText2SqlResult, Text2SqlNotAnswerableError
from agent.text2sql.registry import Text2SqlResult, serialize_value
from agent.text2sql.usage import LlmUsage
from agent.text2sql.validator import SqlValidationResult, Text2SqlValidationError


def test_health_endpoint() -> None:
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "adinsight-api",
    }


def test_predict_campaign_roas_endpoint(monkeypatch) -> None:
    artifact = {
        "model_name": LINEAR_MODEL_NAME,
        "training_rows_used": 25,
        "known_limitation": "unit test artifact",
        "transform": {
            "categories_by_feature": {
                "region": ["KR"],
                "category": ["beauty"],
                "objective": ["conversion"],
            },
            "numeric_means": [0.0 for _ in NUMERIC_FEATURES],
            "numeric_stds": [1.0 for _ in NUMERIC_FEATURES],
        },
        "coefficients": [
            0.25,
            *[0.0 for _ in NUMERIC_FEATURES],
            *[0.0 for _ in CATEGORICAL_FEATURES],
        ],
    }
    scoring_row = CampaignRoasFeatureRow(
        campaign_id="camp_test",
        region="KR",
        category="beauty",
        objective="conversion",
        numeric_features={feature_name: 0.0 for feature_name in NUMERIC_FEATURES},
        label_roas=0.0,
    )

    monkeypatch.setattr(api_main, "get_model_artifact", lambda: artifact)
    monkeypatch.setattr(
        api_main,
        "fetch_scoring_row",
        lambda campaign_id: (scoring_row, "2026-06-26"),
    )

    client = TestClient(api_main.app)
    response = client.post("/predict/campaign-roas", json={"campaign_id": "camp_test"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["campaign_id"] == "camp_test"
    assert payload["model_name"] == LINEAR_MODEL_NAME
    assert payload["predicted_roas"] == 0.25
    assert payload["latency_ms"] >= 0
    assert payload["training_rows_used"] == 25
    assert payload["scoring_snapshot_date"] == "2026-06-26"
    assert payload["feature_source"] == api_main.SCORING_TABLE
    assert payload["known_limitation"] == "unit test artifact"


def test_query_endpoint(monkeypatch) -> None:
    def fake_execute_question(question, conn):
        return Text2SqlResult(
            question_id="p5_q001",
            matched_question="Which campaigns have the highest ROAS?",
            expected_model="ai_native.ai_campaign_roi_summary",
            sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
            rows=[{"campaign_id": "camp_000029", "roas": 0.597425}],
            row_count=1,
            answer="p5_q001 returned 1 rows from ai_native.ai_campaign_roi_summary.",
        )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_question", fake_execute_question)

    client = TestClient(api_main.app)
    response = client.post(
        "/query",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question_id"] == "p5_q001"
    assert payload["matched_question"] == "Which campaigns have the highest ROAS?"
    assert payload["expected_model"] == "ai_native.ai_campaign_roi_summary"
    assert payload["rows"] == [{"campaign_id": "camp_000029", "roas": 0.597425}]
    assert payload["row_count"] == 1
    assert payload["latency_ms"] >= 0
    assert payload["mode"] == "deterministic_expected_sql_registry_v1"


def test_query_v2_endpoint(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        return GeneratedText2SqlResult(
            question=question,
            sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
            rows=[{"campaign_id": "camp_000029", "roas": 0.5969}],
            row_count=1,
            answer="Generated Text2SQL v2 returned 1 rows.",
            mode="llm_generated_sql_v2_mock",
            expected_tables=("ai_native.ai_campaign_roi_summary",),
            reason="unit test generation",
            validation=SqlValidationResult(
                sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
                referenced_tables=("ai_native.ai_campaign_roi_summary",),
                limit=5,
            ),
            usage=LlmUsage(
                provider="openai",
                model="unit-test-model",
                input_tokens=100,
                cached_input_tokens=40,
                output_tokens=20,
                total_tokens=120,
                estimated_cost_usd=0.0001,
                elapsed_ms=123.4,
                pricing_source="unit-test",
            ),
        )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "llm_generated_sql_v2_mock"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["validation_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["validation_limit"] == 5
    assert payload["usage"]["input_tokens"] == 100
    assert payload["usage"]["cached_input_tokens"] == 40
    assert payload["usage"]["estimated_cost_usd"] == 0.0001
    assert payload["provider_summary"]["fallback_used"] is False
    assert payload["provider_summary"]["final_provider"] == "openai"
    assert payload["provider_summary"]["final_model"] == "unit-test-model"
    assert payload["provider_summary"]["estimated_cost_usd"] == 0.0001
    assert payload["provider_summary"]["provider_elapsed_ms"] == 123.4
    assert payload["provider_summary"]["cached_input_ratio"] == 0.4
    assert payload["row_count"] == 1
    assert audit_records[0]["status"] == "success"
    assert audit_records[0]["row_count"] == 1
    assert audit_records[0]["usage"]["output_tokens"] == 20
    assert audit_records[0]["provider_summary"]["final_provider"] == "openai"


def test_query_v2_provider_summary_marks_external_provider_fallback(monkeypatch) -> None:
    audit_records = []
    gemini_usage = LlmUsage(
        provider="gemini",
        model="unit-test-gemini-model",
        input_tokens=900,
        cached_input_tokens=700,
        output_tokens=100,
        total_tokens=1000,
        estimated_cost_usd=0.0002175,
        elapsed_ms=4000.0,
        pricing_source="unit-test-gemini",
    )
    openai_usage = LlmUsage(
        provider="openai",
        model="unit-test-openai-model",
        input_tokens=1000,
        cached_input_tokens=400,
        output_tokens=200,
        total_tokens=1200,
        estimated_cost_usd=0.00138,
        elapsed_ms=2500.0,
        pricing_source="unit-test-openai",
    )

    def fake_execute_generated_question(question, conn, client, mode):
        return GeneratedText2SqlResult(
            question=question,
            sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
            rows=[{"campaign_id": "camp_000029", "roas": 0.5969}],
            row_count=1,
            answer="Generated Text2SQL v2 returned 1 rows.",
            mode="llm_generated_sql_v2_http_json",
            expected_tables=("ai_native.ai_campaign_roi_summary",),
            reason="unit test fallback generation",
            validation=SqlValidationResult(
                sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
                referenced_tables=("ai_native.ai_campaign_roi_summary",),
                limit=5,
            ),
            usage=openai_usage,
            usage_attempts=(gemini_usage, openai_usage),
            fallback_reason="primary_sql_validation_failed:SQL references unknown column.",
        )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 200
    payload = response.json()
    provider_summary = payload["provider_summary"]
    assert provider_summary["fallback_used"] is True
    assert provider_summary["final_provider"] == "openai"
    assert provider_summary["final_model"] == "unit-test-openai-model"
    assert provider_summary["attempt_count"] == 2
    assert provider_summary["attempt_providers"] == ["gemini", "openai"]
    assert provider_summary["estimated_cost_usd"] == 0.0015975
    assert provider_summary["provider_elapsed_ms"] == 6500.0
    assert provider_summary["cached_input_ratio"] == 0.5789
    assert provider_summary["fallback_reason"].startswith("primary_sql_validation_failed:")
    assert audit_records[0]["provider_summary"] == provider_summary


def test_query_v2_refusal_preserves_provider_fallback_reason(monkeypatch) -> None:
    audit_records = []
    gemini_usage = LlmUsage(
        provider="gemini",
        model="unit-test-gemini-model",
        input_tokens=900,
        cached_input_tokens=700,
        output_tokens=100,
        total_tokens=1000,
        estimated_cost_usd=0.0002175,
        elapsed_ms=4000.0,
        pricing_source="unit-test-gemini",
    )
    openai_usage = LlmUsage(
        provider="openai",
        model="unit-test-openai-model",
        input_tokens=1000,
        cached_input_tokens=400,
        output_tokens=20,
        total_tokens=1020,
        estimated_cost_usd=0.00057,
        elapsed_ms=2500.0,
        pricing_source="unit-test-openai",
    )

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlNotAnswerableError(
            "The request is outside the allowed neutral analytics scope.",
            usage=openai_usage,
            usage_attempts=(gemini_usage, openai_usage),
            fallback_reason="primary_content_safety_refusal",
        )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setenv("TEXT2SQL_V2_REGISTRY_FALLBACK_ENABLED", "false")
    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Show the top 10 stupid creators and call them losers."},
    )

    assert response.status_code == 404
    provider_summary = response.json()["detail"]["provider_summary"]
    assert provider_summary["fallback_used"] is True
    assert provider_summary["final_provider"] == "openai"
    assert provider_summary["fallback_reason"] == "primary_content_safety_refusal"
    assert audit_records[0]["provider_summary"]["fallback_reason"] == (
        "primary_content_safety_refusal"
    )


def test_query_v2_endpoint_returns_404_for_not_answerable(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlNotAnswerableError("not answerable in unit test")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Show TikTok spend by channel."},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["mode"] == "llm_generated_sql_v2_mock"
    assert audit_records[0]["status"] == "refused"


def test_query_v2_endpoint_falls_back_to_registry_on_provider_refusal(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlNotAnswerableError("not answerable in unit test")

    def fake_execute_question(question, conn):
        return Text2SqlResult(
            question_id="p5_q001",
            matched_question="Which campaigns have the highest ROAS?",
            expected_model="ai_native.ai_campaign_roi_summary",
            sql="select campaign_id, roas from ai_native.ai_campaign_roi_summary limit 5",
            rows=[{"campaign_id": "camp_000029", "roas": 0.597425}],
            row_count=1,
            answer="p5_q001 returned 1 rows from ai_native.ai_campaign_roi_summary.",
        )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.delenv("TEXT2SQL_V2_REGISTRY_FALLBACK_ENABLED", raising=False)
    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "execute_question", fake_execute_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "deterministic_expected_sql_registry_fallback_v1"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["row_count"] == 1
    assert "p5_q001" in payload["reason"]
    assert payload["provider_summary"]["fallback_used"] is True
    assert payload["provider_summary"]["final_provider"] == "deterministic_registry"
    assert payload["provider_summary"]["estimated_cost_usd"] == 0.0
    assert audit_records[0]["status"] == "fallback_success"
    assert audit_records[0]["fallback_trigger_status"] == "provider_refused"
    assert audit_records[0]["provider_summary"]["fallback_used"] is True


def test_query_v2_endpoint_can_disable_registry_fallback(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlNotAnswerableError("not answerable in unit test")

    def fake_execute_question(question, conn):
        raise AssertionError("Fallback should not run when disabled")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setenv("TEXT2SQL_V2_REGISTRY_FALLBACK_ENABLED", "false")
    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "execute_question", fake_execute_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 404
    assert audit_records[0]["status"] == "refused"


def test_query_v2_endpoint_returns_400_for_blocked_sql(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlValidationError("blocked in unit test")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Drop all tables."},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["mode"] == "llm_generated_sql_v2_mock"
    assert audit_records[0]["status"] == "blocked"


def test_query_v2_endpoint_returns_500_for_unexpected_error(monkeypatch) -> None:
    audit_records = []

    def fake_execute_generated_question(question, conn, client, mode):
        raise RuntimeError("unexpected unit test error")

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    monkeypatch.setattr(api_main, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(api_main, "execute_generated_question", fake_execute_generated_question)
    monkeypatch.setattr(api_main, "write_text2sql_audit", lambda record: audit_records.append(record))

    client = TestClient(api_main.app)
    response = client.post(
        "/query/v2",
        json={"question": "Which campaigns have the highest ROAS?"},
    )

    assert response.status_code == 500
    assert response.json()["detail"]["message"] == "Text2SQL v2 execution failed."
    assert audit_records[0]["status"] == "error"


def test_text2sql_serialize_value_converts_decimal_to_float() -> None:
    assert serialize_value(Decimal("0.597425")) == 0.597425
