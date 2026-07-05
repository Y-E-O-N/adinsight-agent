# Session 39 — Local Text2SQL Model Eval Rubric (2026-07-05)

**Phase**: Phase 5C/8C — local small-model Text2SQL evaluation
**Duration**: ~35m
**Operator**: Yeon (with Codex)

## Goals
- Ollama `qwen2.5-coder:7b`와 다른 local Text2SQL 모델을 비교할 평가 기준을 만든다.
- 공개 Text2SQL benchmark 관행을 확인하고, AdInsight 18문항 eval runner에 적용한다.

## Done
- [x] Spider/BIRD/Test Suite Accuracy/Text2SQL 평가 논문 기준을 조사
- [x] `agent/eval/text2sql_model_scoring.py` 추가
- [x] `agent/eval/run_text2sql_v2_eval.py` summary에 `model_score`와 tier 포함
- [x] scoring unit tests 추가
- [x] 평가 기준 문서 `docs/analysis/stage6_text2sql_local_model_eval_rubric.md` 작성
- [x] README, portfolio draft, CLAUDE, metrics 갱신

## Decisions
- **단일 Exec Acc만 쓰지 않는다**: 적은 질문만 답하고 나머지를 거절하는 모델이 과대평가될 수 있다.
- **AdInsight model score는 4요소 합산**: answerable execution 45%, total pass coverage 25%, safety 20%, p95 latency 10%.
- **tier를 분리한다**: score가 높아도 refusal이 높으면 `demo_candidate`가 아니라 `needs_prompt_or_schema_tuning`으로 남긴다.

## Files changed
- `agent/eval/text2sql_model_scoring.py` — Text2SQL 모델 비교 scoring model
- `agent/eval/run_text2sql_v2_eval.py` — eval summary에 provider metadata와 `model_score` 추가
- `tests/unit/test_text2sql_model_scoring.py` — scoring rubric unit tests
- `tests/unit/test_text2sql_v2_eval.py` — v2 eval summary regression test
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md` — 모델 평가 기준 문서
- `README.md` — 로컬 모델 평가 기준 링크 추가
- `docs/portfolio_draft.md` — portfolio checklist 반영
- `CLAUDE.md` — 현재 Phase와 직전 세션 요약 갱신
- `docs/session_log/README.md` — session index 추가
- `metrics/run_results.jsonl` — rubric checkpoint 기록

## Concepts taught (학습 강화)
- **Execution Accuracy** — 생성 SQL이 실제 DB에서 정답 결과를 반환하는지 보는 Text2SQL 핵심 지표.
- **Coverage vs Refusal** — 모델이 맞춘 비율과 거절한 비율을 분리해야 작은 모델을 공정하게 비교할 수 있다.
- **Safety score** — validator가 위험/부적합 SQL을 얼마나 자주 막는지 모델 선택 기준에 포함한다.

## Portfolio assets added
- 문서: `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- 메트릭: `metrics/run_results.jsonl`에 `local_text2sql_model_eval_rubric` append
- 코드: eval runner summary에 `model_score` 추가

## Open questions
- `qwen2.5-coder:7b` 전체 18문항 eval score는 아직 실행 전이다.
- 다음 후보 모델은 `qwen2.5-coder:14b`, SQL 특화 모델, BIRD 계열 7B 모델 중 로컬 메모리와 Ollama 지원 여부를 기준으로 고른다.

## Metrics
- scoring weights: execution `0.45`, coverage `0.25`, safety `0.20`, latency `0.10`
- p95 latency target: `5000ms`

## Next session — start here
1. Ollama gateway가 떠 있는 상태에서 `TEXT2SQL_PROVIDER=http_json`으로 전체 18문항 eval을 실행한다.
2. `qwen2.5-coder:7b` baseline `model_score`를 기록한다.
3. 같은 command에서 `TEXT2SQL_OLLAMA_MODEL`만 바꿔 후보 모델 1~2개를 비교한다.
