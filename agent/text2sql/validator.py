from __future__ import annotations

import re
from dataclasses import dataclass

from agent.text2sql.registry import BLOCKED_SQL_TOKENS, MAX_RESULT_ROWS

ALLOWED_TABLES = frozenset(
    {
        "ai_native.ai_campaign_roi_summary",
        "marts.mart_campaign_roas_prediction_monitor",
        "ai_native.ai_creator_sponsored_summary",
    }
)

AGGREGATE_PATTERN = re.compile(r"\b(count|avg|sum|min|max)\s*\(", re.IGNORECASE)
COMMENT_PATTERN = re.compile(r"(--|/\*)")
TABLE_PATTERN = re.compile(
    r"\b(?:from|join)\s+([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)",
    re.IGNORECASE,
)
LIMIT_PATTERN = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)


class Text2SqlValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SqlValidationResult:
    sql: str
    referenced_tables: tuple[str, ...]
    limit: int | None


def validate_generated_sql(
    sql: str,
    allowed_tables: frozenset[str] = ALLOWED_TABLES,
    max_result_rows: int = MAX_RESULT_ROWS,
) -> SqlValidationResult:
    stripped_sql = sql.strip().rstrip(";")
    lowered_sql = stripped_sql.lower()

    if not stripped_sql:
        raise Text2SqlValidationError("SQL is empty.")

    if ";" in stripped_sql:
        raise Text2SqlValidationError("Multiple SQL statements are not allowed.")

    if COMMENT_PATTERN.search(stripped_sql):
        raise Text2SqlValidationError("SQL comments are not allowed.")

    if not (lowered_sql.startswith("select") or lowered_sql.startswith("with")):
        raise Text2SqlValidationError("Only SELECT or WITH SQL is allowed.")

    token_pattern = r"\b(" + "|".join(re.escape(token) for token in BLOCKED_SQL_TOKENS) + r")\b"
    if re.search(token_pattern, lowered_sql):
        raise Text2SqlValidationError("SQL contains a blocked token.")

    referenced_tables = tuple(
        table_name.lower()
        for table_name in TABLE_PATTERN.findall(stripped_sql)
    )
    if not referenced_tables:
        raise Text2SqlValidationError("SQL must reference at least one schema-qualified table.")

    disallowed_tables = [
        table_name for table_name in referenced_tables if table_name not in allowed_tables
    ]
    if disallowed_tables:
        raise Text2SqlValidationError(
            f"SQL references disallowed table(s): {', '.join(disallowed_tables)}."
        )

    limit = extract_limit(stripped_sql)
    is_aggregate = bool(AGGREGATE_PATTERN.search(stripped_sql))

    if limit is None and not is_aggregate:
        raise Text2SqlValidationError("Non-aggregate SQL must include an explicit LIMIT.")

    if limit is not None and limit > max_result_rows:
        raise Text2SqlValidationError(
            f"SQL LIMIT {limit} exceeds max_result_rows={max_result_rows}."
        )

    return SqlValidationResult(
        sql=stripped_sql,
        referenced_tables=referenced_tables,
        limit=limit,
    )


def extract_limit(sql: str) -> int | None:
    matches = LIMIT_PATTERN.findall(sql)
    if not matches:
        return None
    return int(matches[-1])
