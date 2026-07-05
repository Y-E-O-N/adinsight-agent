# Session 40 — Text2SQL Eval Set Hardening + Chart (2026-07-05)

**Phase**: Phase 5C/8C — Text2SQL local model evaluation hardening
**Duration**: ~45m
**Operator**: Yeon (with Codex)

## Goals
- 기존 Text2SQL 평가 문항이 local model 비교에 적절한지 보완한다.
- 전혀 무관한 질문, 위험 SQL, 민감정보 요청, 애매한 질문에 대한 refusal 평가 기준을 추가한다.
- Eval 결과를 그래프로 그릴 수 있는지 확인한다.

## Done
- [x] Positive expected-SQL set을 18개에서 24개로 확장
- [x] 대량 결과 문항에 `limit 20` 추가
- [x] `high`, `often` 같은 애매한 표현을 `Top 10`/`Top 20`으로 명확화
- [x] group-by, threshold filter, latest snapshot, join 기반 hard 문항 6개 추가
- [x] Negative/refusal set 8개 추가
- [x] Negative eval runner 추가
- [x] Dependency-free SVG chart renderer 추가
- [x] Eval chart `docs/images/06_text2sql_eval_summary.svg` 생성

## Decisions
- **Positive와 negative를 분리한다**: 정답 SQL 품질과 refusal/safety 품질은 다른 기준이므로 별도 runner로 기록한다.
- **무관한 질문은 성공적으로 거절해야 한다**: weather/lunch recommendation 같은 질문은 SQL 생성으로 이어지면 실패다.
- **그래프는 SVG로 생성한다**: 현재 runtime dependency에 `matplotlib`이 없으므로 새 의존성 없이 portfolio asset을 만든다.

## Files changed
- `agent/eval/text2sql_questions.yml` — positive expected-SQL set 24문항으로 확장
- `agent/eval/text2sql_negative_questions.yml` — negative/refusal set 8문항 추가
- `agent/eval/run_text2sql_negative_eval.py` — negative eval runner
- `agent/eval/render_text2sql_eval_chart.py` — eval 결과 SVG chart renderer
- `agent/text2sql/llm_client.py` — 변경된 question wording에 맞게 mock exact-match 갱신
- `tests/unit/test_text2sql_negative_eval.py` — negative eval summary test
- `tests/unit/test_text2sql_eval_chart.py` — SVG renderer smoke test
- `docs/images/06_text2sql_eval_summary.svg` — generated chart asset
- `docs/analysis/stage4_text2sql_eval_questions.md` — 평가셋 확장 내용 문서화
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md` — 24 positive + 8 negative 기준 반영
- `README.md`, `docs/portfolio_draft.md`, `CLAUDE.md`, `metrics/run_results.jsonl`

## Concepts taught (학습 강화)
- **Negative eval** — 정답 SQL을 맞추는 능력과 무관/위험 질문을 거절하는 능력은 따로 측정해야 한다.
- **Out-of-domain refusal** — BI agent가 weather/lunch 같은 질문에 SQL을 만들면 실패다.
- **Dependency-free SVG chart** — matplotlib 없이도 JSONL metrics를 portfolio-ready chart로 시각화할 수 있다.

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl`에 positive v2 eval, negative eval, hardening checkpoint append
- 이미지: `docs/images/06_text2sql_eval_summary.svg`
- 문서: `docs/analysis/stage4_text2sql_eval_questions.md`, `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`

## Metrics
- Expected SQL evaluator: `24/24 PASS`
- v2 mock positive eval: `13 PASS / 11 REFUSED / 0 BLOCKED`
- v2 mock `model_score`: `88.54`, tier `needs_prompt_or_schema_tuning`
- Negative eval: `8/8 PASS`, `negative_pass_rate=1.0`
- Chart generation: `docs/images/06_text2sql_eval_summary.svg`, records `7`

## Next session — start here
1. Run the 24 positive + 8 negative eval against Ollama `qwen2.5-coder:7b`.
2. Try one alternate local model and compare score, refusal rate, negative pass rate, and p95 latency.
3. Add prompt-injection and schema-exfiltration negative cases.
