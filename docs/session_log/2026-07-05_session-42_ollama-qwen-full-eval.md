# Session 42 — Ollama Qwen2.5-Coder Full Eval (2026-07-05)

**Phase**: Phase 5C/8C — local Text2SQL model evaluation
**Duration**: ~35m
**Operator**: Yeon (with Codex)

## Goals
- Ollama `qwen2.5-coder:7b`를 24 positive + 14 negative/content-safety eval 기준으로 실제 평가한다.
- 모델 SQL 실행 오류가 발생해도 evaluator가 중단되지 않도록 보강한다.

## Done
- [x] Ollama model 확인: `qwen2.5-coder:7b`, Q4_K_M, 7.6B
- [x] Text2SQL gateway 확인: `text2sql_gateway_ollama_v1`
- [x] Positive eval 첫 실행에서 `CardinalityViolation` 재현
- [x] `run_text2sql_v2_eval.py`가 DB execution/comparison error를 `FAIL`로 기록하도록 보강
- [x] Positive 24문항 eval 완료
- [x] Negative/content-safety 14문항 eval 완료
- [x] Eval chart 재생성

## Results
- Positive eval: `8 PASS / 11 FAIL / 5 REFUSED / 0 BLOCKED`
- `exec_acc`: `0.4211`
- `refuse_rate`: `0.2083`
- p50 latency: `4791.302ms`
- p95 latency: `9528.069ms`
- `model_score`: `52.53`
- tier: `needs_prompt_or_schema_tuning`
- Negative/content-safety eval: `14/14 PASS`
- `negative_pass_rate`: `1.0`
- unsafe echo failures: `0`

## Decisions
- **qwen2.5-coder:7b is not demo-primary yet**: safety/refusal is good, but positive SQL accuracy is too low.
- **Evaluator must keep running on DB errors**: generated SQL can pass validator but fail in Postgres, so DB errors must count as `FAIL` rather than aborting the eval.
- **Next comparison needs a stronger or more SQL-specialized local model**: try a larger Qwen Coder or SQL-specialized candidate before spending time on prompt-only tuning.

## Files changed
- `agent/eval/run_text2sql_v2_eval.py` — DB execution/comparison errors recorded as `FAIL`
- `tests/unit/test_text2sql_v2_eval.py` — regression test for DB execution error handling
- `docs/images/06_text2sql_eval_summary.svg` — latest eval chart
- `README.md`
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Concepts taught (학습 강화)
- **Execution failure vs validation failure** — SQL can be syntactically allowed but still fail at DB execution time.
- **Model selection evidence** — local model choice should use positive accuracy, refusal rate, safety pass rate, and latency together.

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl`에 Ollama positive/negative eval rows
- 이미지: `docs/images/06_text2sql_eval_summary.svg`
- 문서: `docs/analysis/stage6_text2sql_local_model_eval_rubric.md` qwen baseline row

## Next session — start here
1. Try one alternate local model and run the same 24 positive + 14 negative eval.
2. Compare against `qwen2.5-coder:7b` on score, p95 latency, refusal, and negative pass rate.
3. If no local 7B/14B model reaches demo tier, keep deterministic v1 as demo primary and use local LLM as experimental v2.
