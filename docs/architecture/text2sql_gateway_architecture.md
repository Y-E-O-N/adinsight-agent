# Text2SQL Gateway Architecture

**Status**: implemented with mock, local Ollama, OpenAI, and Gemini backend options
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

The gateway supports these backend modes:

| Backend | Env | Purpose |
|---|---|---|
| Mock | `TEXT2SQL_GATEWAY_BACKEND=mock` | deterministic CI/demo backend |
| Ollama/local model | `TEXT2SQL_GATEWAY_BACKEND=ollama` | local small-model Text2SQL backend |
| OpenAI | `TEXT2SQL_GATEWAY_BACKEND=openai` | external structured-output Text2SQL backend |
| Gemini | `TEXT2SQL_GATEWAY_BACKEND=gemini` | external structured-output Text2SQL backend |

The default is `mock`.

This means:

- no external LLM API key is required
- CI and local demos stay deterministic
- the HTTP contract is already fixed for later real-provider work
- local model output is still parsed into the same JSON contract before it can reach `/query/v2`

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

## Local Model Backend

Run a local model server that exposes an Ollama-compatible `/api/generate` endpoint, then start the gateway with:

```bash
TEXT2SQL_GATEWAY_BACKEND=ollama
TEXT2SQL_OLLAMA_URL=http://127.0.0.1:11434/api/generate
TEXT2SQL_OLLAMA_MODEL=qwen2.5-coder:7b
TEXT2SQL_OLLAMA_TIMEOUT_SECONDS=60
uv run uvicorn text2sql_gateway.main:app --host 0.0.0.0 --port 8010
```

Docker Compose equivalent:

```bash
TEXT2SQL_GATEWAY_BACKEND=ollama \
TEXT2SQL_OLLAMA_URL=http://host.docker.internal:11434/api/generate \
TEXT2SQL_OLLAMA_MODEL=qwen2.5-coder:7b \
docker compose up text2sql-gateway
```

Safety behavior:

- The local model is asked to return the Text2SQL JSON contract only.
- If the model returns invalid JSON, the gateway returns `not_answerable`.
- `/query/v2` still validates SQL before executing it.

## External Provider Backends

The external backends use the same gateway request/response contract as mock and Ollama. Provider-specific API calls stay inside `text2sql_gateway/main.py` and `text2sql_gateway/backends.py`; the serving API still only sees the internal `{question, schema_context} -> {answerability, sql, expected_tables, reason}` contract.

OpenAI backend:

```bash
TEXT2SQL_GATEWAY_BACKEND=openai
TEXT2SQL_OPENAI_API_KEY=$OPENAI_API_KEY
TEXT2SQL_OPENAI_MODEL=gpt-5.5
TEXT2SQL_OPENAI_TIMEOUT_SECONDS=60
TEXT2SQL_OPENAI_TEMPERATURE=0
uv run uvicorn text2sql_gateway.main:app --host 0.0.0.0 --port 8010
```

Gemini backend:

```bash
TEXT2SQL_GATEWAY_BACKEND=gemini
TEXT2SQL_GEMINI_API_KEY=$GEMINI_API_KEY
TEXT2SQL_GEMINI_MODEL=gemini-3.5-flash
TEXT2SQL_GEMINI_TIMEOUT_SECONDS=60
uv run uvicorn text2sql_gateway.main:app --host 0.0.0.0 --port 8010
```

Run model-only eval through the gateway:

```bash
set -a
source .env
set +a
POSTGRES_HOST=localhost \
TEXT2SQL_PROVIDER=http_json \
TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate \
TEXT2SQL_PROVIDER_TIMEOUT_SECONDS=90 \
TEXT2SQL_EVAL_MODEL_LABEL=$TEXT2SQL_OPENAI_MODEL \
uv run python agent/eval/run_text2sql_v2_eval.py
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

Replace or extend the gateway backend with one of:

- local Ollama model backend
- OpenAI-compatible backend
- Bedrock backend
- Gemini backend

The serving API and future web UI do not need to know which provider is used behind the gateway.

## Verified End-To-End Smoke

On `2026-07-05`, `/query/v2` was run through the local gateway:

```bash
uv run uvicorn text2sql_gateway.main:app --host 127.0.0.1 --port 8010

set -a; source .env; set +a; \
POSTGRES_HOST=localhost \
TEXT2SQL_PROVIDER=http_json \
TEXT2SQL_PROVIDER_URL=http://127.0.0.1:8010/text2sql/generate \
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Smoke request:

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

Result:

- gateway `/health`: `200 OK`
- API `/health`: `200 OK`
- `/query/v2`: `200 OK`
- response mode: `llm_generated_sql_v2_http_json`
- row count: `5`
- top campaign: `camp_000029`
- latency: `58.981ms`

## Verified Ollama End-To-End Smoke

On `2026-07-05`, `/query/v2` was run through the gateway with:

```bash
TEXT2SQL_GATEWAY_BACKEND=ollama
TEXT2SQL_OLLAMA_MODEL=qwen2.5-coder:7b
```

Initial result:

- The model returned valid gateway JSON.
- The first API execution failed because the model hallucinated a column/table combination.
- The fix was to enrich `SCHEMA_CONTEXT_V1` with exact allowed columns and canonical query examples.

Final result:

- API `/health`: `200 OK`
- `/query/v2`: `200 OK`
- response mode: `llm_generated_sql_v2_http_json`
- generated SQL table: `ai_native.ai_campaign_roi_summary`
- row count: `5`
- top campaign: `camp_000029`
- latency: `4800.432ms`

This shows why small local models need explicit schema context and why `/query/v2` keeps validator and execution guardrails after generation.
