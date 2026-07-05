from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg

from agent.text2sql.llm_client import SqlGenerationClient, SqlGenerationRequest
from agent.text2sql.registry import MAX_RESULT_ROWS, serialize_value
from agent.text2sql.validator import SqlValidationResult, validate_generated_sql

SCHEMA_CONTEXT_V1 = """
Allowed tables:
- ai_native.ai_campaign_roi_summary: campaign grain ROI and payment performance.
  Columns: campaign_id, campaign_name, campaign_region, product_category,
  campaign_objective, campaign_budget_krw, total_payment_events,
  net_payment_amount_krw, roas, has_positive_net_payment,
  included_in_campaign_roi_review, roas_performance_tier.
  Example for highest ROAS:
  select campaign_id, campaign_name, roas, net_payment_amount_krw
  from ai_native.ai_campaign_roi_summary
  order by roas desc, net_payment_amount_krw desc
  limit 5
- marts.mart_campaign_roas_prediction_monitor: latest campaign ROAS prediction metrics.
  Columns: scoring_snapshot_date, model_name, campaign_id, campaign_name,
  predicted_roas, actual_roas, roas_prediction_error,
  absolute_roas_prediction_error, prediction_reason, training_rows_used.
  Use max(scoring_snapshot_date) for latest snapshot questions.
- ai_native.ai_creator_sponsored_summary: creator grain sponsored-content review signals.
  Columns: creator_username, creator_display_name, total_posts,
  sponsored_candidate_posts, hidden_likes_posts, avg_likes_count_clean,
  avg_comments_count, sponsored_candidate_rate, hidden_likes_rate,
  has_engagement_signal, included_in_creator_review.

Rules:
- Use only the columns listed above.
- Prefer ai_native.ai_campaign_roi_summary for campaign ROAS questions.
- Prefer marts.mart_campaign_roas_prediction_monitor for prediction error or MAE/bias questions.
- Prefer ai_native.ai_creator_sponsored_summary for creator, influencer, sponsored, or hidden-likes questions.
""".strip()
STATEMENT_TIMEOUT_MS = 5000


@dataclass(frozen=True)
class GeneratedText2SqlResult:
    question: str
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    answer: str
    mode: str
    expected_tables: tuple[str, ...]
    reason: str
    validation: SqlValidationResult


class Text2SqlNotAnswerableError(ValueError):
    pass


def execute_generated_question(
    question: str,
    conn: psycopg.Connection,
    client: SqlGenerationClient,
    schema_context: str = SCHEMA_CONTEXT_V1,
    statement_timeout_ms: int = STATEMENT_TIMEOUT_MS,
    mode: str = "llm_generated_sql_v2_mock",
) -> GeneratedText2SqlResult:
    generation = client.generate_sql(
        SqlGenerationRequest(question=question, schema_context=schema_context)
    )

    if generation.answerability != "answerable" or generation.sql is None:
        raise Text2SqlNotAnswerableError(generation.reason)

    validation = validate_generated_sql(generation.sql)

    with conn.cursor() as cur:
        cur.execute(f"set local statement_timeout = {int(statement_timeout_ms)}")
        cur.execute(validation.sql)
        records = cur.fetchmany(MAX_RESULT_ROWS)
        columns = [column.name for column in cur.description or []]

    rows = [
        {
            column_name: serialize_value(value)
            for column_name, value in zip(columns, record, strict=True)
        }
        for record in records
    ]

    return GeneratedText2SqlResult(
        question=question,
        sql=validation.sql,
        rows=rows,
        row_count=len(rows),
        answer=build_generated_answer(question, rows),
        mode=mode,
        expected_tables=generation.expected_tables,
        reason=generation.reason,
        validation=validation,
    )


def build_generated_answer(question: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"Generated Text2SQL v2 returned 0 rows for question={question!r}."

    preview = rows[0]
    preview_items = ", ".join(
        f"{column}={value}"
        for column, value in list(preview.items())[:3]
    )
    return (
        f"Generated Text2SQL v2 returned {len(rows)} rows. "
        f"Top row: {preview_items}."
    )
