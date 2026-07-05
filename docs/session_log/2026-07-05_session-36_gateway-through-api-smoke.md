# Session 36 — Gateway Through API Smoke (2026-07-05)

**Phase**: Phase 5C/8C — Text2SQL gateway end-to-end smoke
**Duration**: ~15m
**Operator**: Yeon (with Codex)

## Goals
- `/query/v2`가 mock client를 직접 쓰는 대신 local Text2SQL gateway를 HTTP로 호출하는 경로를 검증한다.

## Done
- [x] gateway server 실행: `127.0.0.1:8010`
- [x] API server 실행: `127.0.0.1:8000`
- [x] API env:
  - `TEXT2SQL_PROVIDER=http_json`
  - `TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate`
  - `POSTGRES_HOST=localhost`
- [x] gateway `/health` 확인
- [x] API `/health` 확인
- [x] `/query/v2` live smoke 확인

## Result
- gateway `/health` -> `200 OK`
- API `/health` -> `200 OK`
- `/query/v2` -> `200 OK`
- mode: `llm_generated_sql_v2_http_json`
- row count: `5`
- top campaign: `camp_000029`
- latency: `58.981ms`

## Decisions
- **gateway-first 구조가 실제로 동작함을 확인했다**: Web UI가 나중에 붙어도 serving API는 provider별 SDK를 몰라도 된다.
- **아직 real LLM provider는 아님**: gateway backend는 여전히 `MockSqlGenerationClient`다. 다음 단계는 gateway 내부 backend를 OpenAI/Bedrock/Gemini 중 하나로 교체하는 것이다.

## Files changed
- `docs/architecture/text2sql_gateway_architecture.md`
- `docs/api/query_v2_request_response_examples.md`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `docs/session_log/2026-07-05_session-36_gateway-through-api-smoke.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `24 passed`
- `git diff --check` -> pass

## Next session — start here
1. Choose gateway backend provider:
   - OpenAI-compatible
   - Bedrock
   - Gemini
2. Implement provider backend inside `text2sql_gateway`.
3. Keep `/query/v2` unchanged.
