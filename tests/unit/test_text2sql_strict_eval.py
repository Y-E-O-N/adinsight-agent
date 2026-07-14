from __future__ import annotations

from agent.eval import run_text2sql_v2_strict_eval as strict_runner
from agent.eval import text2sql_strict_eval as strict_eval
from agent.eval.text2sql_strict_eval import (
    compare_case_strict,
    find_missing_required_features,
)


def test_strict_eval_requires_all_expected_columns(monkeypatch) -> None:
    def fake_fetch_rows(conn, sql):
        if "expected" in sql:
            return [{"campaign_id": "camp_1", "campaign_name": "A"}]
        return [{"campaign_id": "camp_1"}]

    monkeypatch.setattr(strict_eval, "fetch_rows", fake_fetch_rows)
    case = {
        "question_id": "p5_q001",
        "status": "PASS",
        "expected_rows": 1,
        "actual_rows": 1,
        "expected_columns": ["campaign_id", "campaign_name"],
        "required_sql_features": [],
        "expected_sql": "select 'expected'",
        "generated_sql": "select 'generated'",
    }

    result = compare_case_strict(case, conn=None)

    assert result.strict_status == "FAIL"
    assert result.failure_type == "missing_expected_columns"
    assert result.original_status == "PASS"


def test_strict_eval_compares_full_ordered_result_set(monkeypatch) -> None:
    def fake_fetch_rows(conn, sql):
        if "expected" in sql:
            return [
                {"campaign_id": "camp_1", "roas": 0.2},
                {"campaign_id": "camp_2", "roas": 0.1},
            ]
        return [
            {"campaign_id": "camp_1", "roas": 0.2},
            {"campaign_id": "camp_3", "roas": 0.1},
        ]

    monkeypatch.setattr(strict_eval, "fetch_rows", fake_fetch_rows)
    case = {
        "question_id": "p5_q001",
        "status": "PASS",
        "expected_rows": 2,
        "actual_rows": 2,
        "expected_columns": ["campaign_id", "roas"],
        "required_sql_features": ["order_by_roas_desc"],
        "expected_sql": "select 'expected' order by roas desc",
        "generated_sql": "select 'generated' order by roas desc",
    }

    result = compare_case_strict(case, conn=None)

    assert result.strict_status == "FAIL"
    assert result.failure_type == "result_set_mismatch"
    assert result.order_sensitive


def test_strict_eval_allows_numeric_tolerance(monkeypatch) -> None:
    def fake_fetch_rows(conn, sql):
        if "expected" in sql:
            return [{"campaign_id": "camp_1", "roas": 0.2000001}]
        return [{"campaign_id": "camp_1", "roas": 0.2000002}]

    monkeypatch.setattr(strict_eval, "fetch_rows", fake_fetch_rows)
    case = {
        "question_id": "p5_q001",
        "status": "PASS",
        "expected_rows": 1,
        "actual_rows": 1,
        "expected_columns": ["campaign_id", "roas"],
        "required_sql_features": [],
        "expected_sql": "select 'expected'",
        "generated_sql": "select 'generated'",
    }

    result = compare_case_strict(case, conn=None, numeric_tolerance=1e-5)

    assert result.strict_status == "PASS"


def test_find_missing_required_features_flags_latest_snapshot() -> None:
    case = {
        "required_sql_features": ["latest_scoring_snapshot_filter", "aggregate_mae"],
    }
    sql = (
        "select model_name, avg(absolute_roas_prediction_error) as mae "
        "from marts.mart_campaign_roas_prediction_monitor "
        "group by model_name"
    )

    missing = find_missing_required_features(case, sql)

    assert missing == ("latest_scoring_snapshot_filter",)


def test_find_missing_required_features_detects_join_after_newline() -> None:
    case = {
        "required_sql_features": ["join_prediction_monitor_to_campaign_roi"],
    }
    sql = (
        "select monitor.campaign_id, roi.roas_performance_tier "
        "from marts.mart_campaign_roas_prediction_monitor as monitor\n"
        "join ai_native.ai_campaign_roi_summary as roi "
        "on monitor.campaign_id = roi.campaign_id"
    )

    missing = find_missing_required_features(case, sql)

    assert missing == ()


def test_find_missing_required_features_checks_specific_order_by_terms() -> None:
    case = {
        "required_sql_features": ["order_by_absolute_error_desc"],
    }
    sql = (
        "select campaign_id, absolute_roas_prediction_error "
        "from marts.mart_campaign_roas_prediction_monitor "
        "order by campaign_id asc"
    )

    missing = find_missing_required_features(case, sql)

    assert missing == ("order_by_absolute_error_desc",)


def test_strict_runner_merges_latest_question_contracts(tmp_path, monkeypatch) -> None:
    questions_path = tmp_path / "questions.yml"
    questions_path.write_text(
        """
questions:
  - id: p_unit
    question: "latest question"
    expected_model: ai_native.ai_campaign_roi_summary
    expected_columns:
      - campaign_id
      - roas
    required_sql_features:
      - order_by_roas_desc
    expected_sql: |
      select campaign_id, roas
      from ai_native.ai_campaign_roi_summary
      order by roas desc
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(strict_runner, "QUESTIONS_PATH", questions_path)
    payload = {
        "cases": [
            {
                "question_id": "p_unit",
                "question": "old question",
                "expected_columns": ["campaign_id"],
                "required_sql_features": [],
                "expected_sql": "select campaign_id from old_table",
            }
        ]
    }

    merged = strict_runner.merge_latest_question_contracts(payload)
    merged_case = merged["cases"][0]

    assert merged_case["question"] == "latest question"
    assert merged_case["expected_columns"] == ["campaign_id", "roas"]
    assert merged_case["required_sql_features"] == ["order_by_roas_desc"]
    assert "order by roas desc" in merged_case["expected_sql"]
