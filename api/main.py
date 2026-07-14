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
from agent.text2sql.registry import (
    Text2SqlNoMatchError,
    Text2SqlResult,
    Text2SqlUnsafeSqlError,
    execute_question,
)
from agent.text2sql.usage import LlmUsage
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
        with get_connection() as conn:
            fallback_response = try_query_v2_registry_fallback(
                request.question,
                conn,
                mode,
                "provider_refused",
                str(exc),
                started_at,
            )
        if fallback_response is not None:
            return fallback_response

        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        usage = getattr(exc, "usage", None)
        usage_attempts = tuple(getattr(exc, "usage_attempts", ()))
        provider_summary = build_provider_summary(
            usage,
            usage_attempts,
            getattr(exc, "fallback_reason", None),
        )
        record_query_v2_audit(
            {
                "status": "refused",
                "mode": mode,
                "question": request.question,
                "latency_ms": latency_ms,
                "error": str(exc),
                "usage": usage.to_dict() if usage else None,
                "usage_attempts": [
                    usage.to_dict()
                    for usage in usage_attempts
                ],
                "provider_summary": provider_summary,
            }
        )
        raise HTTPException(
            status_code=404,
            detail={
                "message": str(exc),
                "mode": mode,
                "provider_summary": provider_summary,
            },
        ) from exc
    except Text2SqlValidationError as exc:
        with get_connection() as conn:
            fallback_response = try_query_v2_registry_fallback(
                request.question,
                conn,
                mode,
                "provider_blocked",
                str(exc),
                started_at,
            )
        if fallback_response is not None:
            return fallback_response

        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        usage = getattr(exc, "usage", None)
        usage_attempts = tuple(getattr(exc, "usage_attempts", ()))
        provider_summary = build_provider_summary(
            usage,
            usage_attempts,
            getattr(exc, "fallback_reason", None),
        )
        record_query_v2_audit(
            {
                "status": "blocked",
                "mode": mode,
                "question": request.question,
                "latency_ms": latency_ms,
                "error": str(exc),
                "usage": usage.to_dict() if usage else None,
                "usage_attempts": [
                    usage.to_dict()
                    for usage in usage_attempts
                ],
                "provider_summary": provider_summary,
            }
        )
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "mode": mode,
                "provider_summary": provider_summary,
            },
        ) from exc
    except Exception as exc:
        with get_connection() as conn:
            fallback_response = try_query_v2_registry_fallback(
                request.question,
                conn,
                mode,
                "provider_error",
                type(exc).__name__,
                started_at,
            )
        if fallback_response is not None:
            return fallback_response

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
    provider_summary = build_provider_summary(
        result.usage,
        result.usage_attempts,
        result.fallback_reason,
    )
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
            "usage": result.usage.to_dict() if result.usage else None,
            "usage_attempts": [
                usage.to_dict()
                for usage in result.usage_attempts
            ],
            "provider_summary": provider_summary,
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
        usage=result.usage.to_dict() if result.usage else None,
        usage_attempts=[
            usage.to_dict()
            for usage in result.usage_attempts
        ],
        provider_summary=provider_summary,
        known_limitation=(
            "Uses the configured Text2SQL generation provider. SQL is still validated, "
            "bounded, timed out, and audited before execution."
        ),
    )


def try_query_v2_registry_fallback(
    question: str,
    conn: psycopg.Connection,
    provider_mode: str,
    trigger_status: str,
    trigger_error: str,
    started_at: float,
) -> QueryV2Response | None:
    if not query_v2_registry_fallback_enabled():
        return None

    try:
        fallback_result = execute_question(question, conn)
    except Text2SqlNoMatchError:
        return None
    except Text2SqlUnsafeSqlError:
        return None
    except Exception:
        return None

    latency_ms = round((perf_counter() - started_at) * 1000, 3)
    provider_summary = build_fallback_provider_summary()
    record_query_v2_audit(
        {
            "status": "fallback_success",
            "mode": "deterministic_expected_sql_registry_fallback_v1",
            "provider_mode": provider_mode,
            "fallback_trigger_status": trigger_status,
            "fallback_trigger_error": trigger_error,
            "question": question,
            "latency_ms": latency_ms,
            "row_count": fallback_result.row_count,
            "question_id": fallback_result.question_id,
            "provider_summary": provider_summary,
        }
    )

    return build_query_v2_fallback_response(
        question,
        fallback_result,
        latency_ms,
        provider_summary,
    )


def query_v2_registry_fallback_enabled() -> bool:
    return os.getenv("TEXT2SQL_V2_REGISTRY_FALLBACK_ENABLED", "true").lower() not in {
        "0",
        "false",
        "no",
    }


def build_query_v2_fallback_response(
    question: str,
    fallback_result: Text2SqlResult,
    latency_ms: float,
    provider_summary: dict[str, object],
) -> QueryV2Response:
    return QueryV2Response(
        question=question,
        sql=fallback_result.sql,
        rows=fallback_result.rows,
        row_count=fallback_result.row_count,
        answer=fallback_result.answer,
        latency_ms=latency_ms,
        mode="deterministic_expected_sql_registry_fallback_v1",
        expected_tables=[fallback_result.expected_model],
        reason=(
            "Provider result was not usable, so /query/v2 fell back to the "
            f"curated expected-SQL registry question_id={fallback_result.question_id}."
        ),
        validation_tables=[fallback_result.expected_model],
        validation_limit=None,
        usage=None,
        provider_summary=provider_summary,
        known_limitation=(
            "Fallback handles only exact curated questions from "
            "agent/eval/text2sql_questions.yml; model-only evaluation remains separate."
        ),
    )


def build_fallback_provider_summary() -> dict[str, object]:
    return {
        "fallback_used": True,
        "final_provider": "deterministic_registry",
        "final_model": None,
        "attempt_count": 0,
        "estimated_cost_usd": 0.0,
        "provider_elapsed_ms": 0.0,
    }


def build_provider_summary(
    usage: LlmUsage | None,
    usage_attempts: tuple[LlmUsage, ...],
    fallback_reason: str | None = None,
) -> dict[str, object] | None:
    attempts = list(usage_attempts)
    if not attempts and usage is not None:
        attempts = [usage]
    if not attempts:
        return None

    final_usage = attempts[-1] if attempts else usage
    input_tokens = sum_optional_int(usage.input_tokens for usage in attempts)
    cached_input_tokens = sum_optional_int(usage.cached_input_tokens for usage in attempts)
    output_tokens = sum_optional_int(usage.output_tokens for usage in attempts)
    total_tokens = sum_optional_int(usage.total_tokens for usage in attempts)
    estimated_cost_usd = sum_optional_float(
        usage.estimated_cost_usd for usage in attempts
    )
    provider_elapsed_ms = sum_optional_float(usage.elapsed_ms for usage in attempts)
    cached_input_ratio = (
        round(cached_input_tokens / input_tokens, 4)
        if input_tokens and cached_input_tokens is not None
        else None
    )

    provider_names = [
        usage.provider
        for usage in attempts
        if usage.provider
    ]
    fallback_used = len(set(provider_names)) > 1

    return {
        "fallback_used": fallback_used,
        "final_provider": final_usage.provider,
        "final_model": final_usage.model,
        "attempt_count": len(attempts),
        "attempt_providers": provider_names,
        "fallback_reason": fallback_reason if fallback_used else None,
        "estimated_cost_usd": estimated_cost_usd,
        "provider_elapsed_ms": provider_elapsed_ms,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cached_input_ratio": cached_input_ratio,
    }


def sum_optional_int(values: object) -> int | None:
    resolved = [value for value in values if value is not None]
    return sum(resolved) if resolved else None


def sum_optional_float(values: object) -> float | None:
    resolved = [value for value in values if value is not None]
    return round(sum(resolved), 8) if resolved else None


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
