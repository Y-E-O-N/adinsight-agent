from __future__ import annotations

from fastapi.testclient import TestClient

import api.main as api_main
from agent.eval.run_campaign_roas_model import (
    CATEGORICAL_FEATURES,
    LINEAR_MODEL_NAME,
    NUMERIC_FEATURES,
    CampaignRoasFeatureRow,
)


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
