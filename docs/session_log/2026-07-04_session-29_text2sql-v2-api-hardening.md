# Session 29 — Text2SQL v2 API Hardening (2026-07-04)

**Phase**: Phase 5C/8C — Text2SQL v2 API hardening
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- `/query/v2` mock endpoint에 운영 안전장치를 추가한다.
- SQL 실행 timeout, audit log, error-path tests를 보강한다.

## Done
- [x] generated SQL 실행 전에 `set local statement_timeout = 5000`을 적용했다.
- [x] `agent/text2sql/audit.py`를 추가했다.
- [x] `/query/v2` success/refused/blocked/error audit record를 `logs/text2sql_audit.jsonl`에 best-effort append하도록 했다.
- [x] `/query/v2` error path를 명시화했다.
  - not answerable -> `404`
  - validation blocked -> `400`
  - unexpected error -> `500`
- [x] API tests를 보강했다.
  - success audit
  - `404` refused audit
  - `400` blocked audit
  - `500` unexpected error audit
- [x] statement timeout 실행을 unit test로 확인했다.

## Decisions
- **audit log는 `logs/`에 둔다**: runtime request log이므로 Git 커밋 대상이 아니다.
- **audit 실패는 API 실패로 만들지 않는다**: local disk/logging failure가 query serving 자체를 깨지 않도록 best-effort로 처리한다.
- **statement timeout은 v2 generated SQL boundary에 둔다**: v1 registry SQL보다 v2 generated SQL이 더 위험하므로 먼저 v2부터 방어한다.

## Files changed
- `agent/text2sql/audit.py` — JSONL audit writer
- `agent/text2sql/generator.py` — statement timeout before generated SQL execution
- `api/main.py` — audit logging and explicit `/query/v2` error handling
- `tests/unit/test_api.py` — `/query/v2` 200/400/404/500 tests
- `tests/unit/test_text2sql_v2.py` — statement timeout assertion
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — hardening status
- `CLAUDE.md` — current Phase/session summary update
- `docs/session_log/2026-07-04_session-29_text2sql-v2-api-hardening.md` — current handoff
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — hardening metric append

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `16 passed`
- `git diff --check` -> pass

## Next session — start here
1. Decide real provider path:
   - OpenAI-compatible adapter
   - Bedrock adapter
   - keep mock and expand creator coverage
2. Keep `/query` v1 as deterministic baseline.
