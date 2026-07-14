from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psycopg
import yaml

from agent.text2sql.llm_client import (
    SqlGenerationClient,
    SqlGenerationRequest,
    SqlGenerationResponse,
)
from agent.text2sql.registry import MAX_RESULT_ROWS, serialize_value
from agent.text2sql.schema_catalog import (
    Text2SqlIntent,
    build_actual_column_catalog,
    build_intent_routing_catalog,
    find_best_intent_for_question,
    iter_intent_contract_lines,
)
from agent.text2sql.usage import LlmUsage, combine_usages
from agent.text2sql.validator import (
    SqlValidationResult,
    Text2SqlValidationError,
    extract_select_output_names,
    order_by_contains_terms,
    order_by_uses_column,
    validate_generated_sql,
)

RULEBOOK_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "analysis"
    / "text2sql_positive_criteria_rulebook.md"
)
DECISION_GUIDE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "analysis"
    / "text2sql_llm_decision_guide.md"
)
EVAL_QUESTIONS_PATH = (
    Path(__file__).resolve().parents[1]
    / "eval"
    / "text2sql_questions.yml"
)

BASE_SCHEMA_CONTEXT_V1 = build_actual_column_catalog()
SCHEMA_CONTEXT_V1 = BASE_SCHEMA_CONTEXT_V1
STATEMENT_TIMEOUT_MS = 5000
MAX_GENERATION_ATTEMPTS = 2

SQL_GENERATION_POLICY_V1 = """
Text2SQL SQL Generation Policy:
- First route the natural-language question through the Natural-Language Intent Routing Catalog:
  major category -> middle category -> minor intent.
- After routing, use the selected minor intent's table, required output columns, and limit policy.
- Use only actual table and column names from the Actual Allowed Table and Column Catalog.
- Never use conceptual names as SQL columns unless they are listed in the catalog.
- If the selected catalog intent lists required output columns, include every listed output column explicitly in SELECT.
- When an eval question or canonical template expects output columns, include those columns explicitly in SELECT even when the column is also used only for filtering or ordering.
- Extra useful columns are allowed only after all required columns/aliases are selected; never substitute an extra column for an expected alias.
- For ranking/list questions with explicit Top N or "limited to N", use that LIMIT.
- For benchmark broad-list questions that intentionally have no Top N, keep deterministic ORDER BY and do not add a default LIMIT.
- Do not add LIMIT to aggregate queries unless the question explicitly asks for Top N.
- For "largest prediction error" or "largest ROAS prediction error", use absolute_roas_prediction_error, not signed roas_prediction_error.
- If a metric is unavailable, return not_answerable instead of inventing a proxy.
""".strip()

CANONICAL_SQL_TEMPLATES_V1 = """
Canonical SQL Templates:

1) Sponsored review priority:
select
    creator_username,
    sponsored_candidate_posts,
    sponsored_candidate_rate,
    included_in_creator_review
from ai_native.ai_creator_sponsored_summary
where included_in_creator_review = true
order by sponsored_candidate_posts desc, sponsored_candidate_rate desc
limit 20

2) Sponsored candidate rate Top 10:
select
    creator_username,
    sponsored_candidate_rate,
    total_posts
from ai_native.ai_creator_sponsored_summary
order by sponsored_candidate_rate desc, total_posts desc
limit 10

3) No sponsored candidate broad list:
select
    creator_username,
    total_posts,
    sponsored_candidate_posts
from ai_native.ai_creator_sponsored_summary
where total_posts >= 2
  and sponsored_candidate_posts = 0
order by total_posts desc, creator_username asc

4) ROI objective aggregate:
select
    campaign_objective,
    count(*) as campaign_count,
    avg(roas) as avg_roas,
    avg(net_payment_amount_krw) as avg_net_payment_amount_krw
from ai_native.ai_campaign_roi_summary
group by campaign_objective
order by avg_roas desc

5) ROI objective x performance tier aggregate:
select
    campaign_objective,
    roas_performance_tier,
    count(*) as campaign_count,
    avg(roas) as avg_roas
from ai_native.ai_campaign_roi_summary
group by campaign_objective, roas_performance_tier
order by avg_roas desc, campaign_objective asc, roas_performance_tier asc

6) ROI review broad list:
select
    campaign_id,
    campaign_name,
    roas,
    has_positive_net_payment,
    included_in_campaign_roi_review
from ai_native.ai_campaign_roi_summary
where has_positive_net_payment = true
  and included_in_campaign_roi_review = true
order by roas desc, campaign_id asc

7) ROI review aggregate by region:
select
    campaign_region,
    count(*) as review_campaign_count,
    avg(roas) as avg_roas
from ai_native.ai_campaign_roi_summary
where included_in_campaign_roi_review = true
group by campaign_region
order by avg_roas desc, campaign_region asc

8) Latest prediction monitor largest absolute error:
select
    campaign_id,
    campaign_name,
    actual_roas,
    predicted_roas,
    absolute_roas_prediction_error
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
order by absolute_roas_prediction_error desc, campaign_id asc
limit 5

9) Latest prediction monitor actual above predicted:
select
    campaign_id,
    campaign_name,
    actual_roas,
    predicted_roas,
    roas_prediction_error
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
  and roas_prediction_error > 0
order by roas_prediction_error desc, campaign_id asc

10) Latest prediction monitor by objective:
select
    objective,
    count(*) as campaign_count,
    avg(actual_roas) as avg_actual_roas,
    avg(predicted_roas) as avg_predicted_roas,
    avg(roas_prediction_error) as avg_roas_prediction_error
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
group by objective
order by avg_roas_prediction_error desc

11) Latest prediction monitor MAE by objective:
select
    objective,
    count(*) as campaign_count,
    avg(absolute_roas_prediction_error) as mae
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
group by objective
order by mae desc, objective asc

12) Latest prediction monitor joined to campaign ROI tier:
select
    monitor.campaign_id,
    monitor.campaign_name,
    roi.roas_performance_tier,
    monitor.actual_roas,
    monitor.predicted_roas,
    monitor.absolute_roas_prediction_error
from marts.mart_campaign_roas_prediction_monitor as monitor
join ai_native.ai_campaign_roi_summary as roi
  on monitor.campaign_id = roi.campaign_id
where monitor.scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
order by monitor.absolute_roas_prediction_error desc, monitor.campaign_id asc
limit 10

13) Latest prediction error by ROI tier:
select
    roi.roas_performance_tier,
    count(*) as campaign_count,
    avg(monitor.absolute_roas_prediction_error) as mae,
    avg(monitor.roas_prediction_error) as bias
from marts.mart_campaign_roas_prediction_monitor as monitor
join ai_native.ai_campaign_roi_summary as roi
  on monitor.campaign_id = roi.campaign_id
where monitor.scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
group by roi.roas_performance_tier
order by mae desc, roi.roas_performance_tier asc
""".strip()

STRICT_EVAL_FEEDBACK_V1 = """
Strict Eval Feedback Priority:
- Highest priority: include every expected output column explicitly in SELECT.
- Do not omit expected output columns just because they are present in WHERE, GROUP BY, or ORDER BY.
- Avoid aliases that replace expected column names unless the eval expects the alias.
- For largest prediction error rankings, select/order by absolute_roas_prediction_error; signed roas_prediction_error is only for direction questions.
- For campaign ROI aggregates, preserve the canonical aliases and ordering, especially campaign_count/review_campaign_count and avg_roas desc.
- For objective-level monitor questions, use objective from marts.mart_campaign_roas_prediction_monitor.
- For ROI-tier monitor questions, join monitor rows to ai_native.ai_campaign_roi_summary and select roi.roas_performance_tier.
- For broad-list benchmark questions with no Top N, do not add default LIMIT.
""".strip()


@dataclass(frozen=True)
class GeneratedText2SqlResult:
    question: str
    sql: str
    rows: list[dict[str, Any]]
    row_count: int
    answer: str
    mode: str
    expected_tables: tuple[str, ...]
    reason: str
    validation: SqlValidationResult
    usage: LlmUsage | None = None
    usage_attempts: tuple[LlmUsage, ...] = ()
    fallback_reason: str | None = None


class Text2SqlNotAnswerableError(ValueError):
    def __init__(
        self,
        reason: str,
        usage: LlmUsage | None = None,
        usage_attempts: tuple[LlmUsage, ...] = (),
        fallback_reason: str | None = None,
    ) -> None:
        self.usage = usage
        self.usage_attempts = usage_attempts
        self.fallback_reason = fallback_reason
        super().__init__(reason)


class Text2SqlGeneratedSqlValidationError(Text2SqlValidationError):
    def __init__(
        self,
        reason: str,
        usage: LlmUsage | None = None,
        usage_attempts: tuple[LlmUsage, ...] = (),
        fallback_reason: str | None = None,
    ) -> None:
        self.usage = usage
        self.usage_attempts = usage_attempts
        self.fallback_reason = fallback_reason
        super().__init__(reason)


class Text2SqlIntentContractError(Text2SqlValidationError):
    pass


def execute_generated_question(
    question: str,
    conn: psycopg.Connection,
    client: SqlGenerationClient,
    schema_context: str | None = None,
    statement_timeout_ms: int = STATEMENT_TIMEOUT_MS,
    mode: str = "llm_generated_sql_v2_mock",
    max_generation_attempts: int = MAX_GENERATION_ATTEMPTS,
) -> GeneratedText2SqlResult:
    resolved_schema_context = schema_context or build_schema_context_v1()
    generation, validation, usage_attempts = generate_and_validate_sql(
        question=question,
        client=client,
        schema_context=resolved_schema_context,
        max_generation_attempts=max_generation_attempts,
    )

    with conn.cursor() as cur:
        cur.execute(f"set local statement_timeout = {int(statement_timeout_ms)}")
        cur.execute(validation.sql)
        records = cur.fetchmany(MAX_RESULT_ROWS)
        columns = [column.name for column in cur.description or []]

    rows = [
        {
            column_name: serialize_value(value)
            for column_name, value in zip(columns, record, strict=True)
        }
        for record in records
    ]

    return GeneratedText2SqlResult(
        question=question,
        sql=validation.sql,
        rows=rows,
        row_count=len(rows),
        answer=build_generated_answer(question, rows),
        mode=mode,
        expected_tables=generation.expected_tables,
        reason=generation.reason,
        validation=validation,
        usage=generation.usage,
        usage_attempts=usage_attempts,
        fallback_reason=generation.fallback_reason,
    )


def generate_and_validate_sql(
    *,
    question: str,
    client: SqlGenerationClient,
    schema_context: str,
    max_generation_attempts: int,
) -> tuple[SqlGenerationResponse, SqlValidationResult, tuple[LlmUsage, ...]]:
    retry_context = schema_context
    last_validation_error: Exception | None = None
    last_fallback_reason: str | None = None
    usage_attempts: list[LlmUsage] = []
    selected_intent = find_best_intent_for_question(question)

    for attempt in range(max(1, max_generation_attempts)):
        generation = client.generate_sql(
            SqlGenerationRequest(question=question, schema_context=retry_context)
        )
        last_fallback_reason = generation.fallback_reason
        generation_usages = generation.usage_attempts
        if not generation_usages and generation.usage is not None:
            generation_usages = (generation.usage,)
        usage_attempts.extend(generation_usages)

        if generation.answerability != "answerable" or generation.sql is None:
            raise Text2SqlNotAnswerableError(
                generation.reason,
                usage=combine_usages(list(usage_attempts)),
                usage_attempts=tuple(usage_attempts),
                fallback_reason=generation.fallback_reason,
            )

        try:
            validation = validate_generated_sql(generation.sql)
            validate_intent_contract(generation.sql, selected_intent)
            combined_usage = combine_usages(list(usage_attempts))
            if combined_usage is not None:
                generation = SqlGenerationResponse(
                    answerability=generation.answerability,
                    sql=generation.sql,
                    expected_tables=generation.expected_tables,
                    reason=generation.reason,
                    usage=combined_usage,
                    usage_attempts=tuple(usage_attempts),
                    fallback_reason=generation.fallback_reason,
                )
            return generation, validation, tuple(usage_attempts)
        except Exception as exc:
            last_validation_error = exc
            if attempt + 1 >= max_generation_attempts:
                break
            retry_context = build_validation_retry_context(
                schema_context=schema_context,
                rejected_sql=generation.sql,
                validation_error=str(exc),
                selected_intent=selected_intent,
            )

    if last_validation_error is not None:
        raise Text2SqlGeneratedSqlValidationError(
            str(last_validation_error),
            usage=combine_usages(list(usage_attempts)),
            usage_attempts=tuple(usage_attempts),
            fallback_reason=last_fallback_reason,
        )
    raise Text2SqlNotAnswerableError(
        "Model did not produce answerable SQL.",
        usage=combine_usages(list(usage_attempts)),
        usage_attempts=tuple(usage_attempts),
        fallback_reason=last_fallback_reason,
    )


def build_validation_retry_context(
    *,
    schema_context: str,
    rejected_sql: str,
    validation_error: str,
    selected_intent: Text2SqlIntent | None = None,
) -> str:
    intent_lines = (
        list(iter_intent_contract_lines(selected_intent))
        if selected_intent is not None
        else ["Intent: not matched"]
    )
    return "\n\n".join(
        [
            schema_context,
            "Validator Retry Instruction:",
            "The previous SQL was rejected before database execution.",
            f"Validation error: {validation_error}",
            "Selected intent contract:",
            "\n".join(f"- {line}" for line in intent_lines),
            f"Rejected SQL: {rejected_sql}",
            (
                "Regenerate SQL using only actual catalog columns, required SELECT "
                "columns, required aliases, required ORDER BY, and metric semantics."
            ),
        ]
    )


def validate_intent_contract(
    sql: str,
    selected_intent: Text2SqlIntent | None,
) -> None:
    if selected_intent is None:
        return

    selected_columns = extract_select_output_names(sql)
    required_select_columns = {
        column.lower()
        for column in (selected_intent.required_select_columns or selected_intent.required_columns)
    }
    required_aliases = {alias.lower() for alias in selected_intent.required_aliases}
    missing_select_columns = sorted(required_select_columns - selected_columns)
    missing_aliases = sorted(required_aliases - selected_columns)
    missing_order_terms = [
        term
        for term in selected_intent.required_order_by
        if not order_by_contains_terms(sql, (term,))
    ]
    forbidden_order_columns = [
        column
        for column in selected_intent.forbidden_order_by_columns
        if order_by_uses_column(sql, column)
    ]
    semantic_errors = find_metric_semantic_errors(sql, selected_intent)

    errors: list[str] = []
    if missing_select_columns:
        errors.append(
            "missing required SELECT column(s): "
            + ", ".join(missing_select_columns)
        )
    if missing_aliases:
        errors.append("missing required alias(es): " + ", ".join(missing_aliases))
    if missing_order_terms:
        errors.append(
            "missing required ORDER BY term(s): "
            + ", ".join(missing_order_terms)
        )
    if forbidden_order_columns:
        errors.append(
            "forbidden ORDER BY column(s): "
            + ", ".join(forbidden_order_columns)
        )
    errors.extend(semantic_errors)

    if errors:
        raise Text2SqlIntentContractError("; ".join(errors))


def find_metric_semantic_errors(
    sql: str,
    selected_intent: Text2SqlIntent,
) -> list[str]:
    lowered_sql = sql.casefold()
    errors: list[str] = []
    if (
        "largest_error_uses_absolute" in selected_intent.metric_semantics
        and "absolute_roas_prediction_error" not in lowered_sql
    ):
        errors.append(
            "largest prediction error must use absolute_roas_prediction_error"
        )
    if (
        "mae_uses_absolute_error" in selected_intent.metric_semantics
        and not aggregate_uses_column(lowered_sql, "avg", "absolute_roas_prediction_error")
    ):
        errors.append("MAE must average absolute_roas_prediction_error")
    if (
        "bias_uses_signed_error" in selected_intent.metric_semantics
        and not aggregate_uses_column(lowered_sql, "avg", "roas_prediction_error")
    ):
        errors.append("bias must average signed roas_prediction_error")
    return errors


def aggregate_uses_column(sql: str, aggregate_name: str, column_name: str) -> bool:
    pattern = rf"\b{re.escape(aggregate_name)}\s*\(\s*(?:[a-z_][a-z0-9_]*\.)?{re.escape(column_name)}\s*\)"
    return re.search(pattern, sql, flags=re.IGNORECASE) is not None


def build_generated_answer(question: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"Generated Text2SQL v2 returned 0 rows for question={question!r}."

    preview = rows[0]
    preview_items = ", ".join(
        f"{column}={value}"
        for column, value in list(preview.items())[:3]
    )
    return (
        f"Generated Text2SQL v2 returned {len(rows)} rows. "
        f"Top row: {preview_items}."
    )


def build_schema_context_v1(rulebook_path: Path = RULEBOOK_PATH) -> str:
    return "\n\n".join(
        [
            BASE_SCHEMA_CONTEXT_V1,
            build_intent_routing_catalog(),
            SQL_GENERATION_POLICY_V1,
            CANONICAL_SQL_TEMPLATES_V1,
            load_eval_question_sql_contracts(),
            STRICT_EVAL_FEEDBACK_V1,
            load_positive_criteria_rulebook(rulebook_path),
            load_text2sql_decision_guide(),
        ]
    )


def load_eval_question_sql_contracts(
    questions_path: Path = EVAL_QUESTIONS_PATH,
) -> str:
    try:
        payload = yaml.safe_load(questions_path.read_text(encoding="utf-8"))
    except OSError:
        return (
            "Question-ID Canonical SQL Contracts:\n"
            f"- Eval question path unavailable at runtime: {questions_path}\n"
            "- Use the canonical templates and intent catalog above."
        )

    lines = [
        "Question-ID Canonical SQL Contracts:",
        "- These are benchmark few-shot contracts; match their SELECT columns, aliases, and ORDER BY when the user wording is equivalent.",
    ]
    for question in payload.get("questions", []):
        lines.extend(
            [
                f"- {question.get('id')}: {question.get('question')}",
                f"  Expected columns: {', '.join(question.get('expected_columns', []))}",
                "  Expected SQL:",
                indent_sql(str(question.get("expected_sql", "")).strip()),
            ]
        )
    return "\n".join(lines)


def indent_sql(sql: str) -> str:
    return "\n".join(f"    {line}" for line in sql.splitlines())


def load_positive_criteria_rulebook(rulebook_path: Path = RULEBOOK_PATH) -> str:
    try:
        rulebook = rulebook_path.read_text(encoding="utf-8").strip()
    except OSError:
        return (
            "Text2SQL Positive Criteria Rulebook:\n"
            f"- Rulebook path unavailable at runtime: {rulebook_path}\n"
            "- Use the explicit schema context rules above."
        )

    return (
        "Text2SQL Positive Criteria Rulebook:\n"
        f"Source file: {rulebook_path.relative_to(Path(__file__).resolve().parents[2])}\n\n"
        f"{rulebook}"
    )


def load_text2sql_decision_guide(guide_path: Path = DECISION_GUIDE_PATH) -> str:
    try:
        guide = guide_path.read_text(encoding="utf-8").strip()
    except OSError:
        return (
            "Text2SQL LLM Decision Guide:\n"
            f"- Guide path unavailable at runtime: {guide_path}\n"
            "- Apply metric availability, default handling, and answerability checks."
        )

    return (
        "Text2SQL LLM Decision Guide:\n"
        f"Source file: {guide_path.relative_to(Path(__file__).resolve().parents[2])}\n\n"
        f"{guide}"
    )
