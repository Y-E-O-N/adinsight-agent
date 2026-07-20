# AdInsight Agent - Data Engineering Portfolio One-Pager

## 1. Project Summary

AdInsight는 인플루언서 광고 집행 데이터를 결제 전환, campaign ROI, ROAS prediction, Superset monitoring, guarded Text2SQL API까지 연결한 로컬 데이터 플랫폼입니다.

이 프로젝트의 목적은 단일 기능 데모가 아니라 데이터 엔지니어링 end-to-end 흐름을 증명하는 것입니다.

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
| Ingestion | Apify 기반 Instagram 수집, raw loader, daily/backfill Airflow DAG |
| Modeling | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` layered warehouse |
| BI | Superset creator review dashboard, campaign ROAS prediction monitor |
| ML workflow | synthetic payment attribution 기반 ROAS model comparison and artifact export |
| Serving | FastAPI `/health`, `/predict/campaign-roas`, `/query`, `/query/v2` |
| Text2SQL | deterministic expected-SQL baseline, generated-SQL v2 gateway, SQL validator, negative eval |
| Operations | provider cost/latency/fallback observability, audit JSONL, GitHub Actions CI |
| Cloud mapping | MWAA, RDS/Aurora, S3, ECS Fargate, ALB, CloudWatch, QuickSight target design |

## 3. Key Results

| Metric | Result |
|---|---:|
| Phase 2B daily adaptive run | `items_collected_total=1725`, `inserted_total=1410` |
| Synthetic payment benchmark | `498` payment events, net payment KRW `6,329,923.59` |
| Campaign ROI mart | `30` campaign rows, max ROAS `0.5969` |
| Prediction monitor | `25` rows, MAE `0.0799`, bias `0.0000` |
| ROAS model comparison | baseline MAE `0.0892` -> linear model MAE `0.0474` |
| deterministic Text2SQL baseline | expected-SQL registry `24/24 PASS` |
| OpenAI Text2SQL eval | positive `24/24`, negative `14/14` |
| Gemini Text2SQL eval | positive `24/24`, negative `12/14` |
| Provider cost comparison | Gemini `$0.064098` vs OpenAI `$0.103027` over 38 cases |
| Latest documented quality gate | `ruff` pass, `pytest 82 passed`, `git diff --check` pass |

## 4. Strongest Engineering Decisions

| Decision | Why it matters |
|---|---|
| Keep raw immutable | Downstream marts can be rebuilt and audited without mutating source records. |
| Use layered dbt models | Business metrics, feature tables, and ai_native marts have explicit grain and ownership. |
| Use simple ROAS model first | With 25 synthetic labeled rows, linear/LOO validation is more defensible than overclaiming a boosting model. |
| Split `/query` and `/query/v2` | deterministic baseline remains stable while generated SQL gets its own validator, timeout, audit, and fallback. |
| Gemini primary + OpenAI fallback | Gemini was cheaper in the measured scope; OpenAI was cleaner on safety and faster overall. |

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

Built AdInsight, an end-to-end influencer campaign analytics platform combining Airflow ingestion, dbt semantic marts, Superset dashboards, ROAS prediction artifact serving, FastAPI APIs, and guarded Text2SQL evaluation with OpenAI/Gemini provider fallback, request-level cost observability, and CI quality gates.
