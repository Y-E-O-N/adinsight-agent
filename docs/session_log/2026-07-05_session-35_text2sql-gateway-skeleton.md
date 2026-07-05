# Session 35 — Text2SQL Gateway Skeleton (2026-07-05)

**Phase**: Phase 5C/8C — Text2SQL gateway-first architecture
**Duration**: ~35m
**Operator**: Yeon (with Codex)

## Goals
- 웹 UI까지 고려해 Text2SQL provider 호출 책임을 serving API에서 분리한다.
- 실제 LLM key 없이도 gateway contract와 service boundary를 먼저 구현한다.

## Done
- [x] `text2sql_gateway/main.py` 추가
- [x] `GET /health` 추가
- [x] `POST /text2sql/generate` 추가
- [x] optional bearer auth `TEXT2SQL_GATEWAY_API_KEY` 추가
- [x] `docker-compose.yml`에 `text2sql-gateway` service 추가(port `8010`)
- [x] `infra/api/Dockerfile`이 gateway package를 copy하도록 수정
- [x] gateway unit tests 추가
- [x] gateway-first architecture 문서 추가

## Decisions
- **Gateway-first로 간다**: 웹 UI가 생기면 UI와 serving API는 provider별 SDK를 몰라도 된다.
- **현재 backend는 mock 유지**: 외부 LLM key 없이도 CI, demo, contract 검증이 가능하다.
- **Gateway auth는 optional**: 로컬 개발은 key 없이 가능하고, 운영/공유 환경에서는 bearer token을 켤 수 있다.

## Files changed
- `text2sql_gateway/main.py`
- `text2sql_gateway/__init__.py`
- `tests/unit/test_text2sql_gateway.py`
- `docker-compose.yml`
- `infra/api/Dockerfile`
- `docs/architecture/text2sql_gateway_architecture.md`
- `README.md`
- `docs/api/query_v2_request_response_examples.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `24 passed`
- `git diff --check` -> pass
- gateway HTTP smoke:
  - `GET /health` -> `200 OK`
  - `POST /text2sql/generate` -> `200 OK`

## Next session — start here
1. Run gateway + serving API together:
   - gateway on `8010`
   - API on `8000`
   - API env `TEXT2SQL_PROVIDER=http_json`
2. Run `/query/v2` through gateway.
3. Later replace gateway mock backend with OpenAI/Bedrock/Gemini provider.
