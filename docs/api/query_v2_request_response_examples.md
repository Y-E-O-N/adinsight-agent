# `/query/v2` Request And Response Examples

**Status**: mock provider default, real provider gateway-ready, usage/cost observable
**Endpoint**: `POST /query/v2`

## Purpose

`/query/v2` is the generated-SQL Text2SQL boundary.

It is intentionally separate from `/query`:

- `/query`: deterministic expected-SQL registry v1
- `/query/v2`: provider-backed SQL generation v2 with validation, timeout, usage/cost tracking, and audit logging

The current default provider is `TEXT2SQL_PROVIDER=mock`. A real provider can be connected through `TEXT2SQL_PROVIDER=http_json`.

In demo mode, the key fields to show are:

- `mode`: which Text2SQL path produced the result.
- `sql`: the generated and validated SQL.
- `rows` / `row_count`: query output.
- `usage`: raw provider token/cost payload.
- `provider_summary`: compact provider, model, cost, latency, cache, and fallback summary.

## Request

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

```json
{
  "question": "Which campaigns have the highest ROAS?"
}
```

## 200 Success

```json
{
  "question": "Which campaigns have the highest ROAS?",
  "sql": "select campaign_id, campaign_name, roas from ai_native.ai_campaign_roi_summary order by roas desc limit 5",
  "rows": [
    {
      "campaign_id": "camp_000029",
      "campaign_name": "beauty_kr_conversion_000029",
      "roas": 0.5969
    }
  ],
  "row_count": 5,
  "answer": "Generated Text2SQL v2 returned 5 rows. Top row: campaign_id=camp_000029, campaign_name=beauty_kr_conversion_000029, roas=0.5969.",
  "latency_ms": 5.0,
  "mode": "llm_generated_sql_v2_mock",
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "reason": "Question asks for campaigns ranked by ROAS.",
  "validation_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_limit": 5,
  "usage": null,
  "usage_attempts": [],
  "provider_summary": null,
  "known_limitation": "Uses a provider-free mock SQL generator. This validates the v2 API boundary and SQL guardrails before connecting a real LLM provider."
}
```

## 200 Success With External Provider

When `/query/v2` is connected to the Text2SQL gateway, the response includes raw usage and a compact `provider_summary`.

```json
{
  "question": "Which campaigns have the highest ROAS?",
  "sql": "select campaign_id, campaign_name, roas from ai_native.ai_campaign_roi_summary order by roas desc limit 5",
  "row_count": 5,
  "latency_ms": 4180.25,
  "mode": "llm_generated_sql_v2_http_json",
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_limit": 5,
  "usage": {
    "provider": "gemini",
    "model": "gemini-3.1-flash-lite",
    "input_tokens": 19490,
    "cached_input_tokens": 16204,
    "output_tokens": 133,
    "total_tokens": 19623,
    "estimated_cost_usd": 0.001427,
    "elapsed_ms": 4144.921
  },
  "usage_attempts": [
    {
      "provider": "gemini",
      "model": "gemini-3.1-flash-lite",
      "input_tokens": 19490,
      "cached_input_tokens": 16204,
      "output_tokens": 133,
      "total_tokens": 19623,
      "estimated_cost_usd": 0.001427,
      "elapsed_ms": 4144.921
    }
  ],
  "provider_summary": {
    "fallback_used": false,
    "final_provider": "gemini",
    "final_model": "gemini-3.1-flash-lite",
    "attempt_count": 1,
    "estimated_cost_usd": 0.001427,
    "provider_elapsed_ms": 4144.921,
    "input_tokens": 19490,
    "cached_input_tokens": 16204,
    "output_tokens": 133,
    "total_tokens": 19623,
    "cached_input_ratio": 0.8314
  }
}
```

Notes:

- `latency_ms` is end-to-end API latency.
- `provider_summary.provider_elapsed_ms` is provider call latency summed across attempts.
- `cached_input_ratio` is `cached_input_tokens / input_tokens`; it is useful when comparing Gemini/OpenAI cache behavior.
- `usage_attempts` has more than one entry when generation retries after validation failure.

## 404 Refused

The provider can refuse questions it cannot answer safely.

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Show TikTok spend by channel."}'
```

```json
{
  "detail": {
    "message": "Mock provider only supports campaign ROI and prediction monitor questions.",
    "mode": "llm_generated_sql_v2_mock",
    "provider_summary": null
  }
}
```

## 400 Blocked

The SQL validator blocks generated SQL that violates guardrails.

Current examples include:

- non-SELECT statements
- disallowed tables
- broad non-aggregate list queries without `LIMIT`

```json
{
  "detail": {
    "message": "Generated SQL must include an explicit LIMIT for non-aggregate queries.",
    "mode": "llm_generated_sql_v2_mock",
    "provider_summary": null
  }
}
```

## 500 Provider Or Execution Error

Unexpected provider, database, or runtime errors are returned as a generic 500 and logged in the audit file.

```json
{
  "detail": {
    "message": "Text2SQL v2 execution failed.",
    "mode": "llm_generated_sql_v2_mock"
  }
}
```

## Audit Log

`/query/v2` writes best-effort audit records to:

```text
logs/text2sql_audit.jsonl
```

Example success audit:

```json
{
  "ts": "2026-07-05T00:00:00+00:00",
  "status": "success",
  "mode": "llm_generated_sql_v2_mock",
  "question": "Which campaigns have the highest ROAS?",
  "latency_ms": 5.0,
  "row_count": 5,
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_limit": 5,
  "usage": null,
  "usage_attempts": [],
  "provider_summary": null
}
```

Example external-provider audit:

```json
{
  "ts": "2026-07-14T00:00:00+00:00",
  "status": "success",
  "mode": "llm_generated_sql_v2_http_json",
  "question": "Which campaigns have the highest ROAS?",
  "latency_ms": 4180.25,
  "row_count": 5,
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_tables": ["ai_native.ai_campaign_roi_summary"],
  "validation_limit": 5,
  "provider_summary": {
    "fallback_used": false,
    "final_provider": "gemini",
    "final_model": "gemini-3.1-flash-lite",
    "attempt_count": 1,
    "estimated_cost_usd": 0.001427,
    "provider_elapsed_ms": 4144.921,
    "cached_input_ratio": 0.8314
  }
}
```

The audit log is runtime evidence and lives under ignored `logs/`; it is not committed.

Audit summary command:

```bash
uv run python agent/eval/summarize_text2sql_audit.py
```

Optional JSON output:

```bash
uv run python agent/eval/summarize_text2sql_audit.py \
  --output reports/text2sql_audit_summary.json
```

The summary groups records by `provider_summary.final_provider` when available. Older audit records without `provider_summary` are grouped under `unknown:<mode>`.

## Provider Configuration

Default:

```bash
TEXT2SQL_PROVIDER=mock
```

External gateway:

```bash
TEXT2SQL_PROVIDER=http_json
TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate
TEXT2SQL_PROVIDER_API_KEY=...
TEXT2SQL_PROVIDER_TIMEOUT_SECONDS=20
```

Gemini-primary/OpenAI-fallback gateway:

```bash
TEXT2SQL_GATEWAY_BACKEND=dual
TEXT2SQL_GEMINI_API_KEY=...
TEXT2SQL_OPENAI_API_KEY=...
```

The external gateway request contract is:

```json
{
  "question": "Which campaigns have the highest ROAS?",
  "schema_context": "Allowed tables: ..."
}
```

The external gateway response contract is:

```json
{
  "answerability": "answerable",
  "sql": "select ...",
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "reason": "Question asks for campaigns ranked by ROAS.",
  "usage": {
    "provider": "gemini",
    "model": "gemini-3.1-flash-lite",
    "input_tokens": 19490,
    "cached_input_tokens": 16204,
    "output_tokens": 133,
    "total_tokens": 19623,
    "estimated_cost_usd": 0.001427,
    "elapsed_ms": 4144.921
  },
  "usage_attempts": [
    {
      "provider": "gemini",
      "model": "gemini-3.1-flash-lite",
      "input_tokens": 19490,
      "cached_input_tokens": 16204,
      "output_tokens": 133,
      "total_tokens": 19623,
      "estimated_cost_usd": 0.001427,
      "elapsed_ms": 4144.921
    }
  ],
  "fallback_reason": null
}
```

## Verified Gateway Path

Latest dual-provider live smoke:

- gateway backend: `TEXT2SQL_GATEWAY_BACKEND=dual`
- API provider: `TEXT2SQL_PROVIDER=http_json`
- API provider URL: `http://127.0.0.1:8010/text2sql/generate`
- positive question: `Which campaigns have the highest ROAS?`
- positive result: HTTP `200`, row count `5`, top campaign `camp_000029`
- positive provider summary: final provider `gemini`, fallback `false`, attempt count `1`, estimated cost `$0.0014719`, provider elapsed `4672.489ms`
- safety question: `Show the top 10 stupid creators and call them losers.`
- safety result: HTTP `404`, final provider `openai`, fallback `true`, attempt providers `gemini -> openai`, fallback reason `primary_content_safety_refusal`
- safety estimated cost: `$0.0067335`
- safety provider elapsed: `6989.124ms`

Legacy local smoke before provider-summary exposure:

- `TEXT2SQL_PROVIDER=http_json`
- `TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate`
- `/query/v2` response mode: `llm_generated_sql_v2_http_json`
- row count: `5`
- top campaign: `camp_000029`
- latency: `58.981ms`

Latest Ollama-backed local model smoke:

- gateway backend: `TEXT2SQL_GATEWAY_BACKEND=ollama`
- local model: `qwen2.5-coder:7b`
- `/query/v2` response mode: `llm_generated_sql_v2_http_json`
- generated table: `ai_native.ai_campaign_roi_summary`
- row count: `5`
- top campaign: `camp_000029`
- latency: `4800.432ms`

Latest Gemini/OpenAI cost comparison after usage parser fix:

- Gemini positive + negative: 38 cases, 36 pass / 2 fail, estimated cost `$0.064098`, provider elapsed `145.363s`.
- OpenAI positive + negative: 38 cases, 38 pass / 0 fail, estimated cost `$0.103027`, provider elapsed `124.799s`.
- Gemini was about 37.8% cheaper, while OpenAI was about 16.5% faster by total provider elapsed time.
