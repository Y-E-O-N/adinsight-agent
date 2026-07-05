# Session 38 — Ollama-backed Gateway Smoke (2026-07-05)

**Phase**: Phase 5C/8C — local small-model Text2SQL smoke
**Duration**: ~35m
**Operator**: Yeon (with Codex)

## Goals
- Ollama `qwen2.5-coder:7b`를 Text2SQL gateway backend로 실제 연결한다.
- `/query/v2 -> gateway -> Ollama -> validator -> Postgres` 경로를 검증한다.

## Done
- [x] Ollama `/api/generate` 직접 호출 성공 확인
- [x] gateway `/text2sql/generate`가 `mode=text2sql_gateway_ollama_v1`로 응답하는 것 확인
- [x] `/query/v2`를 Ollama-backed gateway로 호출
- [x] 첫 실패 원인 진단: schema context 부족으로 hallucinated column/table 조합 생성
- [x] `SCHEMA_CONTEXT_V1`에 실제 컬럼과 canonical query example 추가
- [x] `/query/v2` 재실행 성공
- [x] `/query/v2` provider-specific limitation 문구를 provider-agnostic 문구로 수정

## Result
- model: `qwen2.5-coder:7b`
- gateway backend: `TEXT2SQL_GATEWAY_BACKEND=ollama`
- `/query/v2`: `200 OK`
- mode: `llm_generated_sql_v2_http_json`
- generated table: `ai_native.ai_campaign_roi_summary`
- row count: `5`
- top campaign: `camp_000029`
- latency: `4800.432ms`

## Decisions
- **small model에는 명시적 schema context가 필요하다**: 테이블 설명만으로는 컬럼 hallucination이 발생했다.
- **validator 이후에도 DB execution error가 가능하다**: 현재 validator는 table/limit/token 중심이라 column existence까지 완전히 검증하지 않는다.
- **gateway 구조는 유지한다**: 모델 교체는 gateway 내부 backend만 바꾸면 되고 `/query/v2`는 그대로 유지한다.

## Files changed
- `agent/text2sql/generator.py`
- `api/main.py`
- `docs/architecture/text2sql_gateway_architecture.md`
- `docs/api/query_v2_request_response_examples.md`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `docs/session_log/2026-07-05_session-38_ollama-backed-gateway-smoke.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `27 passed`
- `git diff --check` -> pass

## Next session — start here
1. Run `agent/eval/run_text2sql_v2_eval.py` with Ollama backend.
2. Add optional column-level SQL validation or dry-run classification.
3. Consider a stronger local Text2SQL model if refusal/fail rate is high.
