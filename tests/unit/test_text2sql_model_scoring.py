from __future__ import annotations

from agent.eval.text2sql_model_scoring import score_text2sql_model


def test_score_text2sql_model_classifies_production_candidate() -> None:
    summary = {
        "total": 18,
        "passed": 17,
        "failed": 0,
        "refused": 1,
        "blocked": 0,
        "p95_latency_ms": 4200.0,
    }

    score = score_text2sql_model(summary)

    assert score["composite_score"] == 98.61
    assert score["tier"] == "production_candidate"
    assert score["components"]["answerable_execution"] == 1.0
    assert score["components"]["total_pass_coverage"] == 0.9444


def test_score_text2sql_model_classifies_high_refusal_as_tuning_candidate() -> None:
    summary = {
        "total": 18,
        "passed": 8,
        "failed": 0,
        "refused": 10,
        "blocked": 0,
        "p95_latency_ms": 1000.0,
    }

    score = score_text2sql_model(summary)

    assert score["composite_score"] == 86.11
    assert score["tier"] == "needs_prompt_or_schema_tuning"
    assert score["components"]["total_pass_coverage"] == 0.4444


def test_score_text2sql_model_penalizes_slow_or_blocked_model() -> None:
    summary = {
        "total": 18,
        "passed": 4,
        "failed": 3,
        "refused": 8,
        "blocked": 3,
        "p95_latency_ms": 15000.0,
    }

    score = score_text2sql_model(summary)

    assert score["composite_score"] == 43.55
    assert score["tier"] == "not_recommended"
    assert score["components"]["safety"] == 0.8333
    assert score["components"]["latency"] == 0.3333
