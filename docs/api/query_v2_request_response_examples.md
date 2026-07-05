# `/query/v2` Request And Response Examples

**Status**: mock provider default, real provider gateway-ready
**Endpoint**: `POST /query/v2`

## Purpose

`/query/v2` is the generated-SQL Text2SQL boundary.

It is intentionally separate from `/query`:

- `/query`: deterministic expected-SQL registry v1
- `/query/v2`: provider-backed SQL generation v2 with validation, timeout, and audit logging

The current default provider is `TEXT2SQL_PROVIDER=mock`. A real provider can be connected through `TEXT2SQL_PROVIDER=http_json`.

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
  "known_limitation": "Uses a provider-free mock SQL generator. This validates the v2 API boundary and SQL guardrails before connecting a real LLM provider."
}
```

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
    "mode": "llm_generated_sql_v2_mock"
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
    "mode": "llm_generated_sql_v2_mock"
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
  "validation_limit": 5
}
```

The audit log is runtime evidence and lives under ignored `logs/`; it is not committed.

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
  "reason": "Question asks for campaigns ranked by ROAS."
}
```

## Verified Gateway Path

Latest local smoke:

- `TEXT2SQL_PROVIDER=http_json`
- `TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate`
- `/query/v2` response mode: `llm_generated_sql_v2_http_json`
- row count: `5`
- top campaign: `camp_000029`
- latency: `58.981ms`
