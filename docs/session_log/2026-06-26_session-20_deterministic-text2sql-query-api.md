# Session 20 — Deterministic Text2SQL Query API (2026-06-26)

**Phase**: Phase 6 — deterministic Text2SQL v1 + FastAPI query serving
**Duration**: ~1h
**Operator**: Yeon (with Codex)

## Goals
- FastAPI에 자연어 질의 API v1을 추가한다.
- 자유형 LLM SQL 생성 전에, 검증된 expected SQL registry 기반 deterministic baseline을 만든다.
- 영어/한국어 smoke 결과를 README, portfolio draft, metrics에 남긴다.

## Done
- [x] `POST /query` endpoint를 추가했다.
  - 자연어 질문을 받는다.
  - `agent/eval/text2sql_questions.yml`의 검증된 question registry와 매칭한다.
  - SELECT SQL만 실행한다.
  - SQL, rows, answer, latency를 반환한다.
- [x] 영어/한국어 live smoke를 확인했다.
  - `"Which campaigns have the highest ROAS?"` -> `p5_q001`, rows `5`, latency `41.013ms`
  - `"최신 ROAS 예측 모델의 MAE와 bias를 요약해줘."` -> `p5_q008`, rows `1`, latency `42.839ms`
- [x] README에 `/query` curl 예시를 추가했다.
- [x] `docs/portfolio_draft.md`, `metrics/run_results.jsonl`에 실측 결과를 기록했다.
- [x] commit/push를 완료했다.
  - commit: `848bd27 Add deterministic Text2SQL query API`

## Decisions
- **deterministic registry v1으로 시작한다**: 현재 `/query`는 자유형 LLM SQL 생성이 아니라 curated expected SQL registry exact-match 방식이다. 이렇게 해야 hallucination과 destructive SQL 위험을 줄이고, 이후 LLM SQL generation을 붙일 때 regression baseline으로 쓸 수 있다.
- **SELECT-only guardrail을 둔다**: API가 실행하는 SQL은 SELECT로 시작해야 하며, destructive token은 차단한다.

## Files changed
- `api/main.py` — `POST /query` endpoint 추가
- `api/schemas.py` — query request/response schema 추가
- `agent/text2sql/registry.py` — deterministic registry matching, SELECT validation, execution, answer builder
- `tests/unit/test_api.py` — `/query` smoke coverage 추가
- `README.md` — `/query` curl 예시와 limitation 문구 추가
- `docs/portfolio_draft.md` — FastAPI serving evidence에 `/query` 결과 추가
- `metrics/run_results.jsonl` — `text2sql_query_api_v1_smoke` metrics append

## Concepts taught
- **Deterministic Text2SQL baseline** — LLM이 SQL을 자유 생성하기 전, 검증된 질문과 SQL만 실행하는 baseline을 먼저 만든다.
- **Guardrail** — SQL API에서는 실행 가능한 SQL 범위를 좁혀 read-only 동작을 강제한다.
- **Registry-based self-service** — 완전한 agent는 아니지만, 반복 질문을 안정적으로 API화할 수 있는 첫 단계다.

## Portfolio assets added
- `/query` live smoke metrics:
  - English `p5_q001`, rows `5`, latency `41.013ms`
  - Korean `p5_q008`, rows `1`, latency `42.839ms`
- `metrics/run_results.jsonl` row:
  - `phase=p6`
  - `step=text2sql_query_api_v1_smoke`
  - `mode=deterministic_expected_sql_registry_v1`
- README API usage section

## Open questions
- free-form LLM SQL generation v2를 바로 붙일지, 먼저 Superset dashboard와 데모 시나리오를 정리할지 결정한다.
- Text2SQL 데모 GIF를 언제 캡처할지 정한다.

## Metrics
- `uv run pytest -q` -> `4 passed`
- `ruff check` -> pass
- expected-SQL evaluator -> `18/18 PASS`
- latest functional commit: `848bd27 Add deterministic Text2SQL query API`
- push status at checkpoint: `origin/main` synchronized

## Next session — start here
1. `CLAUDE.md`와 이 로그를 읽고 `/query`가 deterministic registry v1임을 먼저 확인한다.
2. Superset campaign ROAS monitor와 `/query` 결과를 연결하는 demo runbook을 작성한다.
3. 다음 후보:
   - `docs/images/06_text2sql_demo.gif` capture
   - AWS target architecture document
   - LLM SQL generation v2 design
