# 2026-07-06 Session 43 — Ollama Local Model Benchmark

## Goals

- Ollama local model 후보를 모두 다운로드하고 같은 Text2SQL gateway/eval runner로 비교한다.
- Positive expected-SQL 24문항과 negative/content-safety 14문항 기준으로 demo readiness를 판단한다.
- 평가 중 드러난 runner/gateway robustness gap을 작게 보강한다.

## Done

- 다운로드 완료:
  - `qwen2.5-coder:7b`
  - `qwen2.5-coder:14b`
  - `sqlcoder:7b`
  - `sqlcoder:15b`
  - `gemma4:12b`
  - `qwen3.5:9b`
  - `phi4:14b`
- 각 모델마다 temporary Text2SQL gateway를 `127.0.0.1:8011`에 띄우고 `TEXT2SQL_PROVIDER=http_json` eval runner로 평가했다.
- `docs/images/06_text2sql_eval_summary.svg`를 최신 metrics 기준으로 재생성했다.
- Gateway Ollama timeout을 controlled `GatewayBackendError`로 변환하도록 보강했다.
- Negative eval runner가 negative SQL 실행 중 DB error를 만나도 `FAIL_EXECUTED`로 기록하고 계속 진행할 수 있게 보강했다.

## Results

Positive 24문항 complete run 기준:

| Model | PASS | FAIL | REFUSED | BLOCKED | Exec Acc | p95 ms | Score | Tier |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `phi4:14b` | 8 | 12 | 3 | 1 | 0.3810 | 26103.743 | 46.56 | `not_recommended` |
| `qwen2.5-coder:14b` | 7 | 16 | 0 | 1 | 0.2917 | 21068.660 | 41.96 | `not_recommended` |
| `qwen2.5-coder:7b` rerun | 6 | 15 | 3 | 0 | 0.2857 | 10516.514 | 43.86 | `not_recommended` |
| `sqlcoder:7b` | 0 | 2 | 21 | 1 | 0.0000 | 7986.261 | 25.43 | `not_recommended` |
| `qwen3.5:9b` | 0 | 0 | 24 | 0 | 0.0000 | 16235.585 | 23.08 | `not_recommended` |

Incomplete positive runs:

- `sqlcoder:15b`: local model request timeout during positive eval; negative `14/14 PASS`.
- `gemma4:12b`: local model request timeout during positive eval; negative eval later attempted invalid SQL and crashed before the hardening patch.

Negative/content-safety 14문항:

- `sqlcoder:7b`, `sqlcoder:15b`, `qwen3.5:9b`: `14/14 PASS`
- `qwen2.5-coder:7b`: `13/14 PASS`, unsafe echo failure `1`
- `qwen2.5-coder:14b`: `11/14 PASS`, executed failure `1`, unsafe echo failure `2`
- `phi4:14b`: `12/14 PASS`, unsafe echo failure `2`

## Decisions

- 현재 prompt/schema context에서는 모델 크기를 키우는 것만으로 demo-ready Text2SQL 품질이 나오지 않는다.
- Batch 내 최고 complete model은 `phi4:14b`였지만 score `46.56`으로 기준 미달이다.
- `sqlcoder` 계열은 negative refusal은 강하지만 answerable 질문을 과도하게 거절해 현재 gateway prompt에는 맞지 않는다.
- `/query/v2` 데모는 당분간 deterministic v1 fallback과 mock/provider evidence를 함께 보여주고, real local model은 evaluation artifact로 설명한다.

## Files changed

- `text2sql_gateway/backends.py`
- `agent/eval/run_text2sql_negative_eval.py`
- `tests/unit/test_text2sql_gateway.py`
- `tests/unit/test_text2sql_negative_eval.py`
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- `docs/images/06_text2sql_eval_summary.svg`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `metrics/run_results.jsonl`

## Concepts taught

- Text2SQL 모델 평가는 execution accuracy만 보면 부족하고 pass coverage, refusal behavior, unsafe echo, p95 latency를 함께 봐야 한다.
- Negative set을 잘 통과하는 모델이 실제 answerable BI 질문에는 쓸모없을 수 있다.
- Local LLM은 같은 모델도 재실행 variance가 있으므로 repeated-run 또는 deterministic option 고정이 필요하다.

## Portfolio assets added

- Updated local model comparison table in `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- Updated SVG eval chart at `docs/images/06_text2sql_eval_summary.svg`
- Benchmark summary row in `metrics/run_results.jsonl`

## Open questions

- Ollama `options`로 temperature/seed를 고정할지 검토해야 한다.
- Gateway prompt에 table별 few-shot을 넣고 `phi4:14b`, `qwen2.5-coder:7b`를 repeated-run으로 다시 비교해야 한다.
- Provider timeout/error를 positive eval summary row에 `PROVIDER_ERROR`로 누적하는 runner 개선이 필요하다.

## Metrics

- Best complete local positive run: `phi4:14b`, score `46.56`, exec_acc `0.3810`, p95 `26103.743ms`.
- Best negative pass rate among usable complete rows: `sqlcoder:7b`, `qwen3.5:9b`, `14/14 PASS`, but both over-refused answerable questions.

## Next session — start here

1. Run `uv run ruff check` and `uv run pytest -q` if not already done after this handoff.
2. Add deterministic Ollama generation options or prompt few-shot examples.
3. Re-run only `phi4:14b` and `qwen2.5-coder:7b` after prompt/schema tuning.
