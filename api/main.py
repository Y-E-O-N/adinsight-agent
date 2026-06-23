from __future__ import annotations

import os

import numpy as np
import psycopg
from fastapi import FastAPI, HTTPException

from agent.eval.run_campaign_roas_model import (
    CATEGORICAL_FEATURES,
    FEATURE_TABLE,
    NUMERIC_FEATURES,
    CampaignRoasFeatureRow,
    build_design_matrices,
    coerce_float,
    fit_linear,
)
from api.schemas import (
    CampaignRoasPredictRequest,
    CampaignRoasPredictResponse,
    HealthResponse,
)

SCORING_TABLE = "features.feature_campaign_roas_scoring_set"
MODEL_NAME = "linear_regression_numpy_v1"

app = FastAPI(
    title="AdInsight Serving API",
    version="0.1.0",
    description="Local FastAPI skeleton for campaign ROAS prediction serving.",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="adinsight-api")


@app.post("/predict/campaign-roas", response_model=CampaignRoasPredictResponse)
def predict_campaign_roas(
    request: CampaignRoasPredictRequest,
) -> CampaignRoasPredictResponse:
    training_rows = fetch_training_rows()
    scoring_row, scoring_snapshot_date = fetch_scoring_row(request.campaign_id)

    if not training_rows:
        raise HTTPException(status_code=503, detail=f"No rows found in {FEATURE_TABLE}.")

    train_labels = np.array([row.label_roas for row in training_rows], dtype=float)
    train_matrix, scoring_matrix = build_design_matrices(training_rows, [scoring_row])
    coefficients = fit_linear(train_matrix, train_labels)
    predicted_roas = float((scoring_matrix @ coefficients)[0])

    return CampaignRoasPredictResponse(
        campaign_id=request.campaign_id,
        model_name=MODEL_NAME,
        predicted_roas=round(predicted_roas, 6),
        training_rows_used=len(training_rows),
        scoring_snapshot_date=scoring_snapshot_date,
        feature_source=SCORING_TABLE,
        known_limitation=(
            "Local skeleton prediction from 25 synthetic labeled campaign rows; "
            "not production performance evidence."
        ),
    )


def fetch_training_rows() -> list[CampaignRoasFeatureRow]:
    selected_columns = [
        "campaign_id",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
        "label_roas",
    ]
    sql = f"""
        select
            {", ".join(selected_columns)}
        from {FEATURE_TABLE}
        order by campaign_id
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        records = cur.fetchall()

    return [build_feature_row(record, has_label=True) for record in records]


def fetch_scoring_row(campaign_id: str) -> tuple[CampaignRoasFeatureRow, str]:
    selected_columns = [
        "campaign_id",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
        "scoring_snapshot_date",
    ]
    sql = f"""
        select
            {", ".join(selected_columns)}
        from {SCORING_TABLE}
        where campaign_id = %s
        order by scoring_snapshot_date desc
        limit 1
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql, (campaign_id,))
        record = cur.fetchone()

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"campaign_id={campaign_id} not found in {SCORING_TABLE}.",
        )

    return build_feature_row(record, has_label=False), str(record[-1])


def build_feature_row(record: tuple[object, ...], has_label: bool) -> CampaignRoasFeatureRow:
    numeric_offset = 1 + len(CATEGORICAL_FEATURES)
    numeric_values = record[numeric_offset:numeric_offset + len(NUMERIC_FEATURES)]

    return CampaignRoasFeatureRow(
        campaign_id=str(record[0]),
        region=str(record[1]),
        category=str(record[2]),
        objective=str(record[3]),
        numeric_features={
            feature_name: coerce_float(value)
            for feature_name, value in zip(NUMERIC_FEATURES, numeric_values, strict=True)
        },
        label_roas=coerce_float(record[-1]) if has_label else 0.0,
    )


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adinsight"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

