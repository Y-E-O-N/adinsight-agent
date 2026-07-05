from __future__ import annotations

from fastapi.testclient import TestClient

import text2sql_gateway.main as gateway_main


def test_gateway_health_endpoint() -> None:
    client = TestClient(gateway_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "adinsight-text2sql-gateway",
        "mode": "text2sql_gateway_mock_v1",
    }


def test_gateway_generate_sql_returns_json_contract(monkeypatch) -> None:
    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "answerable"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["mode"] == "text2sql_gateway_mock_v1"
    assert "ai_native.ai_campaign_roi_summary" in payload["sql"]


def test_gateway_generate_sql_can_refuse(monkeypatch) -> None:
    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Show TikTok spend by channel.",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "not_answerable"
    assert payload["sql"] is None
    assert payload["expected_tables"] == []


def test_gateway_generate_sql_requires_bearer_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("TEXT2SQL_GATEWAY_API_KEY", "unit-test-token")
    client = TestClient(gateway_main.app)

    unauthorized = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    authorized = client.post(
        "/text2sql/generate",
        headers={"Authorization": "Bearer unit-test-token"},
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
