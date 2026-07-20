# AdInsight Agent

[![CI](https://github.com/Y-E-O-N/adinsight-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Y-E-O-N/adinsight-agent/actions/workflows/ci.yml)

> 인플루언서 광고 집행 데이터를 결제 전환, 캠페인 ROI, ROAS 예측, Superset 모니터링, guarded Text2SQL API까지 연결한 데이터 엔지니어링 포트폴리오 프로젝트입니다.

[English README](README.en.md)

AdInsight는 Instagram 수집 데이터와 합성 결제 이벤트를 결합해 캠페인 성과를 분석하는 로컬 데이터 플랫폼입니다. 핵심 목표는 단순 대시보드가 아니라 `Airflow ingestion -> dbt semantic marts -> ROAS model artifact -> FastAPI serving -> Text2SQL gateway/eval -> portfolio evidence` 흐름을 끝까지 보여주는 것입니다.

![AdInsight architecture](docs/images/00_architecture.svg)

## TL;DR

| 구분 | 내용 |
|---|---|
| 문제 | 인플루언서 광고 성과는 게시물 반응, 캠페인 attribution, 결제 전환, ROAS 지표가 흩어져 있어 분석과 의사결정이 느립니다. |
| 해결 | Airflow, Postgres, dbt, Superset, FastAPI, Text2SQL gateway를 로컬에서 연결해 재현 가능한 분석 플랫폼을 구성했습니다. |
| 차별점 | raw 보존, idempotent 적재, dbt layered mart, synthetic payment benchmark, ROAS artifact serving, SQL validator, provider fallback, CI를 함께 다룹니다. |
| 한계 | 결제 데이터와 ROAS label은 합성 benchmark입니다. 모델 성능은 운영 일반화 주장이 아니라 평가/서빙 패턴 증거로 해석해야 합니다. |

## Key Results

| 영역 | 결과 |
|---|---:|
| Apify daily adaptive run | `items_collected_total=1725`, `inserted_total=1410` |
| Synthetic payment benchmark | `498` payment events, net payment KRW `6,329,923.59` |
| Campaign ROI mart | `30` campaign rows, max ROAS `0.5969` |
| ROAS prediction monitor | `25` rows, MAE `0.0799`, bias `0.0000` |
| ROAS model comparison | baseline MAE `0.0892` -> linear model MAE `0.0474` |
| deterministic Text2SQL baseline | expected-SQL registry `24/24 PASS` |
| external Text2SQL eval | OpenAI `24/24` positive + `14/14` negative, Gemini `24/24` positive + `12/14` negative |
| provider cost scope | Gemini `$0.064098` vs OpenAI `$0.103027` over the same 38-case eval scope |
| quality gate | latest documented gate: `ruff` pass, `pytest 82 passed`, `git diff --check` pass |

## Demo Assets

| 자산 | 위치 |
|---|---|
| Text2SQL demo GIF | [docs/images/06_text2sql_demo.gif](docs/images/06_text2sql_demo.gif) |
| Demo evidence | [docs/analysis/stage6_text2sql_demo_evidence.md](docs/analysis/stage6_text2sql_demo_evidence.md) |
| Korean company submission portfolio | [docs/korean_company_portfolio_submission.md](docs/korean_company_portfolio_submission.md) |
| Korean submission HTML export | [docs/adinsight_portfolio_submission_ko.html](docs/adinsight_portfolio_submission_ko.html) |
| Korean submission DOCX export | [docs/adinsight_portfolio_submission_ko.docx](docs/adinsight_portfolio_submission_ko.docx) |
| Korean job application snippets | [docs/korean_job_application_snippets.md](docs/korean_job_application_snippets.md) |
| Portfolio one-pager | [docs/portfolio_one_pager.md](docs/portfolio_one_pager.md) |
| 3-5 minute demo script | [docs/demo_script_3min.md](docs/demo_script_3min.md) |
| API examples | [docs/api/query_v2_request_response_examples.md](docs/api/query_v2_request_response_examples.md) |
| Interview talking points | [docs/interview_talking_points.md](docs/interview_talking_points.md) |
| Interview flashcards | [docs/interview_flashcards.md](docs/interview_flashcards.md) |
| Selected Korean resume bullets | [docs/resume_selected_bullets_ko.md](docs/resume_selected_bullets_ko.md) |
| Resume bullets | [docs/resume_bullets.md](docs/resume_bullets.md) |

## Architecture

```text
[Ingestion]
  Airflow DAGs + Apify collector + synthetic payment generator
      |
      v
[Storage]
  Postgres schemas: raw -> staging -> intermediate -> marts -> features -> ai_native
      |
      +--> Superset dashboards
      +--> ROAS model comparison and scoring
      +--> FastAPI /predict/campaign-roas
      +--> FastAPI /query and /query/v2
              |
              v
          Text2SQL gateway: mock | Ollama | OpenAI | Gemini | dual fallback
```

| Layer | Local implementation | AWS target mapping |
|---|---|---|
| Orchestration | Airflow in Docker Compose | MWAA |
| Storage/serving DB | PostgreSQL 16 | RDS/Aurora PostgreSQL or Redshift |
| Transform | dbt-postgres | dbt on managed warehouse |
| BI | Superset | QuickSight or managed Superset |
| API serving | FastAPI | ECS Fargate + ALB |
| Model artifact | local JSON artifact | S3 + model registry |
| Text2SQL gateway | FastAPI gateway | ECS/Lambda + Bedrock/OpenAI/Gemini/internal gateway |
| Logs/metrics | JSONL + metrics docs | CloudWatch Logs + S3 |

Detailed docs:

- [AWS target architecture](docs/architecture/aws_target_architecture.md)
- [Text2SQL gateway architecture](docs/architecture/text2sql_gateway_architecture.md)
- [Dual-provider fallback ADR](docs/adr/004-text2sql-dual-provider-fallback.md)

## Data Platform

The dbt model design keeps raw data immutable and moves calculations through explicit layers.

```text
raw
  stg_ig_posts
  stg_syn_campaigns
  stg_syn_post_campaign_attributions
  stg_syn_payment_events
    |
    v
intermediate
  int_ig_post_source_quality
  int_ig_sponsored_candidates
  int_ig_owner_activity
  int_campaign_payment_performance
    |
    v
marts / features / ai_native
  mart_creator_sponsored_summary
  mart_campaign_roi_summary
  mart_campaign_roas_prediction_monitor
  feature_campaign_roas_training_set
  feature_campaign_roas_scoring_set
  ai_creator_sponsored_summary
  ai_campaign_roi_summary
```

Representative evidence:

- dbt lineage screenshot: [docs/images/03_dbt_lineage.png](docs/images/03_dbt_lineage.png)
- Creator review dashboard screenshot: [docs/images/phase3_creator_review_table.jpg](docs/images/phase3_creator_review_table.jpg)
- Campaign ROAS monitor screenshot: [docs/images/05_campaign_roas_prediction_monitor.png](docs/images/05_campaign_roas_prediction_monitor.png)
- Superset exports: [dashboards/superset_exports](dashboards/superset_exports)

## ROAS Prediction Serving

The project compares small, defensible benchmark models before serving predictions. With only 25 labeled synthetic campaign rows, the selected model is a NumPy linear regression artifact rather than a heavier boosting model.

| Candidate | MAE | RMSE |
|---|---:|---:|
| objective mean baseline | `0.0892` | `0.1349` |
| linear_regression_numpy_v1 | `0.0474` | `0.0577` |

The FastAPI endpoint loads [agent/model_artifacts/campaign_roas_linear_v1.json](agent/model_artifacts/campaign_roas_linear_v1.json) instead of fitting a model at request time.

```bash
curl -s -X POST http://127.0.0.1:8000/predict/campaign-roas \
  -H 'Content-Type: application/json' \
  -d '{"campaign_id":"camp_000029"}'
```

Example response:

```json
{
  "campaign_id": "camp_000029",
  "model_name": "linear_regression_numpy_v1",
  "predicted_roas": 0.597425,
  "latency_ms": 23.495,
  "training_rows_used": 25,
  "feature_source": "features.feature_campaign_roas_scoring_set",
  "model_artifact_path": "agent/model_artifacts/campaign_roas_linear_v1.json",
  "known_limitation": "Fitted on 25 synthetic labeled campaign rows; benchmark artifact only."
}
```

## Text2SQL BI Agent

AdInsight keeps two Text2SQL paths separate.

| Path | Purpose | Safety boundary |
|---|---|---|
| `/query` | deterministic baseline using curated expected SQL | exact-match registry, reviewed SELECT only |
| `/query/v2` | generated-SQL serving boundary | provider contract, SQL validator, statement timeout, audit log, fallback |

The v2 gateway supports `mock`, `ollama`, `openai`, `gemini`, and `dual` backends. The product demo path uses Gemini primary, OpenAI fallback, and deterministic registry final fallback.

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

Request-level observability is exposed through `provider_summary`:

- final provider and model
- estimated cost
- provider elapsed time
- cached input ratio
- fallback status
- fallback reason
- attempt providers

Latest documented external-provider result:

| Provider | Positive | Negative | Estimated cost | Provider elapsed |
|---|---:|---:|---:|---:|
| OpenAI `gpt-5.4-mini-2026-03-17` | `24/24` | `14/14` | `$0.103027` | `124.799s` |
| Gemini `gemini-3.1-flash-lite` | `24/24` | `12/14` | `$0.064098` | `145.363s` |

## Quickstart

Requirements:

- Docker Desktop
- Python 3.11
- [uv](https://docs.astral.sh/uv/)

```bash
cp .env.example .env
uv sync
time make up
make ps
make superset-init
```

Service URLs:

| Service | URL |
|---|---|
| Airflow | <http://localhost:8081> |
| Superset | <http://localhost:8088> |
| Flower | <http://localhost:5555> |
| FastAPI | <http://localhost:8000> |
| Postgres | `localhost:5432` |

Basic smoke commands:

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'

curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

Gateway smoke:

```bash
uv run uvicorn text2sql_gateway.main:app --host 0.0.0.0 --port 8010

curl -s -X POST http://127.0.0.1:8010/text2sql/generate \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?","schema_context":"Allowed tables: ai_native.ai_campaign_roi_summary"}'
```

## Project Structure

```text
adinsight-agent/
├── dags/                  # Airflow DAGs
├── dbt/                   # dbt-postgres models and tests
├── data_generation/       # Apify/synthetic data helpers
├── agent/                 # ROAS eval and Text2SQL modules
├── api/                   # FastAPI serving endpoints
├── text2sql_gateway/      # Provider-specific Text2SQL gateway
├── dashboards/            # Superset scripts and exports
├── metrics/               # run metrics and portfolio metrics
├── docs/                  # architecture, ADRs, demo, interview, session logs
├── tests/                 # unit/integration tests
└── infra/                 # Docker images and AWS skeleton notes
```

## JD Alignment

| Data engineering signal | Evidence |
|---|---|
| Workflow orchestration | Airflow collection, backfill, and daily scoring DAGs in [dags](dags) |
| Warehouse modeling | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` layers in [dbt/models](dbt/models) |
| Data quality | dbt tests, expected-SQL eval, negative Text2SQL eval, CI |
| Serving/API | FastAPI `/health`, `/predict/campaign-roas`, `/query`, `/query/v2` in [api](api) |
| AI/LLM boundary | SQL validator, provider gateway, audit log, fallback orchestration in [agent/text2sql](agent/text2sql) and [text2sql_gateway](text2sql_gateway) |
| BI evidence | Superset screenshots and exports in [docs/images](docs/images) and [dashboards/superset_exports](dashboards/superset_exports) |
| Cloud readiness | AWS target mapping in [docs/architecture/aws_target_architecture.md](docs/architecture/aws_target_architecture.md) |

## Current Status

| Area | Status |
|---|---|
| Local data platform | Implemented |
| Campaign ROI mart | Implemented |
| Superset monitor | Implemented |
| ROAS benchmark model + artifact serving | Implemented |
| deterministic Text2SQL v1 | Implemented |
| generated-SQL v2 gateway/eval/fallback | Implemented |
| GitHub Actions CI | Implemented |
| AWS IaC | Skeleton boundary only |
| Load testing / locust | Not implemented |
| Query optimization before/after study | Not implemented |
| Weekly LLM report DAG | Not implemented |

## Known Limitations

- Payment and ROAS labels are synthetic. They are useful for pipeline, modeling, serving, and evaluation patterns, not for real advertiser performance claims.
- The ROAS model uses 25 labeled synthetic campaign rows, so model generalization is intentionally not overclaimed.
- External provider cost and latency are measured from saved eval/smoke runs and can drift when provider pricing or model behavior changes.
- `/query/v2` validates and constrains generated SQL, but broad production use would need authentication, rate limiting, tenant boundaries, and larger repeated traffic measurements.
- AWS docs describe the target mapping and boundaries; this repository is currently a local Docker Compose implementation.

## Documentation Map

| Topic | Link |
|---|---|
| Portfolio draft | [docs/portfolio_draft.md](docs/portfolio_draft.md) |
| Korean company submission portfolio | [docs/korean_company_portfolio_submission.md](docs/korean_company_portfolio_submission.md) |
| Korean submission HTML export | [docs/adinsight_portfolio_submission_ko.html](docs/adinsight_portfolio_submission_ko.html) |
| Korean submission DOCX export | [docs/adinsight_portfolio_submission_ko.docx](docs/adinsight_portfolio_submission_ko.docx) |
| Korean job application snippets | [docs/korean_job_application_snippets.md](docs/korean_job_application_snippets.md) |
| Portfolio one-pager | [docs/portfolio_one_pager.md](docs/portfolio_one_pager.md) |
| English README | [README.en.md](README.en.md) |
| Project blueprint | [docs/adinsight_project_blueprint.md](docs/adinsight_project_blueprint.md) |
| Session logs | [docs/session_log](docs/session_log) |
| Text2SQL v2 design | [docs/analysis/stage6_llm_text2sql_v2_design.md](docs/analysis/stage6_llm_text2sql_v2_design.md) |
| Text2SQL eval report | [docs/analysis/stage6_text2sql_after_fixes_eval_report.md](docs/analysis/stage6_text2sql_after_fixes_eval_report.md) |
| Failure cases | [docs/analysis/stage6_text2sql_v2_failure_cases.md](docs/analysis/stage6_text2sql_v2_failure_cases.md) |
| AWS architecture | [docs/architecture/aws_target_architecture.md](docs/architecture/aws_target_architecture.md) |
| Interview flashcards | [docs/interview_flashcards.md](docs/interview_flashcards.md) |
| Selected Korean resume bullets | [docs/resume_selected_bullets_ko.md](docs/resume_selected_bullets_ko.md) |
| Resume bullets | [docs/resume_bullets.md](docs/resume_bullets.md) |

## License

MIT. Secrets are expected to live in `.env` only and must not be committed.
