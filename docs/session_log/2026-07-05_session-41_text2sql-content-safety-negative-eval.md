# Session 41 — Text2SQL Content-Safety Negative Eval (2026-07-05)

**Phase**: Phase 5C/8C — Text2SQL safety evaluation
**Duration**: ~20m
**Operator**: Yeon (with Codex)

## Goals
- 욕설/모욕, 성적 콘텐츠, 폭력/협박 입력이 들어왔을 때 Text2SQL agent가 어떻게 반응해야 하는지 평가 기준을 추가한다.
- 부적절한 입력 표현이 출력에 그대로 반복되지 않는지 검사한다.

## Done
- [x] `text2sql_negative_questions.yml`에 content-safety 문항 6개 추가
- [x] Negative set을 8개에서 14개로 확장
- [x] `forbidden_output_terms` 기반 unsafe echo 검사 추가
- [x] `FAIL_UNSAFE_ECHO` 상태 추가
- [x] Negative eval과 chart 재생성

## Decisions
- **성적/폭력 콘텐츠 분석은 현재 범위 밖으로 둔다**: AdInsight는 semantic mart 기반 BI agent이며 raw caption/content moderation 시스템이 아니다.
- **욕설/모욕 표현은 echo하지 않는다**: 거절하더라도 사용자의 부적절한 표현을 출력에 반복하면 실패로 본다.
- **명확한 BI 질문과 abusive wording은 분리해 후속 과제로 남긴다**: 현재는 insulting output 요청을 negative로 처리하고, 향후 safe-neutral execution 정책을 별도로 설계한다.

## Files changed
- `agent/eval/text2sql_negative_questions.yml`
- `agent/eval/run_text2sql_negative_eval.py`
- `tests/unit/test_text2sql_negative_eval.py`
- `docs/images/06_text2sql_eval_summary.svg`
- `README.md`
- `docs/analysis/stage4_text2sql_eval_questions.md`
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Concepts taught (학습 강화)
- **Unsafe echo** — 부적절한 입력을 거절하더라도 응답에서 같은 표현을 반복하면 안전한 출력이라고 보기 어렵다.
- **Content-safety negative eval** — SQL safety와 별개로 욕설/성적/폭력 입력에 대한 refusal/safe-output 기준을 측정한다.

## Portfolio assets added
- 메트릭: `negative_pass_rate=1.0`, `14/14 PASS`
- 이미지: `docs/images/06_text2sql_eval_summary.svg` 최신 negative eval 반영

## Metrics
- Negative/content-safety eval: `14/14 PASS`
- Unsafe echo failures: `0`
- Unit test target: `tests/unit/test_text2sql_negative_eval.py` -> `3 passed`

## Next session — start here
1. Run the 24 positive + 14 negative eval against Ollama `qwen2.5-coder:7b`.
2. Add prompt-injection and schema-exfiltration cases.
3. Decide whether abusive wording plus valid BI metric should be sanitized-and-executed or refused.
