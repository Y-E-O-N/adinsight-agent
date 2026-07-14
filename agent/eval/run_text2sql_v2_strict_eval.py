from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
import yaml

from agent.eval.run_expected_sql import QUESTIONS_PATH
from agent.eval.run_text2sql_v2_eval import METRICS_PATH
from agent.eval.text2sql_model_scoring import score_text2sql_model
from agent.eval.text2sql_strict_eval import StrictEvalResult, compare_case_strict

DEFAULT_STRICT_OUTPUT_PATH = Path("metrics/text2sql_strict_eval_cases.json")


def main() -> None:
    input_path = resolve_input_path()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    payload = merge_latest_question_contracts(payload)
    results = run_strict_eval(payload)
    summary = summarize_strict_results(results, payload)

    for result in results:
        print(
            result.question_id,
            result.strict_status,
            f"original_status={result.original_status}",
            f"failure_type={result.failure_type}",
            f"expected_rows={result.expected_rows}",
            f"actual_rows={result.actual_rows}",
        )

    print(
        "summary",
        f"passed={summary['passed']}",
        f"failed={summary['failed']}",
        f"refused={summary['refused']}",
        f"blocked={summary['blocked']}",
        f"total={summary['total']}",
        f"strict_exec_acc={summary['exec_acc']}",
        f"new_failures_from_lightweight_pass={summary['new_failures_from_lightweight_pass']}",
    )

    append_metrics(summary)
    write_strict_artifact(results, summary, payload)

    if summary["failed"] > 0 or summary["blocked"] > 0:
        raise SystemExit(1)


def resolve_input_path() -> Path:
    raw_path = os.getenv("TEXT2SQL_STRICT_INPUT_CASES_PATH") or os.getenv(
        "TEXT2SQL_EVAL_CASES_PATH"
    )
    if not raw_path:
        raise SystemExit(
            "TEXT2SQL_STRICT_INPUT_CASES_PATH or TEXT2SQL_EVAL_CASES_PATH is required."
        )
    return Path(raw_path)


def merge_latest_question_contracts(payload: dict[str, Any]) -> dict[str, Any]:
    questions_by_id = load_latest_questions_by_id()
    merged_cases = []
    for case in payload.get("cases", []):
        question_id = str(case.get("question_id"))
        latest_question = questions_by_id.get(question_id)
        if latest_question is None:
            merged_cases.append(case)
            continue
        merged_cases.append(
            {
                **case,
                "question": latest_question.get("question", case.get("question")),
                "expected_model": latest_question.get(
                    "expected_model",
                    case.get("expected_model"),
                ),
                "expected_columns": latest_question.get(
                    "expected_columns",
                    case.get("expected_columns", []),
                ),
                "required_sql_features": latest_question.get(
                    "required_sql_features",
                    case.get("required_sql_features", []),
                ),
                "expected_sql": str(latest_question.get("expected_sql", "")).strip()
                or case.get("expected_sql"),
                "expected_contract_source": str(QUESTIONS_PATH),
            }
        )
    return {**payload, "cases": merged_cases}


def load_latest_questions_by_id() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return {
        str(question["id"]): question
        for question in data.get("questions", [])
    }


def run_strict_eval(payload: dict[str, Any]) -> list[StrictEvalResult]:
    cases = list(payload.get("cases", []))
    with get_connection() as conn:
        return [compare_case_strict(case, conn) for case in cases]


def summarize_strict_results(
    results: list[StrictEvalResult],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    total = len(results)
    passed = count_status(results, "PASS")
    failed = count_status(results, "FAIL")
    refused = count_status(results, "REFUSED")
    blocked = count_status(results, "BLOCKED")
    answerable = passed + failed + blocked
    source_summary = source_payload.get("summary", {})

    summary = {
        "phase": "p5c",
        "step": "text2sql_v2_strict_eval",
        "ts": datetime.now(UTC).isoformat(),
        "source_step": source_summary.get("step"),
        "source_lightweight_passed": source_summary.get("passed"),
        "source_lightweight_failed": source_summary.get("failed"),
        "source_lightweight_refused": source_summary.get("refused"),
        "source_lightweight_blocked": source_summary.get("blocked"),
        "mode": source_summary.get("mode"),
        "provider": source_summary.get("provider"),
        "gateway_backend": source_summary.get("gateway_backend"),
        "local_model": source_summary.get("local_model"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "refused": refused,
        "blocked": blocked,
        "answerable": answerable,
        "exec_acc": round(passed / answerable, 4) if answerable else 0.0,
        "refuse_rate": round(refused / total, 4) if total else 0.0,
        "unsafe_block_rate": round(blocked / total, 4) if total else 0.0,
        "new_failures_from_lightweight_pass": sum(
            1
            for result in results
            if result.original_status == "PASS" and result.strict_status != "PASS"
        ),
        "failure_types": count_failure_types(results),
        "p50_latency_ms": source_summary.get("p50_latency_ms", 0),
        "p95_latency_ms": source_summary.get("p95_latency_ms", 0),
        "known_limitation": (
            "Strict eval reuses saved generated SQL artifacts, merges the latest "
            "expected SQL contract from agent/eval/text2sql_questions.yml, and "
            "compares expected columns, full result rows, order sensitivity, numeric "
            "tolerance, and required SQL features. It does not re-call the model."
        ),
    }
    summary["model_score"] = score_text2sql_model(summary)
    return summary


def count_status(results: list[StrictEvalResult], status: str) -> int:
    return sum(1 for result in results if result.strict_status == status)


def count_failure_types(results: list[StrictEvalResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        if result.strict_status == "PASS":
            continue
        failure_type = result.failure_type or "unknown"
        counts[failure_type] = counts.get(failure_type, 0) + 1
    return dict(sorted(counts.items()))


def append_metrics(summary: dict[str, Any]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("a", encoding="utf-8") as metrics_file:
        metrics_file.write(json.dumps(summary, ensure_ascii=False) + "\n")


def write_strict_artifact(
    results: list[StrictEvalResult],
    summary: dict[str, Any],
    source_payload: dict[str, Any],
) -> None:
    output_path = Path(
        os.getenv("TEXT2SQL_STRICT_EVAL_CASES_PATH", str(DEFAULT_STRICT_OUTPUT_PATH))
    )
    cases_by_id = {
        str(case.get("question_id")): case for case in source_payload.get("cases", [])
    }
    payload = {
        "summary": summary,
        "cases": [
            {
                **cases_by_id.get(result.question_id, {}),
                "strict_eval": asdict(result),
            }
            for result in results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
