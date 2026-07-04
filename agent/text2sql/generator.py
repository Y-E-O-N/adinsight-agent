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
- marts.mart_campaign_roas_prediction_monitor: latest campaign ROAS prediction metrics.
- ai_native.ai_creator_sponsored_summary: creator grain sponsored-content review signals.
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
        mode="llm_generated_sql_v2_mock",
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
