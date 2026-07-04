# Session 24 — LLM Text2SQL v2 Design (2026-07-04)

**Phase**: Phase 5C/6 — LLM SQL generation v2 design + mock endpoint
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- Pending Text2SQL demo/AWS architecture artifacts를 먼저 커밋하고 push한다.
- deterministic `/query` v1 이후의 LLM SQL generation v2를 안전하게 설계한다.
- provider dependency를 바로 추가하지 않고, v1 evaluator와 validator를 기준선으로 두는 v2 mock harness와 `/query/v2` endpoint를 만든다.

## Done
- [x] Session 20~23 포트폴리오 산출물을 commit/push했다.
  - commit: `b1c2ba4 Document Text2SQL demo and AWS architecture`
- [x] 현재 Text2SQL v1 구조를 확인했다.
  - `agent/text2sql/registry.py`
  - `agent/eval/run_expected_sql.py`
  - `agent/eval/text2sql_questions.yml`
- [x] 현재 dependency 상태를 확인했다.
  - `fastapi`, `pydantic`, `pytest`, `ruff`, `sqlfluff`는 있음.
  - LangChain/OpenAI/Bedrock/sqlglot dependency는 아직 없음.
- [x] v2 design 문서를 추가했다.
  - `docs/analysis/stage6_llm_text2sql_v2_design.md`
- [x] provider-free v2.0 mock harness를 구현했다.
  - `agent/text2sql/validator.py`
  - `agent/text2sql/llm_client.py`
  - `agent/text2sql/generator.py`
  - `tests/unit/test_text2sql_v2.py`
- [x] `POST /query/v2` mock endpoint를 구현했다.
  - request schema: `QueryRequest`
  - response schema: `QueryV2Response`
  - provider: `MockSqlGenerationClient`
- [x] 검증을 실행했다.
  - `uv run ruff check api tests/unit/test_api.py agent/text2sql tests/unit/test_text2sql_v2.py` -> pass
  - `uv run pytest -q` -> `12 passed`
- [x] README, portfolio draft, CLAUDE에 v2 design checkpoint를 반영했다.

## Decisions
- **provider-free mock harness부터 구현한다**: API key와 LLM provider 선택 전에 `validator`, `llm_client` interface, `generator` boundary를 먼저 만든다.
- **v1 registry를 제거하지 않는다**: v1 exact-match는 safe fallback이며, expected-SQL eval은 v2 regression baseline이다.
- **`/query/v2`를 먼저 둔다**: v2가 안정되기 전에는 기존 `/query` behavior를 바꾸지 않는다.
- **allowlisted schema부터 시작한다**: `ai_native.ai_campaign_roi_summary`, `marts.mart_campaign_roas_prediction_monitor`, `ai_native.ai_creator_sponsored_summary`만 v2 schema scope에 둔다.

## Files changed
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — v2 design, validator requirements, prompt contract, eval plan, implementation phases
- `agent/text2sql/validator.py` — allowlisted SELECT/WITH SQL validator
- `agent/text2sql/llm_client.py` — provider interface and mock SQL generation client
- `agent/text2sql/generator.py` — v2 generated SQL execution boundary
- `tests/unit/test_text2sql_v2.py` — validator and mock generator tests
- `api/main.py` — `POST /query/v2` endpoint
- `api/schemas.py` — `QueryV2Response`
- `tests/unit/test_api.py` — `/query/v2` API tests
- `README.md` — v2 design link and Phase row
- `docs/portfolio_draft.md` — v2 design portfolio checklist item
- `CLAUDE.md` — current Phase and session summary update
- `docs/session_log/2026-07-04_session-24_llm-text2sql-v2-design.md` — current handoff
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — v2 design metric append

## Concepts taught
- **LLM SQL generation boundary** — LLM은 SQL 후보를 만들 수 있지만, 실행 권한은 validator와 executor가 통제한다.
- **Regression baseline** — v1 expected-SQL registry는 v2가 더 똑똑해졌는지, 더 위험해졌는지 비교하는 기준선이다.
- **Mock harness** — 외부 provider/API key 없이 인터페이스와 guardrail을 먼저 검증하는 구현 단계다.

## Portfolio assets added
- `docs/analysis/stage6_llm_text2sql_v2_design.md`
- Provider-free v2.0 mock harness modules, `/query/v2` endpoint, and tests

## Open questions
- v2 provider를 OpenAI, Bedrock, 또는 local mock first로 어디까지 가져갈지 결정한다.
- `sqlglot` dependency를 validator 단계에 추가할지, initial regex validator를 유지할지 결정한다.
- v2 eval runner를 먼저 만들지, real provider integration 설계를 먼저 할지 결정한다.

## Metrics
- `uv run ruff check api tests/unit/test_api.py agent/text2sql tests/unit/test_text2sql_v2.py` -> pass
- `uv run pytest -q` -> `12 passed`

## Next session — start here
1. Inspect v2 design:
   ```bash
   sed -n '1,240p' docs/analysis/stage6_llm_text2sql_v2_design.md
   ```
2. Choose next implementation step:
   - `agent/eval/run_text2sql_v2_eval.py`
   - or real provider integration design
3. Keep `/query` v1 unchanged until `/query/v2` is tested.
