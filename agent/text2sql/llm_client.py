from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agent.text2sql.registry import normalize_question


@dataclass(frozen=True)
class SqlGenerationRequest:
    question: str
    schema_context: str


@dataclass(frozen=True)
class SqlGenerationResponse:
    answerability: str
    sql: str | None
    expected_tables: tuple[str, ...]
    reason: str


class SqlGenerationClient(Protocol):
    def generate_sql(self, request: SqlGenerationRequest) -> SqlGenerationResponse:
        ...


class MockSqlGenerationClient:
    """Provider-free v2 harness for validator and executor tests."""

    def generate_sql(self, request: SqlGenerationRequest) -> SqlGenerationResponse:
        normalized_question = normalize_question(request.question)

        if "highest roas" in normalized_question:
            return SqlGenerationResponse(
                answerability="answerable",
                sql=(
                    "select campaign_id, campaign_name, roas "
                    "from ai_native.ai_campaign_roi_summary "
                    "order by roas desc "
                    "limit 5"
                ),
                expected_tables=("ai_native.ai_campaign_roi_summary",),
                reason="Question asks for campaigns ranked by ROAS.",
            )

        if "mae" in normalized_question and "bias" in normalized_question:
            return SqlGenerationResponse(
                answerability="answerable",
                sql=(
                    "select model_name, count(*) as prediction_rows, "
                    "avg(absolute_roas_prediction_error) as mae, "
                    "avg(roas_prediction_error) as bias "
                    "from marts.mart_campaign_roas_prediction_monitor "
                    "where scoring_snapshot_date = ("
                    "select max(scoring_snapshot_date) "
                    "from marts.mart_campaign_roas_prediction_monitor"
                    ") "
                    "group by model_name "
                    "order by model_name asc"
                ),
                expected_tables=("marts.mart_campaign_roas_prediction_monitor",),
                reason="Question asks for latest model error metrics.",
            )

        return SqlGenerationResponse(
            answerability="not_answerable",
            sql=None,
            expected_tables=(),
            reason="Mock provider only supports the initial v2 smoke questions.",
        )
