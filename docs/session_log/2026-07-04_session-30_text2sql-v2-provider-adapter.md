# Session 30 — Text2SQL v2 Provider Adapter (2026-07-04)

**Phase**: Phase 5C/8C — Text2SQL v2 real-provider integration boundary
**Duration**: ~35m
**Operator**: Yeon (with Codex)

## Goals
- `/query/v2`와 v2 eval runner가 mock provider에 하드코딩되지 않게 한다.
- 실제 LLM provider/gateway를 붙일 수 있는 adapter boundary를 만든다.
- API 키가 없어도 기존 mock demo와 CI가 깨지지 않게 유지한다.

## Done
- [x] `agent/text2sql/provider.py`를 추가했다.
- [x] `TEXT2SQL_PROVIDER=mock` 기본 provider를 정의했다.
- [x] `TEXT2SQL_PROVIDER=http_json` external gateway adapter를 추가했다.
- [x] `/query/v2`가 provider factory를 통해 client와 mode를 선택하도록 변경했다.
- [x] `agent/eval/run_text2sql_v2_eval.py`도 같은 provider factory를 사용하도록 변경했다.
- [x] `execute_generated_question()`에 provider mode 주입을 추가했다.
- [x] provider factory와 response contract validation unit test를 추가했다.

## Decisions
- **직접 SDK 의존성을 추가하지 않는다**: OpenAI/Bedrock 선택 전까지는 `http_json` gateway contract로 provider boundary만 고정한다.
- **기본값은 mock으로 유지한다**: 로컬 demo, CI, 포트폴리오 evidence가 외부 API 키에 의존하지 않게 한다.
- **eval runner와 API가 같은 factory를 쓴다**: demo serving과 batch evaluation의 provider drift를 줄인다.

## Files changed
- `agent/text2sql/provider.py` — provider factory, HTTP JSON adapter, response validation
- `agent/text2sql/generator.py` — generated result mode injection
- `api/main.py` — `/query/v2` provider factory wiring
- `agent/eval/run_text2sql_v2_eval.py` — eval provider factory wiring
- `tests/unit/test_text2sql_v2.py` — provider factory and contract tests
- `README.md` — provider env contract
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — adapter status and contract
- `docs/portfolio_draft.md` — portfolio checklist update
- `CLAUDE.md` — current phase/session summary update
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — provider adapter metric append

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `20 passed`
- `git diff --check` -> pass
- `set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_text2sql_v2_eval.py`
  - `8 PASS / 10 REFUSED / 0 BLOCKED`

## Next session — start here
1. Choose the real provider gateway:
   - OpenAI-compatible gateway
   - Bedrock-backed gateway
   - local proxy that implements the `http_json` contract
2. Run with:
   - `TEXT2SQL_PROVIDER=http_json`
   - `TEXT2SQL_PROVIDER_URL=...`
   - optional `TEXT2SQL_PROVIDER_API_KEY=...`
3. Execute `agent/eval/run_text2sql_v2_eval.py` and compare against mock:
   - Exec Acc
   - Refuse Rate
   - Unsafe Block Rate
   - p50/p95 latency
