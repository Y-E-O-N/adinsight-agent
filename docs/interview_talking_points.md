# AdInsight Interview Talking Points

## One-Line Pitch

AdInsight is an AI-native analytics platform that turns influencer campaign data into campaign ROI marts, ROAS prediction, Superset monitoring, and guarded Text2SQL APIs.

## Architecture Decisions

### Why keep raw data immutable?

Raw Instagram and synthetic payment inputs stay in `raw` so every downstream mart can be rebuilt and audited. Transformations happen in dbt layers, not by mutating source records.

### Why add an `ai_native` layer?

General marts are optimized for BI. The `ai_native` layer is optimized for natural-language analytics: clear grain, semantic column names, synonyms, and example questions.

### Why deterministic Text2SQL v1 before generated SQL?

The deterministic `/query` endpoint creates a safety baseline. It proves that the expected-SQL registry, evaluator, and API shape work before introducing an LLM provider.

### Why keep `/query/v2` separate?

Generated SQL has different failure modes. `/query/v2` has its own provider factory, validator, statement timeout, audit log, and error-path tests, while `/query` remains stable.

## Metrics To Mention

| Area | Metric |
|---|---:|
| expected-SQL v1 eval | `18/18 PASS` |
| v2 mock eval | `13 PASS / 5 REFUSED / 0 BLOCKED` |
| v2 answerable exec accuracy | `1.0` |
| v2 refuse rate | `0.2778` |
| ROAS model best MAE | `0.0474` |
| ROAS baseline MAE | `0.0892` |
| unit tests | `20 passed` |
| CI | GitHub Actions ruff + pytest on push/PR |

## Failure Case Story

During v2 mock expansion, a Korean creator query without `LIMIT` was initially answerable but blocked by the validator. I kept it refused instead of weakening the guardrail.

Why this matters:

- It proves generated SQL is not trusted blindly.
- It turns a failure into a documented product decision.
- It gives a concrete example of safety over demo completeness.

## Tradeoffs

### Synthetic payment data

The project uses synthetic payment events because real advertiser payment data is sensitive. I explicitly label ROAS and model metrics as synthetic benchmark evidence.

### Small ML training set

The current labeled campaign set has 25 rows. I use leave-one-out comparison and artifact-backed serving to demonstrate the ML workflow, but I do not overclaim model generalization.

### Mock v2 provider

The v2 provider defaults to mock because CI and demos should not depend on API keys. A real provider can be connected through `TEXT2SQL_PROVIDER=http_json`.

## Strong Interview Answers

### "What would you improve next?"

I would connect a real provider gateway to the existing `http_json` contract, run the same 18-question eval, and compare mock vs real provider on Exec Acc, Refuse Rate, Unsafe Block Rate, and latency.

### "How would this move to AWS?"

MWAA for orchestration, RDS/Aurora PostgreSQL for serving data, S3 for raw/model/eval artifacts, ECS Fargate plus ALB for FastAPI, CloudWatch for logs/metrics, and QuickSight or managed Superset for BI.

### "What makes this more than a toy?"

The project has rebuildable data layers, dbt tests, CI, model artifact serving, API contracts, measured eval results, failure-case documentation, and AWS target architecture mapping.
