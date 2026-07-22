# AdInsight Agent

[![CI](https://github.com/Y-E-O-N/adinsight-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Y-E-O-N/adinsight-agent/actions/workflows/ci.yml)

> A solo data engineering portfolio project that connects influencer campaign data to payment conversion, campaign ROI, ROAS prediction, Superset monitoring, and guarded Text2SQL APIs.

AdInsight is a local analytics platform built around Instagram collection data and synthetic payment events. From April 2026 to July 2026, I designed, implemented, validated, and documented the full workflow end to end: `Airflow ingestion -> dbt semantic marts -> ROAS model artifact -> FastAPI serving -> Text2SQL gateway/eval -> portfolio evidence`.

![AdInsight architecture](docs/images/00_architecture.svg)

## TL;DR

| Area | Summary |
|---|---|
| Problem | Influencer ad performance data is fragmented across post engagement, campaign attribution, payment conversion, and ROAS metrics. |
| Solution | A reproducible local platform using Airflow, Postgres, dbt, Superset, FastAPI, and a Text2SQL gateway. |
| Ownership | Solo project covering planning, data modeling, ingestion, transformation, serving, evaluation, CI, and documentation. |
| Differentiator | Immutable raw layer, idempotent ingestion, layered dbt marts, synthetic payment benchmark, ROAS artifact serving, SQL validation, provider fallback, and CI. |
| Boundary | Payment and ROAS labels are synthetic benchmark data. Model results show the evaluation and serving pattern, not production forecasting accuracy. |

## Key Results

| Area | Result |
|---|---|
| Ingestion/load run | Collected `1,725` items and inserted `1,410` new rows in one daily adaptive run. |
| Synthetic payment benchmark | Generated `498` payment events with net payment KRW `6,329,923.59`. |
| Campaign ROI mart | Built `30` campaign-level rows with max ROAS `0.5969`. |
| ROAS prediction monitor | Evaluated `25` synthetic labeled rows with MAE `0.0799` and bias `0.0000`. |
| ROAS model comparison | Improved from baseline MAE `0.0892` to linear model MAE `0.0474`. |
| Deterministic Text2SQL baseline | Passed the curated expected-SQL registry at `24/24`. |
| External Text2SQL eval | OpenAI passed `24/24` answerable questions and `14/14` safety questions; Gemini passed `24/24` and `12/14`. |
| Provider cost scope | Gemini `$0.064098` vs OpenAI `$0.103027` over the same 38-case eval scope. |
| Quality gate | Documented `ruff` pass, `pytest 82 passed`, and `git diff --check` pass. |

## Demo Assets

| Asset | Link |
|---|---|
| Korean README | [README.md](README.md) |
| Portfolio one-pager | [docs/portfolio_one_pager.md](docs/portfolio_one_pager.md) |
| Text2SQL demo GIF | [docs/images/06_text2sql_demo.gif](docs/images/06_text2sql_demo.gif) |
| Demo evidence | [docs/analysis/stage6_text2sql_demo_evidence.md](docs/analysis/stage6_text2sql_demo_evidence.md) |
| 3-5 minute demo script | [docs/demo_script_3min.md](docs/demo_script_3min.md) |
| API examples | [docs/api/query_v2_request_response_examples.md](docs/api/query_v2_request_response_examples.md) |
| Interview flashcards | [docs/interview_flashcards.md](docs/interview_flashcards.md) |
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

## Data Platform

The dbt design keeps raw inputs immutable and moves calculations through explicit layers.

```text
raw
  -> staging
  -> intermediate
  -> marts
  -> features
  -> ai_native
```

Representative assets:

- dbt lineage: [docs/images/03_dbt_lineage.png](docs/images/03_dbt_lineage.png)
- Creator review dashboard: [docs/images/phase3_creator_review_table.jpg](docs/images/phase3_creator_review_table.jpg)
- Campaign ROAS monitor: [docs/images/05_campaign_roas_prediction_monitor.png](docs/images/05_campaign_roas_prediction_monitor.png)
- Superset exports: [dashboards/superset_exports](dashboards/superset_exports)

## ROAS Prediction Serving

The current training set has 25 labeled synthetic campaign rows, so the project uses a small and defensible benchmark setup. The selected model is a NumPy linear regression artifact, served by FastAPI without request-time fitting.

| Candidate | MAE | RMSE |
|---|---:|---:|
| objective mean baseline | `0.0892` | `0.1349` |
| linear_regression_numpy_v1 | `0.0474` | `0.0577` |

```bash
curl -s -X POST http://127.0.0.1:8000/predict/campaign-roas \
  -H 'Content-Type: application/json' \
  -d '{"campaign_id":"camp_000029"}'
```

## Text2SQL BI Agent

AdInsight keeps deterministic and generated-SQL paths separate.

| Path | Purpose | Safety boundary |
|---|---|---|
| `/query` | deterministic baseline using curated expected SQL | exact-match registry, reviewed SELECT only |
| `/query/v2` | generated-SQL serving boundary | provider contract, SQL validator, statement timeout, audit log, fallback |

The v2 gateway supports `mock`, `ollama`, `openai`, `gemini`, and `dual` backends. The demo path uses Gemini first, OpenAI fallback, and deterministic registry final fallback.

`/query/v2` exposes request-level `provider_summary` fields:

- final provider and model
- estimated cost
- provider elapsed time
- cached input ratio
- fallback status and reason
- attempt providers

Documented external-provider result:

| Provider | Answerable questions | Safety questions | Estimated cost | Provider elapsed |
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

Basic smoke:

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

## Current Status

| Area | Status |
|---|---|
| Local data platform | Implemented |
| Campaign ROI mart | Implemented |
| Superset monitor | Implemented |
| ROAS benchmark model + artifact serving | Implemented |
| Deterministic Text2SQL v1 | Implemented |
| Generated-SQL v2 gateway/eval/fallback | Implemented |
| GitHub Actions CI | Implemented |
| AWS IaC | Skeleton boundary only |
| Load testing / locust | Not implemented |
| Query optimization before/after study | Not implemented |
| Weekly LLM report DAG | Not implemented |

## Known Limitations

- Payment and ROAS labels are synthetic benchmark data, not real advertiser results.
- The ROAS model uses 25 labeled synthetic campaign rows, so model generalization is intentionally not overclaimed.
- External provider cost and latency are measured from saved eval/smoke runs and can drift when provider pricing or model behavior changes.
- `/query/v2` validates and constrains generated SQL, but production use would need authentication, rate limiting, tenant boundaries, and larger repeated traffic measurements.
- AWS docs describe the target mapping and boundaries; this repository is currently a local Docker Compose implementation.

## Documentation Map

| Topic | Link |
|---|---|
| Portfolio source | [docs/portfolio_draft.md](docs/portfolio_draft.md) |
| Portfolio one-pager | [docs/portfolio_one_pager.md](docs/portfolio_one_pager.md) |
| Text2SQL v2 design | [docs/analysis/stage6_llm_text2sql_v2_design.md](docs/analysis/stage6_llm_text2sql_v2_design.md) |
| Text2SQL eval report | [docs/analysis/stage6_text2sql_after_fixes_eval_report.md](docs/analysis/stage6_text2sql_after_fixes_eval_report.md) |
| Failure cases | [docs/analysis/stage6_text2sql_v2_failure_cases.md](docs/analysis/stage6_text2sql_v2_failure_cases.md) |
| AWS architecture | [docs/architecture/aws_target_architecture.md](docs/architecture/aws_target_architecture.md) |
| Interview flashcards | [docs/interview_flashcards.md](docs/interview_flashcards.md) |
| Resume bullets | [docs/resume_bullets.md](docs/resume_bullets.md) |

## License

MIT. Secrets are expected to live in `.env` only and must not be committed.
