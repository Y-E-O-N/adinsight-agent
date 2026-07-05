from __future__ import annotations

from agent.eval.run_text2sql_v2_eval import V2EvalCaseResult, summarize_results


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
