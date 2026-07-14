from __future__ import annotations

import re
from dataclasses import dataclass

from agent.text2sql.registry import BLOCKED_SQL_TOKENS, MAX_RESULT_ROWS
from agent.text2sql.schema_catalog import ALLOWED_COLUMNS_BY_TABLE, ALLOWED_TEXT2SQL_TABLE_NAMES

ALLOWED_TABLES = ALLOWED_TEXT2SQL_TABLE_NAMES

AGGREGATE_PATTERN = re.compile(r"\b(count|avg|sum|min|max)\s*\(", re.IGNORECASE)
COMMENT_PATTERN = re.compile(r"(--|/\*)")
TABLE_PATTERN = re.compile(
    r"\b(?:from|join)\s+([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)",
    re.IGNORECASE,
)
TABLE_ALIAS_PATTERN = re.compile(
    r"\b(?:from|join)\s+([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)"
    r"(?:\s+(?:as\s+)?([a-zA-Z_][\w]*))?",
    re.IGNORECASE,
)
QUALIFIED_COLUMN_PATTERN = re.compile(
    r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b",
    re.IGNORECASE,
)
IDENTIFIER_PATTERN = re.compile(r"\b[a-zA-Z_][\w]*\b")
LIMIT_PATTERN = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
ORDER_BY_PATTERN = re.compile(r"\border\s+by\b", re.IGNORECASE)
STRING_LITERAL_PATTERN = re.compile(r"'(?:''|[^'])*'")
SELECT_FROM_PATTERN = re.compile(r"\bselect\b(.*?)\bfrom\b", re.IGNORECASE | re.DOTALL)
ORDER_BY_CLAUSE_PATTERN = re.compile(
    r"\border\s+by\b(.*?)(?:\blimit\b|\boffset\b|$)",
    re.IGNORECASE | re.DOTALL,
)

SQL_KEYWORDS = frozenset(
    {
        "and",
        "as",
        "asc",
        "abs",
        "avg",
        "between",
        "by",
        "case",
        "coalesce",
        "count",
        "cast",
        "desc",
        "distinct",
        "else",
        "end",
        "false",
        "from",
        "group",
        "having",
        "in",
        "is",
        "join",
        "left",
        "limit",
        "max",
        "min",
        "not",
        "null",
        "on",
        "or",
        "order",
        "over",
        "right",
        "round",
        "select",
        "sum",
        "then",
        "true",
        "when",
        "where",
        "with",
    }
)


class Text2SqlValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SqlValidationResult:
    sql: str
    referenced_tables: tuple[str, ...]
    limit: int | None
    referenced_columns: tuple[str, ...] = ()


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

    referenced_columns = validate_referenced_columns(stripped_sql, referenced_tables)

    limit = extract_limit(stripped_sql)
    is_aggregate = bool(AGGREGATE_PATTERN.search(stripped_sql))

    if limit is None and not is_aggregate and not has_order_by(stripped_sql):
        raise Text2SqlValidationError(
            "Non-aggregate SQL without LIMIT must include deterministic ORDER BY."
        )

    if limit is not None and limit > max_result_rows:
        raise Text2SqlValidationError(
            f"SQL LIMIT {limit} exceeds max_result_rows={max_result_rows}."
        )

    return SqlValidationResult(
        sql=stripped_sql,
        referenced_tables=referenced_tables,
        limit=limit,
        referenced_columns=referenced_columns,
    )


def extract_limit(sql: str) -> int | None:
    matches = LIMIT_PATTERN.findall(sql)
    if not matches:
        return None
    return int(matches[-1])


def has_order_by(sql: str) -> bool:
    return bool(ORDER_BY_PATTERN.search(sql))


def validate_referenced_columns(
    sql: str,
    referenced_tables: tuple[str, ...],
    allowed_columns_by_table: dict[str, frozenset[str]] = ALLOWED_COLUMNS_BY_TABLE,
) -> tuple[str, ...]:
    alias_to_table = extract_table_aliases(sql, referenced_tables)
    valid_columns = set().union(
        *[
            allowed_columns_by_table.get(table_name, frozenset())
            for table_name in referenced_tables
        ]
    )
    referenced_columns: set[str] = set()

    for qualifier, column_name in QUALIFIED_COLUMN_PATTERN.findall(sql):
        qualified_table_name = f"{qualifier.lower()}.{column_name.lower()}"
        if qualified_table_name in referenced_tables:
            continue

        table_name = alias_to_table.get(qualifier.lower())
        if table_name is None:
            raise Text2SqlValidationError(
                f"SQL references unknown table alias or qualifier: {qualifier}."
            )
        if column_name.lower() not in allowed_columns_by_table[table_name]:
            raise Text2SqlValidationError(
                f"SQL references unknown column {qualifier}.{column_name} "
                f"for table {table_name}."
            )
        referenced_columns.add(f"{qualifier.lower()}.{column_name.lower()}")

    bare_identifiers = extract_bare_column_identifiers(sql)
    table_aliases = set(alias_to_table)
    output_aliases = extract_output_aliases(sql)
    ignored_identifiers = SQL_KEYWORDS | table_aliases | output_aliases

    for identifier in bare_identifiers:
        normalized = identifier.lower()
        if normalized in ignored_identifiers:
            continue
        if normalized in valid_columns:
            referenced_columns.add(normalized)
            continue
        raise Text2SqlValidationError(f"SQL references unknown column: {identifier}.")

    return tuple(sorted(referenced_columns))


def extract_table_aliases(sql: str, referenced_tables: tuple[str, ...]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table_name in referenced_tables:
        aliases[table_name.split(".")[-1]] = table_name

    for table_name, alias in TABLE_ALIAS_PATTERN.findall(sql):
        normalized_table_name = table_name.lower()
        if alias and alias.lower() not in SQL_KEYWORDS:
            aliases[alias.lower()] = normalized_table_name

    return aliases


def extract_bare_column_identifiers(sql: str) -> set[str]:
    cleaned_sql = STRING_LITERAL_PATTERN.sub(" ", sql)
    cleaned_sql = QUALIFIED_COLUMN_PATTERN.sub(" ", cleaned_sql)
    return {
        identifier
        for identifier in IDENTIFIER_PATTERN.findall(cleaned_sql)
        if not identifier.isdigit()
    }


def extract_output_aliases(sql: str) -> frozenset[str]:
    match = SELECT_FROM_PATTERN.search(sql)
    if match is None:
        return frozenset()

    aliases: set[str] = set()
    for expression in split_select_expressions(match.group(1)):
        as_match = re.search(r"\bas\s+([a-zA-Z_][\w]*)\s*$", expression, re.IGNORECASE)
        if as_match:
            aliases.add(as_match.group(1).lower())
            continue

        parts = expression.strip().split()
        if len(parts) > 1 and re.search(r"[()\s]", expression):
            aliases.add(parts[-1].lower())

    return frozenset(aliases)


def extract_select_output_names(sql: str) -> frozenset[str]:
    match = SELECT_FROM_PATTERN.search(sql)
    if match is None:
        return frozenset()

    output_names: set[str] = set()
    for expression in split_select_expressions(match.group(1)):
        normalized_expression = expression.strip()
        as_match = re.search(
            r"\bas\s+([a-zA-Z_][\w]*)\s*$",
            normalized_expression,
            re.IGNORECASE,
        )
        if as_match:
            output_names.add(as_match.group(1).lower())
            continue

        if re.search(r"\b(count|avg|sum|min|max)\s*\(", normalized_expression, re.IGNORECASE):
            parts = normalized_expression.split()
            if len(parts) > 1:
                output_names.add(parts[-1].lower())
            continue

        column_match = re.search(
            r"(?:\b[a-zA-Z_][\w]*\.)?([a-zA-Z_][\w]*)\s*$",
            normalized_expression,
        )
        if column_match:
            output_names.add(column_match.group(1).lower())

    return frozenset(output_names)


def extract_order_by_clause(sql: str) -> str:
    match = ORDER_BY_CLAUSE_PATTERN.search(sql)
    if match is None:
        return ""
    return normalize_sql_fragment(match.group(1))


def normalize_sql_fragment(value: str) -> str:
    return " ".join(value.casefold().replace("\n", " ").split())


def order_by_contains_terms(sql: str, required_terms: tuple[str, ...]) -> bool:
    order_by_clause = extract_order_by_clause(sql)
    if not order_by_clause:
        return False
    return all(normalize_sql_fragment(term) in order_by_clause for term in required_terms)


def order_by_uses_column(sql: str, column_name: str) -> bool:
    order_by_clause = extract_order_by_clause(sql)
    if not order_by_clause:
        return False
    return re.search(rf"\b{re.escape(column_name.casefold())}\b", order_by_clause) is not None


def split_select_expressions(select_clause: str) -> list[str]:
    expressions: list[str] = []
    current: list[str] = []
    depth = 0

    for char in select_clause:
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        elif char == "," and depth == 0:
            expressions.append("".join(current).strip())
            current = []
            continue
        current.append(char)

    if current:
        expressions.append("".join(current).strip())

    return expressions
