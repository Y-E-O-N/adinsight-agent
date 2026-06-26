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
