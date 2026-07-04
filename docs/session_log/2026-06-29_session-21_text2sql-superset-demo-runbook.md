# Session 21 — Text2SQL + Superset Demo Runbook (2026-06-29)

**Phase**: Phase 6/7 — deterministic Text2SQL v1 demo asset
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- Session 20 `/query` checkpoint 이후 이어서 Superset dashboard와 자연어 질의 API를 하나의 demo scenario로 연결한다.
- stale한 `CLAUDE.md`, README Phase table, portfolio checklist를 현재 상태에 맞게 갱신한다.
- 다음 세션에서 바로 demo GIF 캡처 또는 AWS architecture 문서로 이어갈 수 있게 만든다.

## Done
- [x] `CLAUDE.md`와 최신 세션 로그를 읽고 현재 Phase를 회복했다.
- [x] `/query` functional commit `848bd27`이 현재 git log에 있음을 확인했다.
- [x] `docs/analysis/stage6_text2sql_superset_demo_runbook.md`를 추가했다.
  - Superset monitor -> `/query` English question -> `/query` Korean question demo 흐름
  - guardrail 설명
  - local vs AWS mapping
  - demo script
  - next GIF capture plan
- [x] README에 demo runbook 링크와 최신 Phase status를 반영했다.
- [x] `docs/portfolio_draft.md`의 Text2SQL demo GIF 항목에 capture plan 링크를 달았다.
- [x] `CLAUDE.md`의 현재 Phase와 직전 세션 요약에 Session 20/21 흐름을 반영했다.

## Decisions
- **데모 연결을 먼저 한다**: AWS target architecture보다 먼저, 이미 만든 `/query`와 Superset monitor를 포트폴리오에서 설명 가능한 흐름으로 묶는다.
- **LLM Agent 완료로 표현하지 않는다**: 현재 `/query`는 deterministic expected-SQL registry v1이므로, README와 CLAUDE 모두 그 한계를 명확히 남긴다.
- **daily Airflow metric append는 보존한다**: `metrics/run_results.jsonl`에 scheduled `campaign_roas_prediction_daily` 3줄이 로컬 수정으로 남아 있다. 자동 실행 산출물이므로 되돌리지 않고 별도 커밋 여부를 판단한다.

## Files changed
- `docs/analysis/stage6_text2sql_superset_demo_runbook.md` — Superset + `/query` demo runbook
- `README.md` — demo runbook link, Phase status update
- `docs/portfolio_draft.md` — Text2SQL demo GIF capture plan link
- `CLAUDE.md` — current Phase, latest Text2SQL API/demo status, next step update
- `docs/session_log/2026-06-26_session-20_deterministic-text2sql-query-api.md` — missing official handoff for `/query` checkpoint
- `docs/session_log/2026-06-29_session-21_text2sql-superset-demo-runbook.md` — current handoff
- `docs/session_log/README.md` — session index update

## Concepts taught
- **Demo runbook** — 기능이 있다는 사실보다, 면접자가 따라 볼 수 있는 순서와 증거를 문서화하는 자산이다.
- **Self-service analytics story** — Superset은 반복 운영 화면, `/query`는 같은 mart를 자연어로 조회하는 API 역할을 맡는다.
- **AWS mapping** — 로컬 FastAPI/Postgres/Superset 구조를 ECS or Lambda container, Aurora or Redshift, QuickSight로 대응해 설명한다.

## Portfolio assets added
- Demo runbook:
  - `docs/analysis/stage6_text2sql_superset_demo_runbook.md`
- Next capture target:
  - `docs/images/06_text2sql_demo.gif`

## Open questions
- `metrics/run_results.jsonl`의 scheduled daily scoring append 3줄을 커밋할지 결정한다.
- Text2SQL demo GIF를 실제로 캡처할지, 먼저 AWS target architecture 문서를 만들지 결정한다.
- LLM SQL generation v2는 demo capture 이후 붙이는 것이 자연스럽다.

## Metrics
- No code tests required; documentation-only checkpoint.
- Verified current git history includes `848bd27 Add deterministic Text2SQL query API`.
- Verified local dirty state includes `metrics/run_results.jsonl` scheduled Airflow metric appends.

## Next session — start here
1. Inspect current state:
   ```bash
   git status --short --branch
   git diff -- metrics/run_results.jsonl
   ```
2. If demo capture is next:
   - Open Superset dashboard `AdInsight Campaign ROAS Prediction Monitor`.
   - Start FastAPI:
     ```bash
     set -a; source .env; set +a; POSTGRES_HOST=localhost uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
     ```
   - Run the two `/query` curls in `docs/analysis/stage6_text2sql_superset_demo_runbook.md`.
   - Capture `docs/images/06_text2sql_demo.gif`.
3. If architecture is next:
   - Draft AWS target architecture around QuickSight, ECS/Fargate or Lambda container, Aurora/Redshift, S3 model/eval artifacts, CloudWatch metrics.
