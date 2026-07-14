# AdInsight Resume Bullets

## Data Platform / Analytics Engineering

- Built an end-to-end influencer campaign analytics platform with Airflow, Postgres, dbt, Superset, and FastAPI, modeling raw Instagram collection and synthetic payment events into campaign ROI, ROAS prediction, and Text2SQL-ready semantic marts.
- Designed a layered dbt warehouse (`raw -> staging -> intermediate -> marts -> features -> ai_native`) with immutable raw inputs, idempotent transformations, semantic metadata, and portfolio evidence captured through dbt tests, screenshots, and run metrics.
- Implemented campaign payment and ROI marts from synthetic attribution/payment events, producing campaign-grain ROAS summaries and reusable feature tables for model training and daily scoring.

## ML / ROAS Prediction

- Built a ROAS model comparison runner using leave-one-out validation across baseline, linear, ridge, and KNN candidates; improved MAE from objective-mean baseline `0.0892` to `0.0474` with `linear_regression_numpy_v1`.
- Served campaign ROAS predictions through FastAPI using a saved model artifact instead of request-time fitting, exposing reproducible response metadata such as model name, training rows, feature source, and scoring snapshot date.

## Text2SQL / AI-Native BI

- Implemented deterministic Text2SQL v1 by matching natural-language questions to a curated expected-SQL registry, returning SQL, rows, answer text, and latency while keeping execution restricted to reviewed SELECT statements.
- Built a generated-SQL Text2SQL v2 boundary with provider factory, SQL validator, statement timeout, best-effort audit logging, provider usage/cost tracking, and explicit API error handling for success, refused, blocked, and unexpected-error paths.
- Expanded Text2SQL evaluation to 24 positive questions and 14 negative/content-safety questions, with latest external-provider runs reaching OpenAI `24/24` positive and `14/14` negative pass, and Gemini `24/24` positive and `12/14` negative pass.
- Added request-level `provider_summary` observability for `/query/v2`, exposing final provider, model, estimated cost, provider latency, cached input ratio, and fallback status; measured Gemini at `$0.064098` vs OpenAI at `$0.103027` over the same 38-case positive/negative scope.
- Documented Text2SQL failure cases where broad no-LIMIT generated SQL is refused or blocked, turning guardrail behavior into an auditable safety decision.

## DevOps / Quality

- Added GitHub Actions CI for Python 3.11 with `uv sync --dev --frozen`, full `ruff check`, and `pytest`, keeping the project green across API, Text2SQL, and portfolio documentation checkpoints.
- Cleaned existing ruff issues across evaluation scripts, Airflow DAG utilities, and data loaders to establish full-repo lint as a quality gate before extending Text2SQL v2.

## Portfolio / Cloud Mapping

- Mapped the local architecture to an AWS target design using MWAA, RDS/Aurora PostgreSQL, S3, ECS Fargate, ALB, CloudWatch, and QuickSight, while explicitly documenting cost-control and non-deployed boundaries.
- Produced portfolio-ready evidence including architecture SVG, Superset screenshots, Text2SQL demo GIF, API request/response examples, v1/v2 eval comparison, external-provider cost comparison, failure cases, 3-5 minute demo script, and interview talking points.

## Short Version

- Built AdInsight, an AI-native influencer campaign analytics platform combining Airflow ingestion, dbt semantic marts, Superset dashboards, ROAS prediction serving, and guarded Text2SQL APIs.
- Delivered deterministic Text2SQL baseline (`24/24 PASS`) and generated-SQL v2 guardrails with OpenAI/Gemini gateway backends, validator, timeout, audit logging, provider cost observability, CI, and documented failure cases.
