# 2026-07-06 Session 44 — Text2SQL Prompt Schema Fallback Tuning

## Goals

- Local model raw benchmark 이후 모델 교체만으로 부족했던 문제를 prompt/schema/fallback 설계로 먼저 개선한다.
- Model-only eval과 product fallback behavior를 분리한다.
- `qwen2.5-coder:7b`, `phi4:14b`만 선별 재평가한다.

## Done

- `SCHEMA_CONTEXT_V1`에 table별 canonical SQL examples를 추가했다.
  - campaign ROI highest ROAS
  - campaign objective aggregation
  - latest prediction MAE/bias
  - creator review candidates
- Ollama gateway prompt에 few-shot JSON examples와 refusal rule을 추가했다.
- Ollama request에 deterministic options를 기본 적용했다.
  - `TEXT2SQL_OLLAMA_TEMPERATURE`, default `0.0`
  - `TEXT2SQL_OLLAMA_SEED`, default `7`
- `/query/v2`에 deterministic registry fallback을 구현했다.
  - provider refusal/block/error 이후 v1 curated registry exact-match가 있으면 fallback response 반환
  - response mode: `deterministic_expected_sql_registry_fallback_v1`
  - eval runner는 fallback 없이 model-only 평가를 유지
- Unit tests를 추가했다.
  - fallback success
  - fallback disabled
  - gateway deterministic options payload

## Results

Tuned model-only positive eval:

| Model | PASS | FAIL | REFUSED | BLOCKED | Exec Acc | p95 ms | Score | Tier |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `qwen2.5-coder:7b` | 8 | 16 | 0 | 0 | 0.3333 | 8082.541 | 49.52 | `not_recommended` |
| `phi4:14b` | 11 | 12 | 0 | 1 | 0.4583 | 18781.653 | 53.91 | `needs_prompt_or_schema_tuning` |

Tuned negative/content-safety eval:

| Model | PASS | FAIL | Negative Pass Rate | Unsafe Echo Failures | Executed Failures |
|---|---:|---:|---:|---:|---:|
| `qwen2.5-coder:7b` | 13 | 1 | 0.9286 | 0 | 1 |
| `phi4:14b` | 14 | 0 | 1.0000 | 0 | 0 |

## Decisions

- `phi4:14b` is the best current local model candidate after tuning, but still not a primary free-form Text2SQL model.
- `/query/v2` should be presented as provider + validator + fallback architecture, not as fully solved autonomous SQL generation.
- Product demo path should keep deterministic `/query` v1 and fallback-enabled `/query/v2`; model-only numbers remain honest evaluation evidence.

## Files changed

- `api/main.py`
- `agent/text2sql/generator.py`
- `text2sql_gateway/backends.py`
- `tests/unit/test_api.py`
- `tests/unit/test_text2sql_gateway.py`
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- `docs/analysis/stage6_llm_text2sql_v2_design.md`
- `docs/images/06_text2sql_eval_summary.svg`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `metrics/run_results.jsonl`

## Concepts taught

- Fallback-enabled product quality and model-only benchmark quality are different measurements.
- Refusal rate can improve while semantic SQL accuracy still remains insufficient.
- Few-shot schema/prompt examples can improve local LLM behavior, but failed-case-driven prompt tuning is still needed.

## Portfolio assets added

- Updated local model rubric with tuned rerun results.
- Updated SVG eval chart.
- Added `/query/v2` fallback implementation evidence and tests.

## Open questions

- Should `phi4:14b` failed cases be converted into more canonical few-shot examples?
- Should the eval runner record provider timeout/error as `PROVIDER_ERROR` instead of crashing/incomplete?
- Should product docs expose fallback mode explicitly in the web UI?

## Metrics

- `phi4:14b` tuned score: `53.91`
- `phi4:14b` tuned negative pass rate: `1.0`
- `qwen2.5-coder:7b` tuned score: `49.52`

## Next session — start here

1. Inspect `phi4:14b` failed questions and group them by failure type.
2. Add targeted few-shot examples only for high-value demo questions.
3. Consider a small web UI that calls fallback-enabled `/query/v2` and displays `mode` clearly.
