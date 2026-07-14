from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

import psycopg

from agent.text2sql.registry import serialize_value
from agent.text2sql.validator import order_by_contains_terms

LIMIT_PATTERN = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
JOIN_PATTERN = re.compile(r"\bjoin\b", re.IGNORECASE)


@dataclass(frozen=True)
class StrictEvalResult:
    question_id: str
    original_status: str
    strict_status: str
    failure_type: str | None
    reason: str
    expected_rows: int
    actual_rows: int | None
    expected_columns: tuple[str, ...]
    generated_columns: tuple[str, ...]
    missing_required_features: tuple[str, ...]
    order_sensitive: bool
    first_diff_row: int | None = None
    expected_preview: list[dict[str, Any]] | None = None
    generated_preview: list[dict[str, Any]] | None = None


def compare_case_strict(
    case: dict[str, Any],
    conn: psycopg.Connection,
    numeric_tolerance: float = 1e-6,
) -> StrictEvalResult:
    question_id = str(case["question_id"])
    original_status = str(case["status"])
    expected_columns = tuple(str(column) for column in case.get("expected_columns", []))
    generated_sql = case.get("generated_sql")
    expected_sql = str(case.get("expected_sql", "")).strip()
    expected_row_count = int(case.get("expected_rows") or 0)
    actual_row_count = case.get("actual_rows")
    if actual_row_count is not None:
        actual_row_count = int(actual_row_count)

    if not isinstance(generated_sql, str) or not generated_sql.strip():
        return StrictEvalResult(
            question_id=question_id,
            original_status=original_status,
            strict_status=original_status,
            failure_type=status_to_failure_type(original_status),
            reason="No generated SQL is available for strict comparison.",
            expected_rows=expected_row_count,
            actual_rows=actual_row_count,
            expected_columns=expected_columns,
            generated_columns=(),
            missing_required_features=(),
            order_sensitive=is_order_sensitive(case),
            expected_preview=[],
            generated_preview=[],
        )

    missing_features = find_missing_required_features(case, generated_sql)
    if missing_features:
        generated_columns = fetch_column_names_safely(conn, generated_sql)
        return StrictEvalResult(
            question_id=question_id,
            original_status=original_status,
            strict_status="FAIL",
            failure_type="missing_required_sql_feature",
            reason=f"Generated SQL is missing required feature(s): {', '.join(missing_features)}.",
            expected_rows=expected_row_count,
            actual_rows=actual_row_count,
            expected_columns=expected_columns,
            generated_columns=generated_columns,
            missing_required_features=missing_features,
            order_sensitive=is_order_sensitive(case),
            expected_preview=[],
            generated_preview=[],
        )

    try:
        expected_rows = fetch_rows(conn, expected_sql)
        generated_rows = fetch_rows(conn, generated_sql)
    except psycopg.Error as exc:
        conn.rollback()
        return StrictEvalResult(
            question_id=question_id,
            original_status=original_status,
            strict_status="FAIL",
            failure_type="sql_execution_error",
            reason=f"Strict comparison SQL execution failed: {exc.__class__.__name__}: {exc}",
            expected_rows=expected_row_count,
            actual_rows=actual_row_count,
            expected_columns=expected_columns,
            generated_columns=(),
            missing_required_features=(),
            order_sensitive=is_order_sensitive(case),
            expected_preview=[],
            generated_preview=[],
        )

    generated_columns = tuple(generated_rows[0].keys()) if generated_rows else ()
    expected_result_columns = tuple(expected_rows[0].keys()) if expected_rows else expected_columns
    missing_columns = [
        column for column in expected_columns if column not in generated_columns
    ]
    if missing_columns:
        return StrictEvalResult(
            question_id=question_id,
            original_status=original_status,
            strict_status="FAIL",
            failure_type="missing_expected_columns",
            reason=f"Generated result is missing expected column(s): {', '.join(missing_columns)}.",
            expected_rows=len(expected_rows),
            actual_rows=len(generated_rows),
            expected_columns=expected_columns,
            generated_columns=generated_columns,
            missing_required_features=(),
            order_sensitive=is_order_sensitive(case),
            expected_preview=preview_rows(expected_rows, expected_columns),
            generated_preview=preview_rows(generated_rows, expected_columns),
        )

    if len(expected_rows) != len(generated_rows):
        return StrictEvalResult(
            question_id=question_id,
            original_status=original_status,
            strict_status="FAIL",
            failure_type="row_count_mismatch",
            reason=f"Expected {len(expected_rows)} row(s), got {len(generated_rows)} row(s).",
            expected_rows=len(expected_rows),
            actual_rows=len(generated_rows),
            expected_columns=expected_columns,
            generated_columns=generated_columns,
            missing_required_features=(),
            order_sensitive=is_order_sensitive(case),
            expected_preview=preview_rows(expected_rows, expected_columns),
            generated_preview=preview_rows(generated_rows, expected_columns),
        )

    if not expected_rows and not generated_rows:
        return pass_result(case, expected_columns, generated_columns)

    columns_to_compare = expected_columns or expected_result_columns
    if is_order_sensitive(case):
        rows_match = ordered_rows_match(
            expected_rows,
            generated_rows,
            columns_to_compare,
            numeric_tolerance,
        )
    else:
        rows_match = unordered_rows_match(
            expected_rows,
            generated_rows,
            columns_to_compare,
            numeric_tolerance,
        )

    if rows_match:
        return pass_result(case, expected_columns, generated_columns)

    first_diff_row = find_first_diff_row(
        expected_rows,
        generated_rows,
        columns_to_compare,
        numeric_tolerance,
    )
    return StrictEvalResult(
        question_id=question_id,
        original_status=original_status,
        strict_status="FAIL",
        failure_type="result_set_mismatch",
        reason="Generated result set differs from the expected result set.",
        expected_rows=len(expected_rows),
        actual_rows=len(generated_rows),
        expected_columns=expected_columns,
        generated_columns=generated_columns,
        missing_required_features=(),
        order_sensitive=is_order_sensitive(case),
        first_diff_row=first_diff_row,
        expected_preview=preview_rows(expected_rows, columns_to_compare),
        generated_preview=preview_rows(generated_rows, columns_to_compare),
    )


def pass_result(
    case: dict[str, Any],
    expected_columns: tuple[str, ...],
    generated_columns: tuple[str, ...],
) -> StrictEvalResult:
    expected_rows = int(case.get("expected_rows") or 0)
    actual_rows = case.get("actual_rows")
    if actual_rows is not None:
        actual_rows = int(actual_rows)
    return StrictEvalResult(
        question_id=str(case["question_id"]),
        original_status=str(case["status"]),
        strict_status="PASS",
        failure_type=None,
        reason="Generated SQL matched expected columns and result rows under strict comparison.",
        expected_rows=expected_rows,
        actual_rows=actual_rows,
        expected_columns=expected_columns,
        generated_columns=generated_columns,
        missing_required_features=(),
        order_sensitive=is_order_sensitive(case),
        expected_preview=[],
        generated_preview=[],
    )


def fetch_rows(conn: psycopg.Connection, sql: str) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql.strip().rstrip(";"))
        records = cur.fetchall()
        columns = [column.name for column in cur.description or []]

    return [
        {
            column_name: serialize_value(value)
            for column_name, value in zip(columns, record, strict=True)
        }
        for record in records
    ]


def fetch_column_names_safely(
    conn: psycopg.Connection,
    sql: str,
) -> tuple[str, ...]:
    try:
        rows = fetch_rows(conn, sql)
    except psycopg.Error:
        conn.rollback()
        return ()
    if not rows:
        return ()
    return tuple(rows[0].keys())


def is_order_sensitive(case: dict[str, Any]) -> bool:
    expected_sql = str(case.get("expected_sql", "")).lower()
    features = {str(feature) for feature in case.get("required_sql_features", [])}
    return (
        "order by" in expected_sql
        or any(feature.startswith("order_by") for feature in features)
        or any(feature.startswith("limit") for feature in features)
        or "limit" in features
    )


def ordered_rows_match(
    expected_rows: list[dict[str, Any]],
    generated_rows: list[dict[str, Any]],
    columns: tuple[str, ...],
    numeric_tolerance: float,
) -> bool:
    return all(
        row_values_match(expected_row, generated_row, columns, numeric_tolerance)
        for expected_row, generated_row in zip(expected_rows, generated_rows, strict=True)
    )


def unordered_rows_match(
    expected_rows: list[dict[str, Any]],
    generated_rows: list[dict[str, Any]],
    columns: tuple[str, ...],
    numeric_tolerance: float,
) -> bool:
    expected_signatures = sorted(
        row_signature(row, columns, numeric_tolerance) for row in expected_rows
    )
    generated_signatures = sorted(
        row_signature(row, columns, numeric_tolerance) for row in generated_rows
    )
    return expected_signatures == generated_signatures


def find_first_diff_row(
    expected_rows: list[dict[str, Any]],
    generated_rows: list[dict[str, Any]],
    columns: tuple[str, ...],
    numeric_tolerance: float,
) -> int | None:
    for index, (expected_row, generated_row) in enumerate(
        zip(expected_rows, generated_rows, strict=True),
        start=1,
    ):
        if not row_values_match(expected_row, generated_row, columns, numeric_tolerance):
            return index
    return None


def preview_rows(
    rows: list[dict[str, Any]],
    columns: tuple[str, ...],
    limit: int = 3,
) -> list[dict[str, Any]]:
    return [
        {
            column: row.get(column)
            for column in columns
        }
        for row in rows[:limit]
    ]


def row_values_match(
    expected_row: dict[str, Any],
    generated_row: dict[str, Any],
    columns: tuple[str, ...],
    numeric_tolerance: float,
) -> bool:
    return all(
        values_match(expected_row.get(column), generated_row.get(column), numeric_tolerance)
        for column in columns
    )


def row_signature(
    row: dict[str, Any],
    columns: tuple[str, ...],
    numeric_tolerance: float,
) -> str:
    values = [normalize_value(row.get(column), numeric_tolerance) for column in columns]
    return json.dumps(values, ensure_ascii=False, sort_keys=True)


def values_match(left: Any, right: Any, numeric_tolerance: float) -> bool:
    if isinstance(left, int | float) and isinstance(right, int | float):
        return math.isclose(float(left), float(right), abs_tol=numeric_tolerance)
    return left == right


def normalize_value(value: Any, numeric_tolerance: float) -> Any:
    if isinstance(value, int | float):
        if numeric_tolerance <= 0:
            return value
        digits = max(0, round(-math.log10(numeric_tolerance)))
        return round(float(value), digits)
    return value


def find_missing_required_features(
    case: dict[str, Any],
    generated_sql: str,
) -> tuple[str, ...]:
    sql = generated_sql.lower()
    missing = [
        feature
        for feature in case.get("required_sql_features", [])
        if not feature_is_present(str(feature), sql)
    ]
    return tuple(missing)


def feature_is_present(feature: str, sql: str) -> bool:
    if feature == "latest_scoring_snapshot_filter":
        return "scoring_snapshot_date" in sql and "max(scoring_snapshot_date)" in sql
    if feature.startswith("join_"):
        return JOIN_PATTERN.search(sql) is not None
    if feature.startswith("limit_"):
        expected_limit = feature.removeprefix("limit_")
        if expected_limit.isdigit():
            return extract_limit(sql) == int(expected_limit)
        return extract_limit(sql) is not None
    if feature == "limit":
        return extract_limit(sql) is not None
    if feature == "filter_boolean_included_in_creator_review":
        return "included_in_creator_review" in sql and "true" in sql
    if feature == "filter_boolean_has_engagement_signal":
        return "has_engagement_signal" in sql and "true" in sql
    if feature == "filter_boolean_has_positive_net_payment":
        return "has_positive_net_payment" in sql and "true" in sql
    if feature == "filter_boolean_included_in_campaign_roi_review":
        return "included_in_campaign_roi_review" in sql and "true" in sql
    if feature == "filter_sponsored_candidate_posts_gte_1":
        return "sponsored_candidate_posts" in sql and (">= 1" in sql or ">0" in sql or "> 0" in sql)
    if feature == "filter_sponsored_candidate_posts_eq_0":
        return "sponsored_candidate_posts" in sql and "= 0" in sql
    if feature == "filter_total_posts_gte_2":
        return "total_posts" in sql and ">= 2" in sql
    if feature == "filter_campaign_objective_conversion":
        return "campaign_objective" in sql and "conversion" in sql
    if feature == "filter_positive_prediction_error":
        return "roas_prediction_error" in sql and "> 0" in sql
    if feature == "filter_absolute_error_gte_005":
        return "absolute_roas_prediction_error" in sql and "0.05" in sql
    if feature.startswith("group_by_"):
        return "group by" in sql and feature.removeprefix("group_by_") in sql
    if feature in {"aggregate_mae", "aggregate_bias"}:
        alias = "mae" if feature == "aggregate_mae" else "bias"
        return "avg(" in sql and alias in sql
    if feature.startswith("aggregate_"):
        return any(function_name in sql for function_name in ("avg(", "count(", "sum("))
    if feature == "order_by_sponsored_priority":
        return order_by_contains_terms(
            sql,
            ("sponsored_candidate_posts desc", "sponsored_candidate_rate desc"),
        )
    if feature == "order_by_sponsored_candidate_rate_desc":
        return order_by_contains_terms(sql, ("sponsored_candidate_rate desc",))
    if feature == "order_by_hidden_likes_rate_desc":
        return order_by_contains_terms(sql, ("hidden_likes_rate desc",))
    if feature == "order_by_avg_comments_count_desc":
        return order_by_contains_terms(sql, ("avg_comments_count desc",))
    if feature == "order_by_roas_desc":
        return order_by_contains_terms(sql, ("roas desc",))
    if feature == "order_by_absolute_error_desc":
        return order_by_contains_terms(sql, ("absolute_roas_prediction_error desc",))
    if feature == "order_by_prediction_error_desc":
        return order_by_contains_terms(sql, ("roas_prediction_error desc",))
    if feature.startswith("order_by_"):
        return "order by" in sql
    if feature.endswith("_table_selection"):
        return True
    if feature.startswith(("korean_synonym_",)):
        return True
    return True


def extract_limit(sql: str) -> int | None:
    matches = LIMIT_PATTERN.findall(sql)
    if not matches:
        return None
    return int(matches[-1])


def status_to_failure_type(status: str) -> str | None:
    if status == "PASS":
        return None
    if status == "REFUSED":
        return "answerable_refused"
    if status == "BLOCKED":
        return "validator_blocked"
    return "no_generated_sql"
