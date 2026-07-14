# Stage 6 Text2SQL Strict Eval Report

작성일: 2026-07-09

이 문서는 기존 lightweight Text2SQL eval과 새 strict eval을 비교한다.
strict eval은 모델을 다시 호출하지 않고, 이미 저장된 case artifact의 `generated_sql`을 DB에서 다시 실행해 재채점한다.
따라서 같은 모델 출력물에 대해 기존 평가와 엄밀 평가를 공정하게 비교할 수 있다.

## Why Strict Eval

기존 lightweight eval은 빠른 모델 비교에 유용하지만 다음 false positive를 놓칠 수 있다.

- 첫 row는 맞지만 전체 result set이 다른 경우
- expected column 일부가 빠졌는데 비교 가능한 일부 컬럼만 맞은 경우
- 정렬 우선순위가 다른데 row count만 같은 경우
- latest snapshot filter, join, aggregation alias 같은 SQL feature가 빠진 경우
- numeric 값이 거의 같지만 tolerance 기준이 명시되지 않은 경우

strict eval은 이런 항목을 더 강하게 검사한다.

## Strict Criteria

| Criterion | Strict behavior |
|---|---|
| Full row set | expected SQL과 generated SQL의 전체 row set을 비교한다. |
| Expected columns | `expected_columns` 전체가 generated result에 있어야 한다. |
| Order sensitivity | expected SQL에 `ORDER BY`, `LIMIT`, `order_by_*`, `limit_*` feature가 있으면 row order까지 비교한다. |
| Numeric tolerance | numeric 값은 기본 absolute tolerance `1e-6`으로 비교한다. |
| Required SQL features | latest snapshot filter, join, limit, group by, aggregate alias 등 주요 feature를 문자열 기반으로 검사한다. |
| Existing non-answer states | generated SQL이 없는 REFUSED/BLOCKED/provider error는 strict에서도 pass로 뒤집지 않는다. |

## Runner

```bash
set -a; source .env; set +a
POSTGRES_HOST=localhost \
TEXT2SQL_STRICT_INPUT_CASES_PATH=/private/tmp/adinsight-text2sql-cases/openai_positive.json \
TEXT2SQL_STRICT_EVAL_CASES_PATH=/private/tmp/adinsight-text2sql-cases/openai_strict_positive.json \
uv run python agent/eval/run_text2sql_v2_strict_eval.py
```

입력은 기존 lightweight artifact이고, 출력은 strict artifact다.

## Result Summary

| Model | Lightweight positive | Strict positive | New failures from lightweight PASS | Top strict failure types |
|---|---:|---:|---:|---|
| OpenAI `gpt-5.4-mini-2026-03-17` | 8 PASS / 12 FAIL / 2 REFUSED / 2 BLOCKED | 3 PASS / 17 FAIL / 2 REFUSED / 2 BLOCKED | 5 | result set mismatch 7, missing columns 6 |
| Gemini `gemini-3.1-flash-lite` | 10 PASS / 13 FAIL / 1 BLOCKED | 3 PASS / 20 FAIL / 1 BLOCKED | 7 | missing columns 11, missing SQL feature 4 |
| Ollama `qwen2.5-coder:7b` | 8 PASS / 16 FAIL | 1 PASS / 23 FAIL | 7 | missing columns 11, missing SQL feature 6 |
| Ollama `phi4:14b` | 11 PASS / 12 FAIL / 1 BLOCKED | 2 PASS / 21 FAIL / 1 BLOCKED | 9 | missing columns 11, result set mismatch 4 |

## Interpretation

Strict eval substantially increases FAIL counts. This does not mean the models got worse.
It means the previous evaluator was intentionally lightweight and allowed partial-result matches.

The biggest newly exposed issues are:

1. **Missing expected columns**
   - Models often return a useful-looking subset but omit required columns like `campaign_count`, `included_in_creator_review`, `training_rows_used`, or expected aliases.
2. **Result set mismatch**
   - The row count and first row may pass lightweight checks, but the full ordered rows differ.
3. **Missing required SQL features**
   - Latest snapshot filters, explicit limit values, joins, and aggregate aliases need stronger prompt examples.
4. **Existing refusal/provider failures**
   - Strict eval preserves answerable refusals and provider errors as failures; it does not reinterpret them.

## Failure-Driven Improvement Model

The combined lightweight + strict failure model is written to:

`docs/analysis/stage6_text2sql_failure_improvement_model.md`

Top recommended actions:

1. Fix schema context columns and add expected output-column examples.
2. Add required SQL feature examples and validator-aligned constraints.
3. Add ordering and top-row priority examples.
4. Tighten LIMIT policy.
5. Add prediction monitor `objective` and related few-shot examples.

## Known Limitations

- Strict feature checks are string-based, not a full SQL AST parser.
- The strict runner reuses saved generated SQL; it does not measure model variance.
- Some strict failures may be acceptable product behavior if the UI does not require every expected column, but for benchmark-style eval they should remain failures.
