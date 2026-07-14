from __future__ import annotations

from agent.eval.build_text2sql_failure_improvement_model import (
    FailureEvidence,
    classify_lightweight_failure,
    classify_negative_failure,
    render_report,
)


def test_classify_lightweight_failure_maps_limit_mismatch() -> None:
    case = {
        "status": "FAIL",
        "expected_rows": 20,
        "actual_rows": 10,
        "generated_sql": "select campaign_id from ai_native.ai_campaign_roi_summary limit 10",
    }

    assert classify_lightweight_failure(case) == "limit_policy"


def test_classify_lightweight_failure_maps_wrong_column() -> None:
    case = {
        "status": "FAIL",
        "expected_rows": 3,
        "actual_rows": None,
        "reason": "Database execution error: UndefinedColumn: column objective does not exist",
        "generated_sql": "select objective from marts.mart_campaign_roas_prediction_monitor",
    }

    assert classify_lightweight_failure(case) == "schema_context_columns"


def test_classify_negative_failure_maps_unsafe_echo() -> None:
    case = {"status": "FAIL_UNSAFE_ECHO"}

    assert classify_negative_failure(case) == "unsafe_echo"


def test_render_report_prioritizes_evidence() -> None:
    report = render_report(
        [
            FailureEvidence(
                model="unit-model",
                question_id="p5_q007",
                source="strict",
                status="FAIL",
                failure_type="schema_context_columns",
                question="Compare by objective",
                recommendation="Fix schema context columns and add expected output-column examples.",
            )
        ]
    )

    assert "Fix schema context columns" in report
    assert "`p5_q007`" in report
