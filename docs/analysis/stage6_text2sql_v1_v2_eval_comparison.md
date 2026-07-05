# Stage 6 Text2SQL v1/v2 Eval Comparison

**작성일**: 2026-07-04
**상태**: deterministic v1 and v2 mock baseline measured

## 1. Purpose

Text2SQL v1과 v2 mock harness를 같은 expected-SQL 평가셋 관점에서 비교한다.

현재 목표는 v2가 v1보다 낫다고 주장하는 것이 아니다. v2 real provider를 붙이기 전에, mock provider가 어떤 질문에는 답하고 어떤 질문은 안전하게 거절하는지 수치로 남기는 것이 목적이다.

## 2. Evaluation Set

- Source: `agent/eval/text2sql_questions.yml`
- Total questions: `18`
- Language split: English `9`, Korean `9`
- Domains:
  - creator sponsored review
  - campaign ROI summary
  - campaign ROAS prediction monitor

## 3. Result Summary

| Version | Mode | Total | PASS | FAIL | REFUSED | BLOCKED | Exec Acc | Refuse Rate | Unsafe Block Rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | `deterministic_expected_sql_registry_v1` | 18 | 18 | 0 | 0 | 0 | 1.0000 | 0.0000 | 0.0000 |
| v2 mock | `llm_generated_sql_v2_mock` | 18 | 13 | 0 | 5 | 0 | 1.0000 answerable-only | 0.2778 | 0.0000 |

## 4. Interpretation

v1 is the production-safe baseline:

- It only answers curated questions.
- It has no LLM generation risk.
- It passed all 18 expected-SQL questions.

v2 mock is a provider-boundary smoke:

- It answers the campaign ROI, prediction-monitor, and focused creator-review questions implemented in `MockSqlGenerationClient`.
- It refuses 5 unsupported creator-review questions.
- It did not generate unsafe SQL.
- Its answerable-only Exec Acc is `1.0`, but this does not mean v2 is better than v1. It means the supported mock cases match expected-SQL behavior.

## 5. Failure / Refusal Cases

The 5 REFUSED cases are expected until a richer mock provider or real LLM provider is added.

Representative refusal categories:

| Category | Example question id | Reason |
|---|---|---|
| Broad creator candidate list | `p4_q002` | Current validator requires a LIMIT for non-aggregate generated SQL; broad unbounded lists remain refused. |
| Creator sponsored candidates | `p4_q004` | This no-LIMIT expected query is left refused in v2 mock to avoid unsafe broad generated SQL. |
| Creator engagement signals | `p4_q009` | Mock provider does not yet generate creator-level review SQL. |

## 6. Safety Notes

- `BLOCKED = 0` means no generated SQL violated current validator rules during this run.
- `REFUSED = 5` is preferable to unsafe guessing at this stage.
- The next provider implementation should reduce REFUSED while keeping BLOCKED and FAIL low.

## 7. Next Quality Targets

| Target | Current | Next target |
|---|---:|---:|
| v2 total PASS | 13 | 15+ |
| v2 REFUSED | 5 | 3 or lower |
| v2 BLOCKED unsafe SQL | 0 | 0 |
| v2 FAIL among answerable questions | 0 | 0 |

## 8. Commands

v1 expected-SQL baseline:

```bash
set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_expected_sql.py
```

v2 mock eval:

```bash
set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_text2sql_v2_eval.py
```
