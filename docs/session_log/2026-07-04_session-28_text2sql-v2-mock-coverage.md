# Session 28 — Text2SQL v2 Mock Coverage Expansion (2026-07-04)

**Phase**: Phase 5C — Text2SQL v2 quality expansion
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- v2 mock provider가 expected-SQL 18문항 중 더 많은 질문에 답하게 만든다.
- 안전하지 않은 SQL을 늘리지 않고 PASS coverage를 올린다.
- v1/v2 comparison 문서를 최신 수치로 갱신한다.

## Done
- [x] `MockSqlGenerationClient`를 campaign ROI / prediction monitor p5 질문 중심으로 확장했다.
- [x] p5 질문 8개가 answerable하도록 SQL mapping을 추가했다.
- [x] non-aggregate query는 validator 요구에 맞게 안전한 `LIMIT`을 포함했다.
- [x] unit test를 추가했다.
- [x] v2 eval runner를 실제 DB 기준으로 재실행했다.

## Decisions
- **creator-review p4 질문은 아직 보류한다**: p5 campaign ROI/prediction monitor가 현재 `/query` demo와 AWS architecture story에 더 직접 연결된다.
- **mock coverage는 expected-SQL과 같은 의미의 SQL로만 확장한다**: 무리하게 자유 생성처럼 꾸미지 않고, regression baseline을 명확히 유지한다.

## Files changed
- `agent/text2sql/llm_client.py` — p5 question SQL mappings 추가
- `tests/unit/test_text2sql_v2.py` — p5 aggregation mock provider test 추가
- `agent/eval/run_text2sql_v2_eval.py` — known limitation 문구 최신화
- `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md` — v2 mock eval 수치 최신화
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — v2 eval status 최신화
- `docs/portfolio_draft.md` — v2 eval checklist 수치 최신화
- `CLAUDE.md` — current Phase/session summary update
- `docs/session_log/2026-07-04_session-28_text2sql-v2-mock-coverage.md` — current handoff
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — latest v2 mock eval metrics append

## Metrics
- Before: `2 PASS / 16 REFUSED / 0 BLOCKED`
- After: `8 PASS / 10 REFUSED / 0 BLOCKED`
- answerable exec_acc: `1.0`
- refuse_rate: `0.5556`
- `uv run pytest -q` -> `14 passed`

## Next session — start here
1. Choose one:
   - expand creator-review p4 mock coverage
   - or design real provider adapter
2. Keep `/query` v1 unchanged as deterministic baseline.
