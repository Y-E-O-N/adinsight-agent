from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Text2SqlTable:
    name: str
    grain: str
    purpose: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class Text2SqlIntent:
    major: str
    middle: str
    minor: str
    table: str
    routing_signals: tuple[str, ...]
    required_columns: tuple[str, ...]
    limit_policy: str
    required_select_columns: tuple[str, ...] = ()
    required_aliases: tuple[str, ...] = ()
    required_order_by: tuple[str, ...] = ()
    metric_semantics: tuple[str, ...] = ()
    forbidden_order_by_columns: tuple[str, ...] = ()
    canonical_sql: str = ""


ALLOWED_TEXT2SQL_TABLES: tuple[Text2SqlTable, ...] = (
    Text2SqlTable(
        name="ai_native.ai_creator_sponsored_summary",
        grain="creator",
        purpose="Creator-level sponsored-content review signals.",
        columns=(
            "creator_username",
            "creator_display_name",
            "total_posts",
            "sponsored_candidate_posts",
            "hidden_likes_posts",
            "carousel_posts",
            "video_posts",
            "avg_likes_count_clean",
            "avg_comments_count",
            "sponsored_candidate_rate",
            "hidden_likes_rate",
            "has_engagement_signal",
            "included_in_creator_review",
        ),
    ),
    Text2SqlTable(
        name="ai_native.ai_campaign_roi_summary",
        grain="campaign",
        purpose="Campaign-level synthetic payment, ROI, and review signals.",
        columns=(
            "campaign_id",
            "campaign_name",
            "campaign_region",
            "product_category",
            "campaign_objective",
            "campaign_budget_krw",
            "campaign_start_date",
            "campaign_end_date",
            "campaign_duration_days",
            "total_attributed_posts",
            "unique_attributed_posts",
            "unique_creators",
            "paid_partnership_posts",
            "avg_observed_engagement_count",
            "high_engagement_posts",
            "viral_engagement_posts",
            "total_payment_events",
            "attributed_posts_with_payment",
            "paying_creators",
            "refunded_events",
            "gross_payment_amount_krw",
            "net_payment_amount_krw",
            "avg_payment_amount_krw",
            "first_payment_ts_utc",
            "last_payment_ts_utc",
            "roas",
            "cost_per_payment_event_krw",
            "payment_events_per_attributed_post",
            "has_positive_net_payment",
            "is_roas_over_1x",
            "is_roas_over_2x",
            "included_in_campaign_roi_review",
            "roas_performance_tier",
        ),
    ),
    Text2SqlTable(
        name="marts.mart_campaign_roas_prediction_monitor",
        grain="campaign prediction snapshot",
        purpose="Campaign ROAS prediction monitoring at scoring snapshot grain.",
        columns=(
            "scoring_snapshot_date",
            "model_name",
            "campaign_id",
            "campaign_name",
            "region",
            "category",
            "objective",
            "campaign_budget_krw",
            "predicted_roas",
            "actual_roas",
            "roas_prediction_error",
            "absolute_roas_prediction_error",
            "net_payment_amount_krw",
            "payment_events",
            "actual_roas_performance_tier",
            "prediction_reason",
            "training_rows_used",
            "prediction_generated_at_utc",
        ),
    ),
)

ALLOWED_TEXT2SQL_TABLE_NAMES = frozenset(table.name for table in ALLOWED_TEXT2SQL_TABLES)
ALLOWED_COLUMNS_BY_TABLE = {
    table.name: frozenset(table.columns)
    for table in ALLOWED_TEXT2SQL_TABLES
}

TEXT2SQL_INTENT_CATALOG: tuple[Text2SqlIntent, ...] = (
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="sponsored_candidate_priority",
        minor="review_first_top20",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=(
            "review first",
            "priority creator",
            "우선 검토",
            "검토 대상",
            "sponsored content",
        ),
        required_columns=(
            "creator_username",
            "sponsored_candidate_posts",
            "sponsored_candidate_rate",
            "included_in_creator_review",
        ),
        limit_policy="Top 20; order by sponsored_candidate_posts desc, sponsored_candidate_rate desc.",
        required_order_by=("sponsored_candidate_posts desc", "sponsored_candidate_rate desc"),
    ),
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="sponsored_candidate_rate",
        minor="sponsored_candidate_rate_top10_with_total_posts",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=(
            "top 10 sponsored candidate rates",
            "top sponsored candidate rates",
            "highest sponsored candidate rates",
        ),
        required_columns=("creator_username", "sponsored_candidate_rate", "total_posts"),
        limit_policy=(
            "Top 10 by sponsored_candidate_rate desc; select total_posts explicitly "
            "and tie-break by total_posts desc."
        ),
        required_order_by=("sponsored_candidate_rate desc", "total_posts desc"),
    ),
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="sponsored_candidate_rate",
        minor="ad_suspicion_top10",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=("sponsored candidate rate", "광고 의심 비율", "협찬 후보 비율"),
        required_columns=("creator_username", "sponsored_candidate_rate"),
        limit_policy="Top 10 when the question asks for high/ranked suspected ad rate; tie-break by total_posts desc.",
        required_order_by=("sponsored_candidate_rate desc", "total_posts desc"),
    ),
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="no_sponsored_candidate",
        minor="broad_creator_list",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=("no sponsored candidate", "협찬 후보가 없는", "게시물이 2개 이상"),
        required_columns=("creator_username", "total_posts", "sponsored_candidate_posts"),
        limit_policy="No default LIMIT for benchmark broad-list question; preserve full ordered list.",
        required_order_by=("total_posts desc", "creator_username asc"),
    ),
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="hidden_likes",
        minor="hidden_likes_top10",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=("likes are often hidden", "hidden likes", "likes hidden"),
        required_columns=("creator_username", "hidden_likes_rate", "hidden_likes_posts"),
        limit_policy="Top 10 by hidden_likes_rate desc, hidden_likes_posts desc.",
        required_order_by=("hidden_likes_rate desc", "hidden_likes_posts desc"),
    ),
    Text2SqlIntent(
        major="creator_sponsored_review",
        middle="engagement_signal",
        minor="engagement_signal_first20",
        table="ai_native.ai_creator_sponsored_summary",
        routing_signals=("engagement signals available", "has engagement signal"),
        required_columns=("creator_username", "has_engagement_signal"),
        limit_policy="First 20 by creator_username asc where has_engagement_signal = true.",
        required_order_by=("creator_username asc",),
    ),
    Text2SqlIntent(
        major="campaign_roi",
        middle="campaign_ranking",
        minor="conversion_high_roas_top10",
        table="ai_native.ai_campaign_roi_summary",
        routing_signals=("conversion campaign", "전환 목적 캠페인", "high ROAS conversion"),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "campaign_objective",
            "roas",
            "total_payment_events",
        ),
        limit_policy="Filter campaign_objective = 'conversion'; order by roas desc, total_payment_events desc; limit 10.",
        required_order_by=("roas desc", "total_payment_events desc"),
    ),
    Text2SqlIntent(
        major="campaign_roi",
        middle="objective_aggregate",
        minor="avg_roas_net_payment_by_objective",
        table="ai_native.ai_campaign_roi_summary",
        routing_signals=(
            "average ROAS and net payment amount by campaign objective",
            "net payment amount by campaign objective",
            "objective별 순결제",
            "목적별 순결제",
        ),
        required_columns=(
            "campaign_objective",
            "campaign_count",
            "avg_roas",
            "avg_net_payment_amount_krw",
        ),
        limit_policy="Aggregate; no LIMIT unless user asks for Top N.",
        required_aliases=("campaign_count", "avg_roas", "avg_net_payment_amount_krw"),
        required_order_by=("avg_roas desc",),
    ),
    Text2SqlIntent(
        major="campaign_roi",
        middle="objective_tier_aggregate",
        minor="campaign_count_avg_roas_by_objective_and_tier",
        table="ai_native.ai_campaign_roi_summary",
        routing_signals=(
            "campaign count and average ROAS by objective and ROAS performance tier",
            "objective and ROAS performance tier",
            "objective별 ROAS tier",
        ),
        required_columns=(
            "campaign_objective",
            "roas_performance_tier",
            "campaign_count",
            "avg_roas",
        ),
        limit_policy="Aggregate; no LIMIT. Order by avg_roas desc, campaign_objective asc, roas_performance_tier asc.",
        required_aliases=("campaign_count", "avg_roas"),
        required_order_by=(
            "avg_roas desc",
            "campaign_objective asc",
            "roas_performance_tier asc",
        ),
    ),
    Text2SqlIntent(
        major="campaign_roi",
        middle="roi_review_target",
        minor="positive_net_payment_broad_list",
        table="ai_native.ai_campaign_roi_summary",
        routing_signals=("ROI review", "순결제액", "net payment", "검토 대상 캠페인"),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "roas",
            "has_positive_net_payment",
            "included_in_campaign_roi_review",
        ),
        limit_policy="No default LIMIT for benchmark broad-list question; preserve full ordered list.",
        required_order_by=("roas desc", "campaign_id asc"),
    ),
    Text2SqlIntent(
        major="campaign_roi",
        middle="region_review_aggregate",
        minor="review_campaign_count_avg_roas_by_region",
        table="ai_native.ai_campaign_roi_summary",
        routing_signals=(
            "campaign count and average ROAS by region",
            "지역별 ROI 검토 대상 캠페인 수",
            "campaign_region",
        ),
        required_columns=(
            "campaign_region",
            "review_campaign_count",
            "avg_roas",
        ),
        limit_policy="Aggregate; no LIMIT. Filter included_in_campaign_roi_review = true and order by avg_roas desc, campaign_region asc.",
        required_aliases=("review_campaign_count", "avg_roas"),
        required_order_by=("avg_roas desc", "campaign_region asc"),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="latest_snapshot",
        minor="actual_above_predicted",
        table="marts.mart_campaign_roas_prediction_monitor",
        routing_signals=("actual ROAS exceeds predicted", "실제 ROAS가 예측보다 높", "positive error"),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "actual_roas",
            "predicted_roas",
            "roas_prediction_error",
        ),
        limit_policy="No default LIMIT for benchmark broad-list question; preserve full ordered list.",
        required_order_by=("roas_prediction_error desc", "campaign_id asc"),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="latest_snapshot",
        minor="largest_absolute_prediction_error",
        table="marts.mart_campaign_roas_prediction_monitor",
        routing_signals=(
            "largest ROAS prediction errors",
            "largest prediction error",
            "큰 예측 오차",
        ),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "actual_roas",
            "predicted_roas",
            "absolute_roas_prediction_error",
        ),
        limit_policy="Use latest snapshot and order by absolute_roas_prediction_error desc, campaign_id asc. Do not use signed roas_prediction_error for largest-error ranking.",
        required_order_by=("absolute_roas_prediction_error desc", "campaign_id asc"),
        metric_semantics=("largest_error_uses_absolute",),
        forbidden_order_by_columns=("roas_prediction_error",),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="latest_snapshot_aggregate",
        minor="objective_actual_vs_predicted",
        table="marts.mart_campaign_roas_prediction_monitor",
        routing_signals=("average actual ROAS and predicted ROAS by objective",),
        required_columns=(
            "objective",
            "campaign_count",
            "avg_actual_roas",
            "avg_predicted_roas",
            "avg_roas_prediction_error",
        ),
        limit_policy="Aggregate; no LIMIT unless user asks for Top N.",
        required_aliases=(
            "campaign_count",
            "avg_actual_roas",
            "avg_predicted_roas",
            "avg_roas_prediction_error",
        ),
        required_order_by=("avg_roas_prediction_error desc",),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="latest_snapshot_aggregate",
        minor="objective_mae_summary",
        table="marts.mart_campaign_roas_prediction_monitor",
        routing_signals=(
            "objective별 MAE",
            "MAE가 큰 순서",
            "average absolute error by objective",
            "MAE by objective",
        ),
        required_columns=("objective", "campaign_count", "mae"),
        limit_policy="Aggregate latest snapshot by objective; no LIMIT. MAE must be avg(absolute_roas_prediction_error).",
        required_aliases=("campaign_count", "mae"),
        required_order_by=("mae desc", "objective asc"),
        metric_semantics=("mae_uses_absolute_error",),
        canonical_sql=(
            "select\n"
            "    objective,\n"
            "    count(*) as campaign_count,\n"
            "    avg(absolute_roas_prediction_error) as mae\n"
            "from marts.mart_campaign_roas_prediction_monitor\n"
            "where scoring_snapshot_date = (\n"
            "    select max(scoring_snapshot_date)\n"
            "    from marts.mart_campaign_roas_prediction_monitor\n"
            ")\n"
            "group by objective\n"
            "order by mae desc, objective asc"
        ),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="latest_snapshot_aggregate",
        minor="model_mae_bias_summary",
        table="marts.mart_campaign_roas_prediction_monitor",
        routing_signals=("MAE and bias", "MAE와 bias", "최신 ROAS 예측 모델"),
        required_columns=("model_name", "prediction_rows", "mae", "bias"),
        limit_policy="Aggregate by model_name over latest snapshot; no LIMIT.",
        required_aliases=("prediction_rows", "mae", "bias"),
        required_order_by=("model_name asc",),
        metric_semantics=("mae_uses_absolute_error", "bias_uses_signed_error"),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="roi_tier_join",
        minor="roi_tier_error_summary",
        table="marts.mart_campaign_roas_prediction_monitor join ai_native.ai_campaign_roi_summary",
        routing_signals=(
            "prediction error by tier summary",
            "tier별 예측 오차",
            "ROI tier별 예측 오차",
            "campaign ROI tier별 예측 오차",
        ),
        required_columns=("roas_performance_tier", "campaign_count", "mae", "bias"),
        limit_policy="Aggregate latest snapshot by roi.roas_performance_tier; no LIMIT.",
        required_aliases=("campaign_count", "mae", "bias"),
        required_order_by=("mae desc", "roas_performance_tier asc"),
        metric_semantics=("mae_uses_absolute_error", "bias_uses_signed_error"),
        canonical_sql=(
            "select\n"
            "    roi.roas_performance_tier,\n"
            "    count(*) as campaign_count,\n"
            "    avg(monitor.absolute_roas_prediction_error) as mae,\n"
            "    avg(monitor.roas_prediction_error) as bias\n"
            "from marts.mart_campaign_roas_prediction_monitor as monitor\n"
            "join ai_native.ai_campaign_roi_summary as roi\n"
            "  on monitor.campaign_id = roi.campaign_id\n"
            "where monitor.scoring_snapshot_date = (\n"
            "    select max(scoring_snapshot_date)\n"
            "    from marts.mart_campaign_roas_prediction_monitor\n"
            ")\n"
            "group by roi.roas_performance_tier\n"
            "order by mae desc, roi.roas_performance_tier asc"
        ),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="roi_tier_join",
        minor="absolute_error_threshold_with_tier",
        table="marts.mart_campaign_roas_prediction_monitor join ai_native.ai_campaign_roi_summary",
        routing_signals=(
            "absolute ROAS error at least 0.05",
            "absolute error at least",
            "0.05, with campaign ROI tier",
        ),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "roas_performance_tier",
            "absolute_roas_prediction_error",
        ),
        limit_policy="Filter latest snapshot to absolute_roas_prediction_error >= 0.05; no default LIMIT.",
        required_order_by=("absolute_roas_prediction_error desc", "campaign_id asc"),
        metric_semantics=("largest_error_uses_absolute",),
    ),
    Text2SqlIntent(
        major="prediction_monitor",
        middle="roi_tier_join",
        minor="latest_error_with_tier",
        table="marts.mart_campaign_roas_prediction_monitor join ai_native.ai_campaign_roi_summary",
        routing_signals=("ROI tier", "ROAS performance tier", "prediction error by tier"),
        required_columns=(
            "campaign_id",
            "campaign_name",
            "roas_performance_tier",
            "actual_roas",
            "predicted_roas",
            "absolute_roas_prediction_error",
        ),
        limit_policy="Use explicit user limit; p5_q011 expects LIMIT 10.",
        required_order_by=("absolute_roas_prediction_error desc", "campaign_id asc"),
        metric_semantics=("largest_error_uses_absolute",),
    ),
    Text2SqlIntent(
        major="not_answerable",
        middle="unavailable_metric",
        minor="views_impressions_clicks",
        table="none",
        routing_signals=("views", "조회수", "impressions", "노출수", "clicks", "클릭수"),
        required_columns=(),
        limit_policy="Return not_answerable; do not substitute unless user accepts a supported proxy.",
    ),
)


def find_best_intent_for_question(question: str) -> Text2SqlIntent | None:
    normalized_question = normalize_for_intent_match(question)
    scored_intents = [
        (score_intent_match(normalized_question, intent), intent)
        for intent in TEXT2SQL_INTENT_CATALOG
    ]
    scored_intents = [
        (score, intent)
        for score, intent in scored_intents
        if score > 0 and intent.major != "not_answerable"
    ]
    if not scored_intents:
        return None
    return max(scored_intents, key=lambda item: item[0])[1]


def normalize_for_intent_match(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


def score_intent_match(normalized_question: str, intent: Text2SqlIntent) -> int:
    score = 0
    for signal in intent.routing_signals:
        normalized_signal = normalize_for_intent_match(signal)
        if normalized_signal and normalized_signal in normalized_question:
            score += max(1, len(normalized_signal.split()))
    return score


def iter_intent_contract_lines(intent: Text2SqlIntent) -> Iterable[str]:
    required_select_columns = intent.required_select_columns or intent.required_columns
    yield f"Intent: {intent.major} -> {intent.middle} -> {intent.minor}"
    yield f"Required SELECT columns: {', '.join(required_select_columns) or 'none'}"
    yield f"Required aliases: {', '.join(intent.required_aliases) or 'none'}"
    yield f"Required ORDER BY: {', '.join(intent.required_order_by) or 'none'}"
    yield f"Metric semantics: {', '.join(intent.metric_semantics) or 'none'}"
    yield (
        "Forbidden ORDER BY columns: "
        f"{', '.join(intent.forbidden_order_by_columns) or 'none'}"
    )
    if intent.canonical_sql:
        yield "Canonical SQL:"
        yield intent.canonical_sql


def build_actual_column_catalog() -> str:
    lines = [
        "Actual Allowed Table and Column Catalog:",
        "- Treat this section as the only source of truth for SQL table and column names.",
        "- Concept names in rulebooks are not SQL columns unless listed here.",
    ]
    for table in ALLOWED_TEXT2SQL_TABLES:
        lines.extend(
            [
                f"- {table.name}",
                f"  Grain: {table.grain}",
                f"  Purpose: {table.purpose}",
                f"  Columns: {', '.join(table.columns)}",
            ]
        )
    return "\n".join(lines)


def build_intent_routing_catalog() -> str:
    lines = [
        "Natural-Language Intent Routing Catalog:",
        "- Route every question in this order: major category -> middle category -> minor intent.",
        "- After selecting the minor intent, use its table, required output columns, and limit policy.",
        "- If multiple intents match, choose the narrowest intent with the strongest routing signals.",
    ]
    for intent in TEXT2SQL_INTENT_CATALOG:
        lines.extend(
            [
                f"- Major: {intent.major}",
                f"  Middle: {intent.middle}",
                f"  Minor: {intent.minor}",
                f"  Table: {intent.table}",
                f"  Routing signals: {', '.join(intent.routing_signals)}",
                f"  Required output columns: {', '.join(intent.required_columns) or 'none'}",
                f"  Required SELECT columns: {', '.join(intent.required_select_columns or intent.required_columns) or 'none'}",
                f"  Required aliases: {', '.join(intent.required_aliases) or 'none'}",
                f"  Required ORDER BY: {', '.join(intent.required_order_by) or 'none'}",
                f"  Metric semantics: {', '.join(intent.metric_semantics) or 'none'}",
                f"  Limit policy: {intent.limit_policy}",
            ]
        )
    return "\n".join(lines)
