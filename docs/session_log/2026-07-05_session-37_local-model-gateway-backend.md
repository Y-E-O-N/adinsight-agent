# Session 37 — Local Model Gateway Backend (2026-07-05)

**Phase**: Phase 5C/8C — local small-model Text2SQL backend
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- 외부 LLM API 없이 로컬 small model을 Text2SQL gateway backend로 붙일 수 있게 한다.
- 로컬 모델 출력이 깨져도 SQL 실행으로 넘어가지 않게 한다.

## Done
- [x] `text2sql_gateway/backends.py` 추가
- [x] `TEXT2SQL_GATEWAY_BACKEND=mock|ollama` backend 선택 추가
- [x] Ollama-compatible `/api/generate` 호출 adapter 추가
- [x] local model prompt builder 추가
- [x] local model JSON contract parser 추가
- [x] invalid JSON / contract mismatch를 `not_answerable`로 refusal 처리
- [x] Docker Compose에 Ollama backend env 추가
- [x] gateway tests 추가
- [x] README / architecture docs / portfolio / CLAUDE 갱신

## Decisions
- **로컬 모델은 DB를 직접 만지지 않는다**: local model은 SQL 후보 JSON만 만들고, `/query/v2` validator가 여전히 실행 전 방어선을 맡는다.
- **깨진 모델 출력은 거절한다**: JSON parsing 실패나 contract mismatch는 `not_answerable`로 처리한다.
- **mock default 유지**: CI와 기본 로컬 데모는 deterministic하게 유지한다.

## Files changed
- `text2sql_gateway/backends.py`
- `text2sql_gateway/main.py`
- `tests/unit/test_text2sql_gateway.py`
- `docker-compose.yml`
- `docs/architecture/text2sql_gateway_architecture.md`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `27 passed`
- `git diff --check` -> pass

## Next session — start here
1. If a local model server is available:
   - run Ollama-compatible `/api/generate`
   - set `TEXT2SQL_GATEWAY_BACKEND=ollama`
   - run gateway and `/query/v2` smoke
2. Evaluate local model output with `agent/eval/run_text2sql_v2_eval.py`.
