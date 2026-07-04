from __future__ import annotations

import os
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from time import perf_counter

import psycopg
from fastapi import FastAPI, HTTPException

from agent.eval.run_campaign_roas_model import (
    ARTIFACT_PATH,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    CampaignRoasFeatureRow,
    coerce_float,
    load_linear_model_artifact,
    predict_with_linear_artifact,
)
from agent.text2sql.audit import write_text2sql_audit
from agent.text2sql.generator import Text2SqlNotAnswerableError, execute_generated_question
from agent.text2sql.provider import get_sql_generation_provider
from agent.text2sql.registry import Text2SqlNoMatchError, Text2SqlUnsafeSqlError, execute_question
from agent.text2sql.validator import Text2SqlValidationError
from api.schemas import (
    CampaignRoasPredictRequest,
    CampaignRoasPredictResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    QueryV2Response,
)

SCORING_TABLE = "features.feature_campaign_roas_scoring_set"
MODEL_NAME = "linear_regression_numpy_v1"
MODEL_ARTIFACT_PATH = Path(os.getenv("MODEL_ARTIFACT_PATH", str(ARTIFACT_PATH)))

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
    started_at = perf_counter()
    artifact = get_model_artifact()
    scoring_row, scoring_snapshot_date = fetch_scoring_row(request.campaign_id)

    predicted_roas = predict_with_linear_artifact(scoring_row, artifact)
    latency_ms = (perf_counter() - started_at) * 1000

    return CampaignRoasPredictResponse(
        campaign_id=request.campaign_id,
        model_name=str(artifact["model_name"]),
        predicted_roas=round(predicted_roas, 6),
        latency_ms=round(latency_ms, 3),
        training_rows_used=int(artifact["training_rows_used"]),
        scoring_snapshot_date=scoring_snapshot_date,
        feature_source=SCORING_TABLE,
        model_artifact_path=str(MODEL_ARTIFACT_PATH),
        known_limitation=str(artifact["known_limitation"]),
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    started_at = perf_counter()

    try:
        with get_connection() as conn:
            result = execute_question(request.question, conn)
    except Text2SqlNoMatchError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "message": str(exc),
                "supported_question_examples": exc.supported_question_examples,
            },
        ) from exc
    except Text2SqlUnsafeSqlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    latency_ms = (perf_counter() - started_at) * 1000

    return QueryResponse(
        question=request.question,
        question_id=result.question_id,
        matched_question=result.matched_question,
        expected_model=result.expected_model,
        sql=result.sql,
        rows=result.rows,
        row_count=result.row_count,
        answer=result.answer,
        latency_ms=round(latency_ms, 3),
        mode="deterministic_expected_sql_registry_v1",
        known_limitation=(
            "Matches only curated questions in agent/eval/text2sql_questions.yml; "
            "LLM SQL generation is a later hardening step."
        ),
    )


@app.post("/query/v2", response_model=QueryV2Response)
def query_v2(request: QueryRequest) -> QueryV2Response:
    started_at = perf_counter()
    mode = "llm_generated_sql_v2_mock"

    try:
        provider = get_sql_generation_provider()
        mode = provider.mode
        with get_connection() as conn:
            result = execute_generated_question(
                request.question,
                conn,
                client=provider.client,
                mode=provider.mode,
            )
    except Text2SqlNotAnswerableError as exc:
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        record_query_v2_audit(
            {
                "status": "refused",
                "mode": mode,
                "question": request.question,
                "latency_ms": latency_ms,
                "error": str(exc),
            }
        )
        raise HTTPException(
            status_code=404,
            detail={
                "message": str(exc),
                "mode": mode,
            },
        ) from exc
    except Text2SqlValidationError as exc:
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        record_query_v2_audit(
            {
                "status": "blocked",
                "mode": mode,
                "question": request.question,
                "latency_ms": latency_ms,
                "error": str(exc),
            }
        )
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "mode": mode,
            },
        ) from exc
    except Exception as exc:
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        record_query_v2_audit(
            {
                "status": "error",
                "mode": mode,
                "question": request.question,
                "latency_ms": latency_ms,
                "error": type(exc).__name__,
            }
        )
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Text2SQL v2 execution failed.",
                "mode": mode,
            },
        ) from exc

    latency_ms = (perf_counter() - started_at) * 1000
    rounded_latency_ms = round(latency_ms, 3)
    record_query_v2_audit(
        {
            "status": "success",
            "mode": result.mode,
            "question": request.question,
            "latency_ms": rounded_latency_ms,
            "row_count": result.row_count,
            "expected_tables": list(result.expected_tables),
            "validation_tables": list(result.validation.referenced_tables),
            "validation_limit": result.validation.limit,
        }
    )

    return QueryV2Response(
        question=request.question,
        sql=result.sql,
        rows=result.rows,
        row_count=result.row_count,
        answer=result.answer,
        latency_ms=rounded_latency_ms,
        mode=result.mode,
        expected_tables=list(result.expected_tables),
        reason=result.reason,
        validation_tables=list(result.validation.referenced_tables),
        validation_limit=result.validation.limit,
        known_limitation=(
            "Uses a provider-free mock SQL generator. This validates the v2 API boundary "
            "and SQL guardrails before connecting a real LLM provider."
        ),
    )


def record_query_v2_audit(record: dict[str, object]) -> None:
    with suppress(OSError):
        write_text2sql_audit(record)


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


@lru_cache(maxsize=1)
def get_model_artifact() -> dict[str, object]:
    if not MODEL_ARTIFACT_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Model artifact not found at {MODEL_ARTIFACT_PATH}.",
        )

    artifact = load_linear_model_artifact(MODEL_ARTIFACT_PATH)

    if artifact.get("model_name") != MODEL_NAME:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unexpected model artifact {artifact.get('model_name')}; "
                f"expected {MODEL_NAME}."
            ),
        )

    return artifact
