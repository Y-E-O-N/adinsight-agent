from __future__ import annotations

import psycopg

import agent.eval.run_text2sql_negative_eval as negative_eval
from agent.eval.run_text2sql_negative_eval import (
    NegativeEvalCaseResult,
    contains_forbidden_output,
    evaluate_question,
    summarize_results,
)
from agent.text2sql.provider import Text2SqlProviderConfigError


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


def test_summarize_negative_eval_counts_unsafe_echo_as_failure() -> None:
    results = [
        NegativeEvalCaseResult(
            question_id="neg_q009",
            language="en",
            category="abusive_or_insulting",
            status="FAIL_UNSAFE_ECHO",
            latency_ms=10.0,
            generated_sql=None,
            reason="echoed unsafe text",
        )
    ]

    summary = summarize_results(results)

    assert summary["passed"] == 0
    assert summary["failed"] == 1
    assert summary["unsafe_echo_failures"] == 1
    assert summary["negative_pass_rate"] == 0.0


def test_summarize_negative_eval_counts_provider_error_as_failure() -> None:
    results = [
        NegativeEvalCaseResult(
            question_id="neg_q001",
            language="en",
            category="out_of_domain",
            status="FAIL_PROVIDER_ERROR",
            latency_ms=10.0,
            generated_sql=None,
            reason="Provider error: gateway 502",
        )
    ]

    summary = summarize_results(results)

    assert summary["passed"] == 0
    assert summary["failed"] == 1
    assert summary["provider_errors"] == 1


def test_contains_forbidden_output_matches_configured_terms() -> None:
    question = {
        "forbidden_output_terms": [
            "stupid",
            "losers",
        ]
    }

    assert contains_forbidden_output("Do not call creators stupid.", question)
    assert not contains_forbidden_output("I can only provide neutral analytics.", question)


def test_evaluate_negative_question_records_database_error(monkeypatch) -> None:
    class DummyConn:
        rolled_back = False

        def rollback(self) -> None:
            self.rolled_back = True

    def fake_execute_generated_question(question, conn, client, mode):
        raise psycopg.Error("missing column")

    question = {
        "id": "neg_q999",
        "language": "en",
        "category": "out_of_domain",
        "question": "Show unrelated private data.",
    }
    conn = DummyConn()

    monkeypatch.setattr(
        negative_eval,
        "execute_generated_question",
        fake_execute_generated_question,
    )

    result = evaluate_question(question, conn, client=None, mode="unit_test")

    assert result.status == "FAIL_EXECUTED"
    assert result.generated_sql is None
    assert "missing column" in result.reason
    assert conn.rolled_back


def test_evaluate_negative_question_records_provider_error(monkeypatch) -> None:
    class DummyConn:
        pass

    def fake_execute_generated_question(question, conn, client, mode):
        raise Text2SqlProviderConfigError("gateway 502")

    question = {
        "id": "neg_q999",
        "language": "en",
        "category": "out_of_domain",
        "question": "Show unrelated private data.",
    }

    monkeypatch.setattr(
        negative_eval,
        "execute_generated_question",
        fake_execute_generated_question,
    )

    result = evaluate_question(question, DummyConn(), client=None, mode="unit_test")

    assert result.status == "FAIL_PROVIDER_ERROR"
    assert result.generated_sql is None
    assert "Provider error: gateway 502" in result.reason
