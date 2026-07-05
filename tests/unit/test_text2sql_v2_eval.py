from __future__ import annotations

import psycopg

from agent.eval.run_text2sql_v2_eval import (
    V2EvalCaseResult,
    evaluate_question,
    summarize_results,
)
from agent.text2sql.llm_client import SqlGenerationResponse


def test_summarize_results_counts_v2_eval_statuses() -> None:
    results = [
        V2EvalCaseResult(
            question_id="p5_q001",
            language="en",
            status="PASS",
            expected_rows=5,
            actual_rows=5,
            latency_ms=10.0,
            generated_sql="select 1",
            reason="answerable",
        ),
        V2EvalCaseResult(
            question_id="p5_q002",
            language="en",
            status="REFUSED",
            expected_rows=3,
            actual_rows=None,
            latency_ms=5.0,
            generated_sql=None,
            reason="not answerable",
        ),
        V2EvalCaseResult(
            question_id="p5_q003",
            language="ko",
            status="BLOCKED",
            expected_rows=10,
            actual_rows=None,
            latency_ms=20.0,
            generated_sql=None,
            reason="blocked",
        ),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 3
    assert summary["passed"] == 1
    assert summary["refused"] == 1
    assert summary["blocked"] == 1
    assert summary["answerable"] == 2
    assert summary["exec_acc"] == 0.5
    assert summary["refuse_rate"] == 0.3333
    assert summary["step"] == "text2sql_v2_eval"
    assert summary["model_score"]["tier"] == "needs_prompt_or_schema_tuning"


def test_evaluate_question_records_database_error_as_fail() -> None:
    class ErrorCursor:
        description = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def execute(self, sql: str) -> None:
            if "select campaign_id" in sql:
                raise psycopg.errors.CardinalityViolation(
                    "more than one row returned by a subquery"
                )

        def fetchmany(self, limit: int):
            return []

    class ErrorConnection:
        def __init__(self) -> None:
            self.rollback_called = False

        def cursor(self):
            return ErrorCursor()

        def rollback(self) -> None:
            self.rollback_called = True

    class ErrorClient:
        def generate_sql(self, request):
            return SqlGenerationResponse(
                answerability="answerable",
                sql=(
                    "select campaign_id "
                    "from ai_native.ai_campaign_roi_summary "
                    "limit 5"
                ),
                expected_tables=("ai_native.ai_campaign_roi_summary",),
                reason="unit test",
            )

    conn = ErrorConnection()
    question = {
        "id": "p5_q001",
        "language": "en",
        "question": "Which campaigns have the highest ROAS?",
        "current_result_rows": 5,
    }

    result = evaluate_question(question, conn, ErrorClient(), "llm_generated_sql_v2_mock")

    assert result.status == "FAIL"
    assert "Database execution error" in result.reason
    assert conn.rollback_called
