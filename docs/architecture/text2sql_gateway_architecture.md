# Text2SQL Gateway Architecture

**Status**: implemented with mock backend
**Gateway app**: `text2sql_gateway/main.py`
**Local endpoint**: `POST /text2sql/generate`
**Docker Compose service**: `text2sql-gateway` on port `8010`

## Why Gateway First

AdInsight will eventually need a web page where a user asks an analytics question and sees query results.

The cleaner long-term split is:

```text
Web UI
  -> Serving API /query/v2
      -> Text2SQL Gateway /text2sql/generate
          -> LLM provider later
      -> SQL validator
      -> Postgres execution
      -> rows and answer back to UI
```

This keeps provider-specific code out of the user-facing serving API.

## Responsibilities

| Layer | Responsibility |
|---|---|
| Web UI | Collect user question and render answer/table |
| Serving API `/query/v2` | Validate generated SQL, execute against Postgres, audit request |
| Text2SQL Gateway | Generate SQL candidate JSON from question + schema context |
| LLM provider | Later backend for SQL generation |
| Postgres | Execute only validated SQL |

## Current Implementation

The gateway currently uses `MockSqlGenerationClient`.

This means:

- no external LLM API key is required
- CI and local demos stay deterministic
- the HTTP contract is already fixed for later real-provider work

## Contract

Request:

```json
{
  "question": "Which campaigns have the highest ROAS?",
  "schema_context": "Allowed tables: ..."
}
```

Response:

```json
{
  "answerability": "answerable",
  "sql": "select ...",
  "expected_tables": ["ai_native.ai_campaign_roi_summary"],
  "reason": "Question asks for campaigns ranked by ROAS.",
  "mode": "text2sql_gateway_mock_v1"
}
```

`/query/v2` already accepts this response through `TEXT2SQL_PROVIDER=http_json`.

## Local Run

Start gateway only:

```bash
uv run uvicorn text2sql_gateway.main:app --host 0.0.0.0 --port 8010
```

Call gateway:

```bash
curl -s -X POST http://127.0.0.1:8010/text2sql/generate \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?","schema_context":"Allowed tables: ai_native.ai_campaign_roi_summary"}'
```

Wire `/query/v2` to gateway:

```bash
TEXT2SQL_PROVIDER=http_json
TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate
TEXT2SQL_PROVIDER_API_KEY=
```

Docker Compose service:

```bash
docker compose up text2sql-gateway
```

## Optional Gateway Auth

Set:

```bash
TEXT2SQL_GATEWAY_API_KEY=...
```

Then callers must send:

```http
Authorization: Bearer ...
```

The serving API sends this via `TEXT2SQL_PROVIDER_API_KEY`.

## Next Step

Replace the gateway's mock backend with one of:

- OpenAI-compatible backend
- Bedrock backend
- Gemini backend

The serving API and future web UI do not need to know which provider is used behind the gateway.
