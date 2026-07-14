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

"v2 is the guarded generated-SQL boundary. The API can run with a provider-free mock, or it can call an external Text2SQL gateway backed by Gemini or OpenAI. Regardless of provider, the generated SQL is validated, bounded, timed out, executed, and audited."

Show in the response:

- `mode`: `llm_generated_sql_v2_mock` or `llm_generated_sql_v2_http_json`
- `sql`: generated and validated SQL
- `row_count`: returned row count
- `provider_summary.final_provider`: `gemini`, `openai`, or `deterministic_registry`
- `provider_summary.estimated_cost_usd`
- `provider_summary.provider_elapsed_ms`
- `provider_summary.cached_input_ratio`
- `provider_summary.fallback_used`
- `provider_summary.fallback_reason`

Current quality numbers:

- expected-SQL deterministic baseline: `24/24 PASS`
- OpenAI latest positive/negative: `38/38 PASS`, estimated cost `$0.103027`
- Gemini latest positive/negative: `36/38 PASS`, estimated cost `$0.064098`
- Gemini was about 37.8% cheaper; OpenAI was about 16.5% faster by total provider elapsed time.
- Dual-provider live smoke: positive request completed on Gemini without fallback; safety refusal triggered Gemini -> OpenAI fallback with `fallback_reason=primary_content_safety_refusal`.

## 4:00-5:00 — Safety And AWS Mapping

Talking point:

"I do not let generated SQL directly hit arbitrary tables. The validator only allows approved semantic marts, SELECT or WITH statements, and bounded non-aggregate queries. `/query/v2` also records the provider, model, cost, latency, cache ratio, and fallback status so that the demo is not only a model-quality claim; it is an observable serving boundary."

AWS mapping:

- Airflow -> MWAA
- Postgres -> RDS or Aurora PostgreSQL
- dbt artifacts and model artifacts -> S3
- FastAPI -> ECS Fargate behind ALB
- Superset -> QuickSight or managed BI
- logs/metrics -> CloudWatch
- Text2SQL gateway -> Bedrock, OpenAI, Gemini, or an internal model gateway behind a private endpoint

Close:

"The project is designed to show the full lifecycle: ingestion, modeling, ML evaluation, serving, BI consumption, Text2SQL guardrails, CI, and portfolio-grade evidence."
