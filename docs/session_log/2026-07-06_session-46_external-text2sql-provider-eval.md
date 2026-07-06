# 2026-07-06 Session 46 — External Text2SQL Provider Eval

## Goals

- OpenAI/Gemini API key 설정 이후 실제 external Text2SQL provider를 같은 gateway/eval contract로 평가한다.
- 계정에서 사용 가능한 모델 ID를 확인하고, positive 24 + negative/content-safety 14 결과를 local model 결과와 비교한다.

## Done

- OpenAI model list에서 `gpt-5.4-mini-2026-03-17` 사용 가능을 확인했다.
- Gemini model list에서 `gemini-3.1-flash-lite` 사용 가능을 확인했다.
- OpenAI gateway smoke 통과:
  - backend: `TEXT2SQL_GATEWAY_BACKEND=openai`
  - model: `gpt-5.4-mini-2026-03-17`
  - result: answerable SQL contract returned
- Gemini gateway smoke 중 Interactions API 응답 shape가 `steps[].content[].text`임을 확인하고 parser를 보강했다.
- Provider/gateway HTTP error가 eval runner를 중단하지 않고 케이스별 failure로 기록되도록 보강했다.
- Positive/negative eval을 두 provider 후보에 대해 실행했다.
- `docs/images/06_text2sql_eval_summary.svg`를 최신 metrics 기준으로 재생성했다.

## Decisions

- 현재 1순위 external candidate는 `gpt-5.4-mini-2026-03-17`이다.
- `gemini-3.1-flash-lite`는 비용 후보로는 의미 있지만, 현 prompt/schema에서는 positive 정확도와 negative safety가 모두 OpenAI mini보다 낮다.
- Provider error는 safety pass로 간주하지 않는다. Positive에서는 `FAIL`, negative에서는 `FAIL_PROVIDER_ERROR`로 집계한다.
- Product demo는 아직 deterministic `/query` v1 또는 fallback-enabled `/query/v2`를 중심으로 설명해야 한다. Free-form primary Text2SQL은 failed-case tuning 후 재평가한다.

## Files changed

- `text2sql_gateway/backends.py` — OpenAI temperature omission, Gemini Interactions response parser, default external model IDs.
- `agent/text2sql/provider.py` — HTTP error body를 provider error detail에 포함.
- `agent/eval/run_text2sql_v2_eval.py` — provider error를 케이스별 `FAIL`로 기록.
- `agent/eval/run_text2sql_negative_eval.py` — provider error를 `FAIL_PROVIDER_ERROR`로 별도 집계.
- `tests/unit/test_text2sql_gateway.py` — Gemini `steps[].content[].text` response shape test.
- `tests/unit/test_text2sql_v2_eval.py` — positive eval provider error handling test.
- `tests/unit/test_text2sql_negative_eval.py` — negative eval provider error handling tests.
- `.env.example` — evaluated external model IDs를 기본 예시로 반영.
- `README.md` — external provider first-pass 결과 요약.
- `docs/analysis/stage6_text2sql_local_model_eval_rubric.md` — OpenAI/Gemini 비교표와 해석 추가.
- `docs/analysis/stage6_llm_text2sql_v2_design.md` — real-provider eval 결과와 다음 튜닝 방향 갱신.
- `docs/architecture/text2sql_gateway_architecture.md` — external backend 모델 예시와 first-pass eval table 추가.
- `docs/portfolio_draft.md` — external provider eval asset 체크리스트 반영.
- `docs/images/06_text2sql_eval_summary.svg` — 최신 eval rows 기준 재생성.
- `metrics/run_results.jsonl` — OpenAI/Gemini positive/negative eval 결과 append.

## Concepts taught

- **Model availability check** — 문서에 있는 모델명이 아니라 현재 계정의 model-list API에서 호출 가능한 모델인지 먼저 확인해야 한다.
- **Gateway response shape drift** — provider가 JSON contract를 지키더라도 응답 envelope shape가 다를 수 있어 adapter parser를 테스트로 고정해야 한다.
- **Model-only eval vs product fallback** — fallback을 켠 product 품질과 fallback 없는 모델 성능은 분리해서 기록해야 한다.

## Portfolio assets added

- External provider comparison metrics:
  - `gpt-5.4-mini-2026-03-17`: positive `12 PASS / 9 FAIL / 2 REFUSED / 1 BLOCKED`, score `66.21`; negative `13/14 PASS`.
  - `gemini-3.1-flash-lite`: positive `9 PASS / 15 FAIL / 0 REFUSED / 0 BLOCKED`, score `56.25`; negative `12/14 PASS`.
- Eval chart: `docs/images/06_text2sql_eval_summary.svg`.
- Architecture/provider comparison table: `docs/architecture/text2sql_gateway_architecture.md`.

## Open questions

- OpenAI mini failure cases 중 prompt/schema tuning으로 해결 가능한 항목과 registry fallback으로 남길 항목을 분리해야 한다.
- Unsafe echo 실패는 prompt의 refusal wording을 더 짧고 중립적으로 만들면 줄어드는지 재평가해야 한다.
- `gpt-5.5` 또는 Gemini Pro 계열을 accuracy upper-bound로 1회만 추가 평가할지 결정해야 한다.

## Metrics

- `uv run ruff check` -> pass
- `uv run pytest -q` -> `48 passed`
- `git diff --check` -> pass
- OpenAI model list availability: `gpt-5.4-mini-2026-03-17=true`
- Gemini model list availability: `gemini-3.1-flash-lite=true`

## Next session — start here

1. Inspect `gpt-5.4-mini-2026-03-17` failed cases from the eval output and group by failure type.
2. Add high-signal prompt/schema examples only for recurring failures:
   - LIMIT mismatch
   - latest snapshot filter missing
   - semantic aggregation mismatch
   - unsafe echo wording
3. Rerun OpenAI mini positive 24 + negative 14 once.
