# AdInsight 3-5 Minute Demo Script

## 0:00-0:30 — Problem

"AdInsight is a portfolio data platform for influencer advertising analytics. It connects Instagram collection, campaign attribution, synthetic payment events, ROAS prediction, Superset monitoring, and Text2SQL serving."

Key point:

- This is not a dashboard-only project.
- The same modeled data is consumed by BI, ML, and API workflows.

## 0:30-1:15 — Data Platform Flow

Show:

- Airflow DAGs for collection and daily scoring
- dbt layers: `raw -> staging -> intermediate -> marts -> features -> ai_native`
- Superset campaign ROAS prediction monitor

Talking point:

"I separated raw preservation from analytics layers. The ai_native layer exists because Text2SQL works better when model grain, synonyms, and example questions are explicit."

## 1:15-2:00 — ROAS Prediction

Show:

```bash
curl -s -X POST http://127.0.0.1:8000/predict/campaign-roas \
  -H 'Content-Type: application/json' \
  -d '{"campaign_id":"camp_000029"}'
```

Talking point:

"The serving endpoint loads a saved linear model artifact instead of refitting at request time. The current best benchmark is `linear_regression_numpy_v1`, with leave-one-out MAE `0.0474` on 25 labeled synthetic campaign rows."

Limitation:

"This is a small synthetic benchmark, so I document it as a serving and evaluation pattern, not a production-quality forecasting claim."

## 2:00-3:00 — Deterministic Text2SQL v1

Show:

```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

Talking point:

"The v1 endpoint is deterministic. It matches questions against `agent/eval/text2sql_questions.yml` and only executes reviewed SELECT SQL. That gives a stable baseline: 18 out of 18 expected-SQL questions pass."

## 3:00-4:00 — Generated Text2SQL v2 Boundary

Show:

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

Talking point:

"v2 is where generated SQL will live. Today it uses a provider-free mock by default, but the boundary is realistic: provider factory, SQL validator, statement timeout, audit log, error handling, and eval runner."

Current quality numbers:

- v1 deterministic: `18 PASS / 0 FAIL`
- v2 mock: `13 PASS / 5 REFUSED / 0 BLOCKED`
- v2 answerable-only exec accuracy: `1.0`

## 4:00-5:00 — Safety And AWS Mapping

Talking point:

"I do not let generated SQL directly hit arbitrary tables. The validator only allows approved semantic marts, SELECT or WITH statements, and bounded non-aggregate queries. Broad no-LIMIT creator lists are refused until pagination is implemented."

AWS mapping:

- Airflow -> MWAA
- Postgres -> RDS or Aurora PostgreSQL
- dbt artifacts and model artifacts -> S3
- FastAPI -> ECS Fargate behind ALB
- Superset -> QuickSight or managed BI
- logs/metrics -> CloudWatch

Close:

"The project is designed to show the full lifecycle: ingestion, modeling, ML evaluation, serving, BI consumption, Text2SQL guardrails, CI, and portfolio-grade evidence."
