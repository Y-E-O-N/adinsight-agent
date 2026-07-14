from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class CampaignRoasPredictRequest(BaseModel):
    campaign_id: str = Field(..., min_length=1, description="Synthetic campaign id to score.")


class CampaignRoasPredictResponse(BaseModel):
    campaign_id: str
    model_name: str
    predicted_roas: float
    latency_ms: float
    training_rows_used: int
    scoring_snapshot_date: str
    feature_source: str
    model_artifact_path: str
    known_limitation: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural-language analytics question.")


class QueryResponse(BaseModel):
    question: str
    question_id: str
    matched_question: str
    expected_model: str
    sql: str
    rows: list[dict[str, object]]
    row_count: int
    answer: str
    latency_ms: float
    mode: str
    known_limitation: str


class QueryV2Response(BaseModel):
    question: str
    sql: str
    rows: list[dict[str, object]]
    row_count: int
    answer: str
    latency_ms: float
    mode: str
    expected_tables: list[str]
    reason: str
    validation_tables: list[str]
    validation_limit: int | None
    usage: dict[str, object] | None = None
    usage_attempts: list[dict[str, object]] = Field(default_factory=list)
    provider_summary: dict[str, object] | None = None
    known_limitation: str
