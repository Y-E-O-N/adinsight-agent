from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import psycopg
import yaml

from agent.eval.run_expected_sql import QUESTIONS_PATH
from agent.eval.text2sql_model_scoring import score_text2sql_model
from agent.text2sql.generator import Text2SqlNotAnswerableError, execute_generated_question
from agent.text2sql.llm_client import SqlGenerationClient
from agent.text2sql.provider import Text2SqlProviderConfigError, get_sql_generation_provider
from agent.text2sql.registry import serialize_value
from agent.text2sql.usage import LlmUsage, summarize_usages
from agent.text2sql.validator import Text2SqlValidationError

METRICS_PATH = Path("metrics/run_results.jsonl")


@dataclass(frozen=True)
class V2EvalCaseResult:
    question_id: str
    language: str
    status: str
    expected_rows: int
    actual_rows: int | None
    latency_ms: float
    generated_sql: str | None
    reason: str
    usage: LlmUsage | None = None
    usage_attempts: tuple[LlmUsage, ...] = ()


def main() -> None:
    results = run_eval()
    summary = summarize_results(results)

    for result in results:
        print(
            result.question_id,
            result.status,
            f"expected_rows={result.expected_rows}",
            f"actual_rows={result.actual_rows}",
            f"latency_ms={result.latency_ms}",
            f"input_tokens={result.usage.input_tokens if result.usage else None}",
            f"output_tokens={result.usage.output_tokens if result.usage else None}",
            f"cost_usd={result.usage.estimated_cost_usd if result.usage else None}",
        )

    print(
        "summary",
        f"passed={summary['passed']}",
        f"failed={summary['failed']}",
        f"refused={summary['refused']}",
        f"blocked={summary['blocked']}",
        f"total={summary['total']}",
        f"exec_acc={summary['exec_acc']}",
        f"refuse_rate={summary['refuse_rate']}",
        f"model_score={summary['model_score']['composite_score']}",
        f"tier={summary['model_score']['tier']}",
        f"input_tokens={summary['usage']['input_tokens']}",
        f"output_tokens={summary['usage']['output_tokens']}",
        f"estimated_cost_usd={summary['usage']['estimated_cost_usd']}",
    )

    append_metrics(summary)
    write_case_artifact_if_configured(results, summary)

    if summary["failed"] > 0 or summary["blocked"] > 0:
        raise SystemExit(1)


def run_eval() -> list[V2EvalCaseResult]:
    questions = load_questions()
    provider = get_sql_generation_provider()

    with get_connection() as conn:
        return [
            evaluate_question(question, conn, provider.client, provider.mode)
            for question in questions
        ]


def evaluate_question(
    question: dict[str, Any],
    conn: psycopg.Connection,
    client: SqlGenerationClient,
    mode: str,
) -> V2EvalCaseResult:
    started_at = perf_counter()
    question_id = str(question["id"])
    expected_rows = int(question["current_result_rows"])

    try:
        generated = execute_generated_question(str(question["question"]), conn, client, mode=mode)
    except Text2SqlProviderConfigError as exc:
        return V2EvalCaseResult(
            question_id=question_id,
            language=str(question["language"]),
            status="FAIL",
            expected_rows=expected_rows,
            actual_rows=None,
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            generated_sql=None,
            reason=f"Provider error: {exc}",
        )
    except Text2SqlNotAnswerableError as exc:
        return V2EvalCaseResult(
            question_id=question_id,
            language=str(question["language"]),
            status="REFUSED",
            expected_rows=expected_rows,
            actual_rows=None,
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            generated_sql=None,
            reason=str(exc),
            usage=getattr(exc, "usage", None),
            usage_attempts=getattr(exc, "usage_attempts", ()),
        )
    except Text2SqlValidationError as exc:
        return V2EvalCaseResult(
            question_id=question_id,
            language=str(question["language"]),
            status="BLOCKED",
            expected_rows=expected_rows,
            actual_rows=None,
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            generated_sql=None,
            reason=str(exc),
            usage=getattr(exc, "usage", None),
            usage_attempts=getattr(exc, "usage_attempts", ()),
        )
    except psycopg.Error as exc:
        conn.rollback()
        return V2EvalCaseResult(
            question_id=question_id,
            language=str(question["language"]),
            status="FAIL",
            expected_rows=expected_rows,
            actual_rows=None,
            latency_ms=round((perf_counter() - started_at) * 1000, 3),
            generated_sql=None,
            reason=f"Database execution error: {exc.__class__.__name__}: {exc}",
        )

    try:
        status = "PASS" if rows_match_expected(question, conn, generated.sql) else "FAIL"
    except psycopg.Error as exc:
        conn.rollback()
        status = "FAIL"
        reason = f"Database comparison error: {exc.__class__.__name__}: {exc}"
    else:
        reason = generated.reason

    return V2EvalCaseResult(
        question_id=question_id,
        language=str(question["language"]),
        status=status,
        expected_rows=expected_rows,
        actual_rows=generated.row_count,
        latency_ms=round((perf_counter() - started_at) * 1000, 3),
        generated_sql=generated.sql,
        reason=reason,
        usage=generated.usage,
        usage_attempts=generated.usage_attempts,
    )


def rows_match_expected(
    question: dict[str, Any],
    conn: psycopg.Connection,
    generated_sql: str,
) -> bool:
    expected_rows = fetch_rows(conn, str(question["expected_sql"]))
    generated_rows = fetch_rows(conn, generated_sql)

    if len(expected_rows) != len(generated_rows):
        return False

    if not expected_rows and not generated_rows:
        return True

    expected_columns = list(question["expected_columns"])
    comparable_columns = [
        column_name
        for column_name in expected_columns
        if column_name in expected_rows[0] and column_name in generated_rows[0]
    ]

    if not comparable_columns:
        return False

    return all(
        expected_rows[0][column_name] == generated_rows[0][column_name]
        for column_name in comparable_columns[:3]
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


def summarize_results(results: list[V2EvalCaseResult]) -> dict[str, Any]:
    total = len(results)
    passed = count_status(results, "PASS")
    failed = count_status(results, "FAIL")
    refused = count_status(results, "REFUSED")
    blocked = count_status(results, "BLOCKED")
    answerable = passed + failed + blocked
    latencies = [result.latency_ms for result in results]
    usage_summary = summarize_usages(
        [
            usage
            for result in results
            for usage in (result.usage_attempts or ((result.usage,) if result.usage else ()))
        ]
    )

    summary = {
        "phase": "p5c",
        "step": "text2sql_v2_eval",
        "ts": datetime.now(UTC).isoformat(),
        "mode": resolve_eval_mode(),
        "provider": os.getenv("TEXT2SQL_PROVIDER", "mock").lower(),
        "gateway_backend": os.getenv("TEXT2SQL_GATEWAY_BACKEND"),
        "local_model": os.getenv("TEXT2SQL_EVAL_MODEL_LABEL") or os.getenv("TEXT2SQL_OLLAMA_MODEL"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "refused": refused,
        "blocked": blocked,
        "answerable": answerable,
        "exec_acc": round(passed / answerable, 4) if answerable else 0.0,
        "refuse_rate": round(refused / total, 4) if total else 0.0,
        "unsafe_block_rate": round(blocked / total, 4) if total else 0.0,
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "usage": usage_summary,
        "known_limitation": (
            "Model score is a portfolio evaluation rubric over the current expected-SQL "
            "questions; it is not a public benchmark score."
        ),
    }
    summary["model_score"] = score_text2sql_model(summary)
    return summary


def resolve_eval_mode() -> str:
    provider = os.getenv("TEXT2SQL_PROVIDER", "mock").lower()
    if provider == "http_json":
        return "llm_generated_sql_v2_http_json"

    return "llm_generated_sql_v2_mock"


def count_status(results: list[V2EvalCaseResult], status: str) -> int:
    return sum(1 for result in results if result.status == status)


def percentile(values: list[float], percentile_value: int) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * (percentile_value / 100))
    return round(sorted_values[index], 3)


def load_questions() -> list[dict[str, Any]]:
    data = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return list(data["questions"])


def append_metrics(summary: dict[str, Any]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("a", encoding="utf-8") as metrics_file:
        metrics_file.write(json.dumps(summary, ensure_ascii=False) + "\n")


def write_case_artifact_if_configured(
    results: list[V2EvalCaseResult],
    summary: dict[str, Any],
) -> None:
    artifact_path = os.getenv("TEXT2SQL_EVAL_CASES_PATH")
    if not artifact_path:
        return

    questions_by_id = {str(question["id"]): question for question in load_questions()}
    payload = {
        "summary": summary,
        "cases": [
            build_case_artifact(result, questions_by_id.get(result.question_id))
            for result in results
        ],
    }
    path = Path(artifact_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_case_artifact(
    result: V2EvalCaseResult,
    question: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "question_id": result.question_id,
        "language": result.language,
        "status": result.status,
        "expected_rows": result.expected_rows,
        "actual_rows": result.actual_rows,
        "latency_ms": result.latency_ms,
        "generated_sql": result.generated_sql,
        "reason": result.reason,
        "usage": result.usage.to_dict() if result.usage else None,
        "usage_attempts": [
            usage.to_dict()
            for usage in result.usage_attempts
        ],
    }
    if question is not None:
        payload.update(
            {
                "question": question.get("question"),
                "expected_model": question.get("expected_model"),
                "expected_columns": question.get("expected_columns", []),
                "required_sql_features": question.get("required_sql_features", []),
                "expected_sql": str(question.get("expected_sql", "")).strip(),
            }
        )
    return payload


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adinsight"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


if __name__ == "__main__":
    main()
