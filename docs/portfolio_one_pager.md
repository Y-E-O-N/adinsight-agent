# AdInsight Agent - 데이터 엔지니어 포트폴리오 원페이지

## 1. Project Summary

AdInsight는 인플루언서 광고 집행 데이터를 결제 전환, campaign ROI, ROAS prediction, Superset monitoring, guarded Text2SQL API까지 연결한 개인 데이터 엔지니어링 프로젝트입니다.

프로젝트 기간은 `2026.04 - 2026.07`이며, 기획, 데이터 모델링, 파이프라인 구현, API serving, Text2SQL 검증, CI, 문서화를 처음부터 끝까지 혼자 진행했습니다. 목적은 단일 기능 데모가 아니라 데이터 엔지니어링 end-to-end 흐름을 증명하는 것입니다.

```text
Airflow ingestion
  -> Postgres raw/staging
  -> dbt intermediate/marts/features/ai_native
  -> Superset dashboard
  -> ROAS model artifact
  -> FastAPI serving
  -> Text2SQL gateway/eval/audit
```

## 2. What I Built

| Area | Implementation |
|---|---|
| Ingestion | Apify 기반 Instagram 수집, raw loader, daily/backfill Airflow DAG를 직접 구현 |
| Modeling | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` layered warehouse 설계 |
| BI | Superset creator review dashboard, campaign ROAS prediction monitor 구성 |
| ML workflow | 합성 결제 attribution 기반 ROAS model comparison, benchmark artifact export |
| Serving | FastAPI `/health`, `/predict/campaign-roas`, `/query`, `/query/v2` 구현 |
| Text2SQL | deterministic expected-SQL baseline, generated-SQL v2 gateway, SQL validator, 안전성 질의 평가 |
| Operations | provider cost/latency/fallback observability, audit JSONL, GitHub Actions CI 구성 |
| Cloud mapping | MWAA, RDS/Aurora, S3, ECS Fargate, ALB, CloudWatch, QuickSight target design 정리 |

## 3. Key Results

| Recruiter-readable result | Evidence |
|---|---|
| 하루 실행 단위의 수집-적재 파이프라인에서 `1,725`건을 수집하고 `1,410`건을 신규 적재했습니다. | Phase 2B daily adaptive run |
| 광고 성과 분석용 mart를 만들고 `30`개 campaign row, 최대 ROAS `0.5969`까지 조회 가능한 분석 테이블을 구성했습니다. | Campaign ROI mart |
| 단순 평균 baseline보다 낮은 오차의 ROAS model artifact를 만들고 API serving까지 연결했습니다. | baseline MAE `0.0892` -> linear MAE `0.0474` |
| 자연어 질의 baseline은 검증된 SQL 기준 `24/24 PASS`로 고정하고, generated SQL은 별도 validator와 안전성 평가로 통제했습니다. | deterministic `/query`, guarded `/query/v2` |
| OpenAI/Gemini provider를 같은 38개 질의로 비교하고 비용, 지연시간, fallback 이유를 request 단위로 관측했습니다. | Gemini `$0.064098`, OpenAI `$0.103027` |
| 코드 품질은 CI에서 `ruff`, `pytest 82 passed`, `git diff --check` 기준으로 관리했습니다. | GitHub Actions quality gate |

## 4. Strongest Engineering Decisions

| Decision | Why it matters |
|---|---|
| Keep raw immutable | Downstream marts can be rebuilt and audited without mutating source records. |
| Use layered dbt models | Business metrics, feature tables, and ai_native marts have explicit grain and ownership. |
| Use simple ROAS model first | With 25 synthetic labeled rows, linear/LOO validation is more defensible than overclaiming a boosting model. |
| Split `/query` and `/query/v2` | deterministic baseline remains stable while generated SQL gets its own validator, timeout, audit, and fallback. |
| Gemini first + OpenAI fallback | Gemini was cheaper in the measured scope; OpenAI was cleaner on safety and faster overall. |

## 5. Demo Flow

1. Show README architecture and Key Results.
2. Show Superset campaign ROAS prediction monitor.
3. Run `/predict/campaign-roas` for `camp_000029`.
4. Run `/query/v2` with `Which campaigns have the highest ROAS?`.
5. Show `provider_summary`: provider, model, cost, latency, fallback status.
6. Explain known limitations and AWS target mapping.

Demo references:

- `docs/images/06_text2sql_demo.gif`
- `docs/demo_script_3min.md`
- `docs/api/query_v2_request_response_examples.md`
- `docs/interview_talking_points.md`

## 6. Claim Boundaries

- Payment and ROAS labels are synthetic benchmark data.
- ROAS model scores demonstrate model comparison and artifact serving, not production forecasting accuracy.
- `/query/v2` is guarded generated SQL with validation and fallback, not arbitrary SQL execution.
- AWS content is a target architecture and skeleton boundary, not a deployed cloud production system.

## 7. Resume-Ready Version

Airflow, PostgreSQL, dbt 기반으로 Instagram 수집 데이터와 합성 결제 이벤트를 `raw -> staging -> intermediate -> marts -> features -> ai_native` 레이어로 모델링하고, Superset dashboard, ROAS prediction artifact serving, FastAPI API, guarded Text2SQL evaluation까지 연결한 개인 데이터 엔지니어링 프로젝트를 처음부터 끝까지 구현했습니다.
