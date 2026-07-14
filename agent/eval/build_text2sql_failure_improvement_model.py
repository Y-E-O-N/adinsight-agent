from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_INPUT_DIR = Path("/private/tmp/adinsight-text2sql-cases")
DEFAULT_OUTPUT_PATH = Path("docs/analysis/stage6_text2sql_failure_improvement_model.md")

MODEL_ARTIFACTS = (
    ("OpenAI gpt-5.4-mini-2026-03-17", "openai_positive.json", "openai_negative.json"),
    ("Gemini gemini-3.1-flash-lite", "gemini_positive.json", "gemini_negative.json"),
    ("Ollama qwen2.5-coder:7b", "qwen25_7b_positive.json", "qwen25_7b_negative.json"),
    ("Ollama phi4:14b", "phi4_14b_positive.json", "phi4_14b_negative.json"),
)


@dataclass(frozen=True)
class FailureEvidence:
    model: str
    question_id: str
    source: str
    status: str
    failure_type: str
    question: str
    recommendation: str


def main() -> None:
    input_dir = Path(os.getenv("TEXT2SQL_FAILURE_MODEL_INPUT_DIR", str(DEFAULT_INPUT_DIR)))
    output_path = Path(os.getenv("TEXT2SQL_FAILURE_MODEL_OUTPUT_PATH", str(DEFAULT_OUTPUT_PATH)))
    evidence = collect_failure_evidence(input_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(evidence), encoding="utf-8")
    print(output_path)


def collect_failure_evidence(input_dir: Path) -> list[FailureEvidence]:
    evidence: list[FailureEvidence] = []
    for model, positive_name, negative_name in MODEL_ARTIFACTS:
        positive_payload = load_json_if_exists(input_dir / positive_name)
        strict_payload = load_json_if_exists(input_dir / strict_name(positive_name))
        negative_payload = load_json_if_exists(input_dir / negative_name)

        if positive_payload:
            evidence.extend(lightweight_positive_failures(model, positive_payload))
        if strict_payload:
            evidence.extend(strict_positive_failures(model, strict_payload))
        if negative_payload:
            evidence.extend(negative_failures(model, negative_payload))
    return evidence


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def strict_name(positive_name: str) -> str:
    return positive_name.replace("_positive.json", "_strict_positive.json")


def lightweight_positive_failures(
    model: str,
    payload: dict[str, Any],
) -> list[FailureEvidence]:
    failures = []
    for case in payload.get("cases", []):
        status = str(case.get("status"))
        if status == "PASS":
            continue
        failure_type = classify_lightweight_failure(case)
        failures.append(
            FailureEvidence(
                model=model,
                question_id=str(case.get("question_id")),
                source="lightweight",
                status=status,
                failure_type=failure_type,
                question=str(case.get("question")),
                recommendation=recommendation_for_failure(failure_type, case),
            )
        )
    return failures


def strict_positive_failures(
    model: str,
    payload: dict[str, Any],
) -> list[FailureEvidence]:
    failures = []
    for case in payload.get("cases", []):
        strict_eval = case.get("strict_eval", {})
        status = str(strict_eval.get("strict_status"))
        if status == "PASS":
            continue
        failure_type = str(strict_eval.get("failure_type") or "unknown")
        failures.append(
            FailureEvidence(
                model=model,
                question_id=str(case.get("question_id")),
                source="strict",
                status=status,
                failure_type=failure_type,
                question=str(case.get("question")),
                recommendation=recommendation_for_failure(failure_type, case),
            )
        )
    return failures


def negative_failures(
    model: str,
    payload: dict[str, Any],
) -> list[FailureEvidence]:
    failures = []
    for case in payload.get("cases", []):
        status = str(case.get("status"))
        if status.startswith("PASS_"):
            continue
        failure_type = classify_negative_failure(case)
        failures.append(
            FailureEvidence(
                model=model,
                question_id=str(case.get("question_id")),
                source="negative",
                status=status,
                failure_type=failure_type,
                question=str(case.get("question")),
                recommendation=recommendation_for_failure(failure_type, case),
            )
        )
    return failures


def classify_lightweight_failure(case: dict[str, Any]) -> str:
    status = str(case.get("status"))
    reason = str(case.get("reason", "")).lower()
    generated_sql = str(case.get("generated_sql", "")).lower()
    actual_rows = case.get("actual_rows")
    expected_rows = case.get("expected_rows")
    if status == "REFUSED":
        return "answerable_refused"
    if status == "BLOCKED":
        return "limit_policy" if "limit" in reason else "validator_blocked"
    if "provider error" in reason:
        return "provider_error"
    if "undefinedcolumn" in reason or "does not exist" in reason:
        return "schema_context_columns"
    if actual_rows != expected_rows:
        return "limit_policy" if "limit" in generated_sql else "row_count_mismatch"
    if " join " not in generated_sql and any(
        str(feature).startswith("join_")
        for feature in case.get("required_sql_features", [])
    ):
        return "join_pattern"
    return "semantic_ordering"


def classify_negative_failure(case: dict[str, Any]) -> str:
    status = str(case.get("status"))
    if status == "FAIL_UNSAFE_ECHO":
        return "unsafe_echo"
    if status == "FAIL_EXECUTED":
        return "negative_executed"
    if status == "FAIL_PROVIDER_ERROR":
        return "provider_error"
    return "negative_failure"


def recommendation_for_failure(
    failure_type: str,
    case: dict[str, Any],
) -> str:
    question_id = str(case.get("question_id", ""))
    if failure_type in {"limit_policy", "row_count_mismatch"}:
        return "Tighten LIMIT policy and preserve explicit Top N or expected broad-list limit."
    if failure_type in {"schema_context_columns", "missing_expected_columns"}:
        return "Fix schema context columns and add expected output-column examples."
    if failure_type in {"join_pattern", "missing_join"}:
        return "Add canonical join examples for prediction monitor and campaign ROI tier questions."
    if failure_type in {"semantic_ordering", "result_set_mismatch"}:
        return "Add ordering and top-row priority examples for this question family."
    if failure_type in {"missing_required_sql_feature", "validator_blocked"}:
        return "Add required SQL feature examples and validator-aligned constraints."
    if failure_type == "answerable_refused":
        return "Clarify answerability in schema context; this question is in-domain."
    if failure_type in {"negative_executed", "unsafe_echo"}:
        return "Strengthen refusal policy for ambiguous or unsafe questions without echoing terms."
    if question_id in {"p5_q007", "p5_q012"}:
        return "Add objective to prediction monitor schema context and few-shot examples."
    return "Inspect generated SQL and add the smallest schema or prompt example that covers it."


def render_report(evidence: list[FailureEvidence]) -> str:
    grouped: dict[str, list[FailureEvidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.recommendation].append(item)

    ranked_groups = sorted(
        grouped.items(),
        key=lambda item: (
            -len({e.question_id for e in item[1]}),
            -len({e.model for e in item[1]}),
            item[0],
        ),
    )

    lines = [
        "# Stage 6 Text2SQL Failure Improvement Model",
        "",
        "작성일: 2026-07-09",
        "",
        "이 문서는 lightweight eval failure와 strict eval failure를 함께 보고,",
        "가장 많은 실패를 줄일 가능성이 큰 schema/prompt/validator 개선 액션을 우선순위화한다.",
        "",
        "## Improvement Actions",
        "",
        "| Priority | Affected cases | Affected models | Recommendation |",
        "|---:|---:|---:|---|",
    ]
    for index, (recommendation, items) in enumerate(ranked_groups, start=1):
        lines.append(
            "| "
            f"{index} | "
            f"{len({item.question_id for item in items})} | "
            f"{len({item.model for item in items})} | "
            f"{recommendation} |"
        )

    lines.extend(["", "## Evidence By Action", ""])
    for index, (recommendation, items) in enumerate(ranked_groups, start=1):
        lines.extend(
            [
                f"### {index}. {recommendation}",
                "",
                "| Model | Source | Case | Status | Failure type | Question |",
                "|---|---|---|---|---|---|",
            ]
        )
        for item in sorted(items, key=lambda evidence: (evidence.model, evidence.question_id)):
            lines.append(
                "| "
                f"{item.model} | "
                f"{item.source} | "
                f"`{item.question_id}` | "
                f"`{item.status}` | "
                f"`{item.failure_type}` | "
                f"{escape_table_cell(item.question)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## How To Use",
            "",
            "1. Fix the highest-priority schema/prompt action.",
            "2. Re-run lightweight eval and strict eval on the same generated SQL artifact.",
            "3. Compare whether affected cases moved from FAIL/BLOCKED/REFUSED to PASS.",
            "4. Only then compare models again.",
            "",
            "## Known Limitations",
            "",
            "- This model is a deterministic failure-to-action mapping, not a learned ML model.",
            "- It prioritizes high-coverage fixes; it does not prove that each fix will make every listed case pass.",
            "- It depends on strict eval artifacts being present in the same input directory.",
        ]
    )
    return "\n".join(lines) + "\n"


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
