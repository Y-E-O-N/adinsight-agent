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
        exact_sql = MOCK_SQL_BY_QUESTION.get(normalized_question)

        if exact_sql is not None:
            return exact_sql

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
            reason="Mock provider only supports campaign ROI and prediction monitor questions.",
        )


MOCK_SQL_BY_QUESTION = {
    normalize_question("Show average ROAS and net payment amount by campaign objective."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select campaign_objective, count(*) as campaign_count, "
                "avg(roas) as avg_roas, "
                "avg(net_payment_amount_krw) as avg_net_payment_amount_krw "
                "from ai_native.ai_campaign_roi_summary "
                "group by campaign_objective "
                "order by avg_roas desc"
            ),
            expected_tables=("ai_native.ai_campaign_roi_summary",),
            reason="Question asks for objective-level campaign ROI aggregation.",
        ),
    normalize_question("전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select campaign_id, campaign_name, campaign_objective, roas, "
                "total_payment_events "
                "from ai_native.ai_campaign_roi_summary "
                "where campaign_objective = 'conversion' "
                "order by roas desc, total_payment_events desc "
                "limit 10"
            ),
            expected_tables=("ai_native.ai_campaign_roi_summary",),
            reason="Question asks for high-ROAS conversion campaigns.",
        ),
    normalize_question("순결제액이 있는 ROI 검토 대상 캠페인을 보여줘."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select campaign_id, campaign_name, roas, has_positive_net_payment, "
                "included_in_campaign_roi_review "
                "from ai_native.ai_campaign_roi_summary "
                "where has_positive_net_payment = true "
                "and included_in_campaign_roi_review = true "
                "order by roas desc, campaign_id asc "
                "limit 50"
            ),
            expected_tables=("ai_native.ai_campaign_roi_summary",),
            reason="Question asks for positive-payment campaigns included in ROI review.",
        ),
    normalize_question(
        "Which creators should we review first for sponsored content?"
    ): SqlGenerationResponse(
        answerability="answerable",
        sql=(
            "select creator_username, sponsored_candidate_posts, "
            "sponsored_candidate_rate, included_in_creator_review "
            "from ai_native.ai_creator_sponsored_summary "
            "where included_in_creator_review = true "
            "order by sponsored_candidate_posts desc, sponsored_candidate_rate desc "
            "limit 20"
        ),
        expected_tables=("ai_native.ai_creator_sponsored_summary",),
        reason="Question asks for priority creator-review candidates.",
    ),
    normalize_question("Which influencers have a high sponsored candidate rate?"):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select creator_username, sponsored_candidate_rate, total_posts "
                "from ai_native.ai_creator_sponsored_summary "
                "order by sponsored_candidate_rate desc, total_posts desc "
                "limit 10"
            ),
            expected_tables=("ai_native.ai_creator_sponsored_summary",),
            reason="Question asks for creators ranked by sponsored-candidate rate.",
        ),
    normalize_question("광고 의심 비율이 높은 작성자는 누구야?"): SqlGenerationResponse(
        answerability="answerable",
        sql=(
            "select creator_username, sponsored_candidate_rate "
            "from ai_native.ai_creator_sponsored_summary "
            "order by sponsored_candidate_rate desc "
            "limit 10"
        ),
        expected_tables=("ai_native.ai_creator_sponsored_summary",),
        reason="Question asks for creators ranked by suspected ad rate.",
    ),
    normalize_question("List creators where likes are often hidden."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select creator_username, hidden_likes_rate, hidden_likes_posts "
                "from ai_native.ai_creator_sponsored_summary "
                "order by hidden_likes_rate desc, hidden_likes_posts desc "
                "limit 10"
            ),
            expected_tables=("ai_native.ai_creator_sponsored_summary",),
            reason="Question asks for creators ranked by hidden-likes rate.",
        ),
    normalize_question("평균 댓글 수가 높은 인플루언서 Top 10을 보여줘."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select creator_username, avg_comments_count "
                "from ai_native.ai_creator_sponsored_summary "
                "order by avg_comments_count desc "
                "limit 10"
            ),
            expected_tables=("ai_native.ai_creator_sponsored_summary",),
            reason="Question asks for creators ranked by average comments.",
        ),
    normalize_question(
        "Which campaigns have the largest ROAS prediction errors in the latest snapshot?"
    ): SqlGenerationResponse(
        answerability="answerable",
        sql=(
            "select campaign_id, campaign_name, actual_roas, predicted_roas, "
            "absolute_roas_prediction_error "
            "from marts.mart_campaign_roas_prediction_monitor "
            "where scoring_snapshot_date = ("
            "select max(scoring_snapshot_date) "
            "from marts.mart_campaign_roas_prediction_monitor"
            ") "
            "order by absolute_roas_prediction_error desc, campaign_id asc "
            "limit 5"
        ),
        expected_tables=("marts.mart_campaign_roas_prediction_monitor",),
        reason="Question asks for latest snapshot prediction error ranking.",
    ),
    normalize_question("최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘."):
        SqlGenerationResponse(
            answerability="answerable",
            sql=(
                "select campaign_id, campaign_name, actual_roas, predicted_roas, "
                "roas_prediction_error "
                "from marts.mart_campaign_roas_prediction_monitor "
                "where scoring_snapshot_date = ("
                "select max(scoring_snapshot_date) "
                "from marts.mart_campaign_roas_prediction_monitor"
                ") "
                "and roas_prediction_error > 0 "
                "order by roas_prediction_error desc, campaign_id asc "
                "limit 50"
            ),
            expected_tables=("marts.mart_campaign_roas_prediction_monitor",),
            reason="Question asks for campaigns where actual ROAS exceeded predicted ROAS.",
        ),
    normalize_question(
        "Compare average actual ROAS and predicted ROAS by objective in the latest "
        "prediction snapshot."
    ): SqlGenerationResponse(
        answerability="answerable",
        sql=(
            "select objective, count(*) as campaign_count, "
            "avg(actual_roas) as avg_actual_roas, "
            "avg(predicted_roas) as avg_predicted_roas, "
            "avg(roas_prediction_error) as avg_roas_prediction_error "
            "from marts.mart_campaign_roas_prediction_monitor "
            "where scoring_snapshot_date = ("
            "select max(scoring_snapshot_date) "
            "from marts.mart_campaign_roas_prediction_monitor"
            ") "
            "group by objective "
            "order by avg_roas_prediction_error desc"
        ),
        expected_tables=("marts.mart_campaign_roas_prediction_monitor",),
        reason="Question asks for latest actual vs predicted ROAS by objective.",
    ),
}
