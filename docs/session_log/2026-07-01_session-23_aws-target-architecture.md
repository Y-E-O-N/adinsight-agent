# Session 23 — AWS Target Architecture (2026-07-01)

**Phase**: Phase 8B — AWS target architecture + IaC skeleton
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- `/predict`, `/query`, Superset/Text2SQL demo asset 이후 로컬 구현을 AWS target architecture로 매핑한다.
- 비용이 드는 실제 배포 전, 면접에서 설명 가능한 service boundary와 migration plan을 문서화한다.
- IaC를 바로 적용하지 않고, 먼저 `infra/aws/` skeleton과 environment contract를 만든다.

## Done
- [x] 최신 `CLAUDE.md`와 Session 22 handoff를 읽고 현재 상태를 회복했다.
- [x] 기존 cloud tooling strategy를 확인했다.
  - `docs/analysis/stage5_jd_cloud_tooling_strategy.md`
- [x] AWS target architecture 문서를 추가했다.
  - `docs/architecture/aws_target_architecture.md`
- [x] AWS infra skeleton README를 추가했다.
  - `infra/aws/README.md`
- [x] README Phase table에 AWS target architecture checkpoint를 반영했다.
- [x] portfolio checklist에 AWS target architecture asset을 추가했다.
- [x] `CLAUDE.md` 현재 Phase에 AWS architecture 결과를 반영했다.

## Decisions
- **실제 배포보다 architecture boundary를 먼저 문서화한다**: MWAA, RDS/Redshift, S3, ECS Fargate, ALB, QuickSight, CloudWatch mapping을 먼저 고정해 cloud 이해도를 보여준다.
- **RDS PostgreSQL을 first target으로 둔다**: 현재 SQL 호환성과 비용을 고려하면 RDS가 현실적이고, Redshift는 데이터 규모가 커진 뒤 analytics-heavy mart 확장안으로 둔다.
- **SageMaker endpoint는 보류한다**: 현재 model artifact는 25 synthetic labeled rows 기반 benchmark이므로, ECS/Fargate FastAPI serving이 더 정직한 첫 cloud slice다.
- **Streaming은 future extension으로 둔다**: campaign ROAS monitoring은 daily batch가 자연스럽고, Kinesis/MSK는 payment-event ingestion 확장안으로 문서화한다.

## Files changed
- `docs/architecture/aws_target_architecture.md` — local-to-AWS mapping, logical architecture, flows, security, observability, cost-control, migration phases
- `infra/aws/README.md` — IaC skeleton boundary, target modules, env contract, first deployable slice
- `README.md` — architecture/skeleton links and Phase table update
- `docs/portfolio_draft.md` — AWS target architecture checklist item
- `CLAUDE.md` — current Phase update
- `docs/session_log/2026-07-01_session-23_aws-target-architecture.md` — current handoff
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — architecture documentation metric append

## Concepts taught
- **Target architecture** — 지금 로컬 구현을 운영 환경으로 옮길 때의 service boundary, data flow, security, observability를 먼저 고정하는 설계 문서다.
- **Cost-controlled cloud migration** — 포트폴리오에서는 무조건 managed service를 켜기보다, 비용 높은 서비스를 언제까지 보류할지 설명하는 것이 중요하다.
- **Serving boundary** — Airflow/MWAA batch workflow와 FastAPI/ECS request serving을 분리해야 운영 책임이 명확해진다.

## Portfolio assets added
- `docs/architecture/aws_target_architecture.md`
- `infra/aws/README.md`

## Open questions
- 이번 문서/GIF/metrics 변경을 하나의 checkpoint commit으로 묶을지 결정한다.
- 다음 구현은 LLM SQL generation v2 design 또는 API hardening/CI 중 하나가 자연스럽다.

## Metrics
- Architecture doc: `docs/architecture/aws_target_architecture.md`
- IaC skeleton doc: `infra/aws/README.md`
- No code tests required; documentation-only checkpoint.

## Next session — start here
1. Check dirty state:
   ```bash
   git status --short --branch
   git diff --stat
   ```
2. Decide whether to commit all pending portfolio/documentation artifacts.
3. Recommended next task:
   - LLM SQL generation v2 design guarded by expected-SQL evaluator
   - or API hardening/CI around `/predict`, `/query`
