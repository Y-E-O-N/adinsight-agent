from __future__ import annotations

from agent.eval.run_text2sql_negative_eval import NegativeEvalCaseResult, summarize_results


def test_summarize_negative_eval_counts_refused_blocked_and_failed() -> None:
    results = [
        NegativeEvalCaseResult(
            question_id="neg_q001",
            language="en",
            category="out_of_domain",
            status="PASS_REFUSED",
            latency_ms=10.0,
            generated_sql=None,
            reason="not answerable",
        ),
        NegativeEvalCaseResult(
            question_id="neg_q002",
            language="ko",
            category="unsafe_write_sql",
            status="PASS_BLOCKED",
            latency_ms=20.0,
            generated_sql=None,
            reason="blocked",
        ),
        NegativeEvalCaseResult(
            question_id="neg_q003",
            language="en",
            category="ambiguous_metric",
            status="FAIL_EXECUTED",
            latency_ms=30.0,
            generated_sql="select 1",
            reason="executed",
        ),
    ]

    summary = summarize_results(results)

    assert summary["total"] == 3
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["refused"] == 1
    assert summary["blocked"] == 1
    assert summary["negative_pass_rate"] == 0.6667
    assert summary["p95_latency_ms"] == 30.0
