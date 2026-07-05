# Session 31 — Text2SQL v2 Focused Coverage Expansion (2026-07-05)

**Phase**: Phase 5C — Text2SQL v2 quality expansion
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- v2 mock provider가 18문항 중 더 많은 질문에 답하게 한다.
- Exec Acc, Refuse Rate, Unsafe Block Rate를 최신화한다.
- failure cases를 문서화한다.

## Done
- [x] `MockSqlGenerationClient`에 LIMIT가 명확한 creator-review 질문 5개를 추가했다.
- [x] v2 mock eval을 `8 PASS / 10 REFUSED / 0 BLOCKED`에서 `13 PASS / 5 REFUSED / 0 BLOCKED`로 개선했다.
- [x] no-LIMIT creator list가 validator에서 `BLOCKED`되는 중간 실패를 확인했다.
- [x] no-LIMIT 케이스는 mock answerable에서 제외하고 refusal/failure-case로 문서화했다.
- [x] v1/v2 eval comparison 문서와 README/portfolio/CLAUDE 요약을 최신화했다.

## Decisions
- **broad list는 제한 없이 생성하지 않는다**: v2 generated SQL은 비집계 리스트에 명시적 `LIMIT`가 없으면 validator가 차단한다.
- **mock coverage는 안전한 대표 질문부터 확장한다**: creator-review도 answerable하게 만들되, 무제한 리스트는 아직 refusal로 둔다.
- **중간 BLOCKED run도 metrics evidence로 남긴다**: 실패가 validator guardrail을 설명하는 증거다.

## Files changed
- `agent/text2sql/llm_client.py` — focused creator-review mock SQL 추가
- `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md` — v2 comparison 수치 최신화
- `docs/analysis/stage6_text2sql_v2_failure_cases.md` — failure/refusal cases 문서
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — provider/eval status 최신화
- `README.md` — `/query/v2` 최신 eval 수치
- `docs/portfolio_draft.md` — checklist 최신화
- `CLAUDE.md` — current phase/session summary update
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — live eval metrics append

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `20 passed`
- `git diff --check` -> pass
- `set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_text2sql_v2_eval.py`
  - final: `13 PASS / 5 REFUSED / 0 BLOCKED`
  - answerable exec_acc `1.0`
  - refuse_rate `0.2778`
  - unsafe_block_rate `0.0`

## Next session — start here
1. Real provider gateway 선택/기동:
   - `TEXT2SQL_PROVIDER=http_json`
   - `TEXT2SQL_PROVIDER_URL=...`
2. v2 real-provider eval 실행.
3. mock vs real-provider comparison table 추가.
