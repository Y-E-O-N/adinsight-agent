# 2026-07-06 Session 45 — External LLM Gateway Backends

## Goals

- Local Ollama 모델만으로는 Text2SQL primary model 기준에 못 미쳤으므로 OpenAI/Gemini 같은 외부 LLM도 같은 평가 프레임에 포함할 수 있게 한다.
- Serving API와 eval runner는 그대로 두고, provider-specific 호출은 Text2SQL gateway 안에 둔다.

## Done

- `TEXT2SQL_GATEWAY_BACKEND=openai` backend 추가.
- `TEXT2SQL_GATEWAY_BACKEND=gemini` backend 추가.
- OpenAI backend는 JSON Schema structured output contract를 사용한다.
- Gemini backend는 `application/json` response format + schema contract를 사용한다.
- `TEXT2SQL_EVAL_MODEL_LABEL`을 추가해 OpenAI/Gemini 모델명을 eval metrics에 기록할 수 있게 했다.
- `.env.example`, README, gateway architecture doc, Text2SQL design/rubric docs를 갱신했다.
- Unit tests에서 mocked HTTP response로 external provider payload와 parsing을 검증했다.

## Decisions

- `/query/v2`와 eval runner는 계속 `TEXT2SQL_PROVIDER=http_json`으로 gateway만 바라본다.
- OpenAI/Gemini 직접 호출 코드는 serving API가 아니라 gateway backend에만 둔다.
- Real external eval은 API key가 있을 때 실행한다. 현재 로컬 `.env`에는 OpenAI/Gemini key가 없었다.

## Files changed

- `text2sql_gateway/backends.py`
- `text2sql_gateway/main.py`
- `agent/eval/run_text2sql_v2_eval.py`
- `agent/eval/run_text2sql_negative_eval.py`
- `tests/unit/test_text2sql_gateway.py`
- `.env.example`
- `README.md`
- `docs/architecture/text2sql_gateway_architecture.md`
- `docs/analysis/stage6_llm_text2sql_v2_design.md`
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Concepts taught

- External LLM 비교도 local model과 같은 contract로 평가해야 수치가 공정하다.
- Gateway-first 구조는 provider switching, API key isolation, eval reuse에 유리하다.
- Product fallback과 model-only benchmark는 계속 분리해야 한다.

## Portfolio assets added

- External provider architecture and run instructions in `docs/architecture/text2sql_gateway_architecture.md`
- External provider comparison plan in `docs/analysis/stage6_text2sql_local_model_eval_rubric.md`
- Environment contract in `.env.example`

## Open questions

- OpenAI/Gemini API key를 어떤 방식으로 로컬 `.env`에 넣을지 결정해야 한다.
- 평가할 구체 모델 목록을 확정해야 한다.
- API 비용을 관리하기 위해 positive 24 + negative 14를 먼저 1회씩만 실행할지 결정해야 한다.

## Metrics

- Adapter tests: included in `uv run pytest -q`, total `44 passed`.
- Real external eval: pending API keys.

## Next session — start here

1. Add `TEXT2SQL_OPENAI_API_KEY` or `TEXT2SQL_GEMINI_API_KEY` to local `.env`.
2. Start gateway with `TEXT2SQL_GATEWAY_BACKEND=openai` or `gemini`.
3. Run `agent/eval/run_text2sql_v2_eval.py` and `agent/eval/run_text2sql_negative_eval.py` with `TEXT2SQL_PROVIDER=http_json`.
