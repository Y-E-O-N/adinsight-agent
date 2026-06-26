from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
import yaml

QUESTIONS_PATH = Path("agent/eval/text2sql_questions.yml")
MAX_RESULT_ROWS = 50

BLOCKED_SQL_TOKENS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "copy",
)


class Text2SqlError(ValueError):
    """Base exception for deterministic Text2SQL registry failures."""


class Text2SqlNoMatchError(Text2SqlError):
    def __init__(self, supported_question_examples: list[str]) -> None:
        self.supported_question_examples = supported_question_examples
        super().__init__("No deterministic Text2SQL v1 match found for this question.")


class Text2SqlUnsafeSqlError(Text2SqlError):
    pass


@dataclass(frozen=True)
class Text2SqlQuestion:
    id: str
    language: str
    question: str
    expected_model: str
    expected_columns: list[str]
    expected_sql: str


@dataclass(frozen=True)
class Text2SqlResult:
    question_id: str
    matched_question: str
    expected_model: str
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    answer: str


def load_questions(path: Path = QUESTIONS_PATH) -> list[Text2SqlQuestion]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        Text2SqlQuestion(
            id=str(question["id"]),
            language=str(question["language"]),
            question=str(question["question"]),
            expected_model=str(question["expected_model"]),
            expected_columns=list(question["expected_columns"]),
            expected_sql=str(question["expected_sql"]).strip(),
        )
        for question in data["questions"]
    ]


def find_question(user_question: str, questions: list[Text2SqlQuestion]) -> Text2SqlQuestion:
    normalized_user_question = normalize_question(user_question)

    for question in questions:
        if normalized_user_question == normalize_question(question.question):
            return question

    for question in questions:
        if normalized_user_question == normalize_question(question.id):
            return question

    supported_questions = [question.question for question in questions[:5]]
    raise Text2SqlNoMatchError(supported_questions)


def execute_question(
    user_question: str,
    conn: psycopg.Connection,
    questions_path: Path = QUESTIONS_PATH,
) -> Text2SqlResult:
    question = find_question(user_question, load_questions(questions_path))
    sql = validate_select_sql(question.expected_sql)

    with conn.cursor() as cur:
        cur.execute(sql)
        records = cur.fetchmany(MAX_RESULT_ROWS)
        columns = [column.name for column in cur.description or []]

    rows = [
        {
            column_name: serialize_value(value)
            for column_name, value in zip(columns, record, strict=True)
        }
        for record in records
    ]

    return Text2SqlResult(
        question_id=question.id,
        matched_question=question.question,
        expected_model=question.expected_model,
        sql=sql,
        rows=rows,
        row_count=len(rows),
        answer=build_answer(question, rows),
    )


def validate_select_sql(sql: str) -> str:
    stripped_sql = sql.strip().rstrip(";")
    lowered_sql = stripped_sql.lower()

    if not lowered_sql.startswith("select"):
        raise Text2SqlUnsafeSqlError("Only SELECT SQL is allowed.")

    token_pattern = r"\b(" + "|".join(re.escape(token) for token in BLOCKED_SQL_TOKENS) + r")\b"
    if re.search(token_pattern, lowered_sql):
        raise Text2SqlUnsafeSqlError("SQL contains a blocked token.")

    return stripped_sql


def build_answer(question: Text2SqlQuestion, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"{question.id} returned 0 rows from {question.expected_model}."

    preview = rows[0]
    preview_items = ", ".join(
        f"{column}={value}"
        for column, value in list(preview.items())[:3]
    )
    return (
        f"{question.id} returned {len(rows)} rows from {question.expected_model}. "
        f"Top row: {preview_items}."
    )


def normalize_question(value: str) -> str:
    return " ".join(value.strip().lower().split())


def serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
