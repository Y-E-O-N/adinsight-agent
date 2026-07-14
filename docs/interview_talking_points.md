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

### Why expose provider cost and latency?

Text2SQL quality is not only execution accuracy. A usable serving boundary also needs provider choice, estimated cost, latency, cache ratio, fallback status, and failure reason to be visible per request. `/query/v2` exposes this through `provider_summary` and mirrors it into the audit log.

## Metrics To Mention

| Area | Metric |
|---|---:|
| expected-SQL baseline | `24/24 PASS` |
| OpenAI positive eval | `24/24 PASS` |
| OpenAI negative eval | `14/14 PASS` |
| Gemini positive eval | `24/24 PASS` |
| Gemini negative eval | `12/14 PASS` |
| Gemini cost over 38 cases | `$0.064098` |
| OpenAI cost over 38 cases | `$0.103027` |
| provider cost observation | request-level `provider_summary` + audit summary CLI |
| ROAS model best MAE | `0.0474` |
| ROAS baseline MAE | `0.0892` |
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

### Provider-backed v2

The v2 provider defaults to mock because CI and demos should not depend on API keys. Real OpenAI/Gemini calls sit behind the same `TEXT2SQL_PROVIDER=http_json` gateway contract, so eval runner and API serving use the same boundary.

### Why Gemini primary and OpenAI fallback?

Gemini was cheaper in the latest measured 38-case positive/negative scope, while OpenAI was faster and cleaner on negative safety. ADR 004 therefore chooses Gemini as the cost-efficient primary path and OpenAI as the reliability/safety fallback, with deterministic registry fallback kept for curated demo stability.

The policy has also been live-smoked through `/query/v2`: a normal ROAS query completed on Gemini without fallback, while a content-safety refusal triggered Gemini -> OpenAI fallback and recorded `fallback_reason=primary_content_safety_refusal` in `provider_summary`.

## Strong Interview Answers

### "What would you improve next?"

I would collect more repeated dual-provider traffic and report fallback rate, p95 latency, and cost distribution from the audit summary CLI. The orchestration path is implemented; the next improvement is operational evidence over a larger request sample.

### "How would this move to AWS?"

MWAA for orchestration, RDS/Aurora PostgreSQL for serving data, S3 for raw/model/eval artifacts, ECS Fargate plus ALB for FastAPI, CloudWatch for logs/metrics, and QuickSight or managed Superset for BI.

### "What makes this more than a toy?"

The project has rebuildable data layers, dbt tests, CI, model artifact serving, API contracts, measured eval results, failure-case documentation, and AWS target architecture mapping.
