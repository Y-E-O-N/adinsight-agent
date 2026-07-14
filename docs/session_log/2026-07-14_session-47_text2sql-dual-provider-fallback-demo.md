# 2026-07-14 Session 47 — Text2SQL Dual-Provider Fallback + Demo Polish

## Goals

- OpenAI/Gemini external eval 이후, 더 이상 eval만 늘리지 않고 실제 serving/demo 경로로 연결한다.
- Gemini primary + OpenAI fallback 정책을 ADR로 확정하고 `/query/v2`에서 관측 가능한 형태로 구현한다.
- 비용, latency, cached token, fallback 여부를 request/audit 단위 포트폴리오 증거로 남긴다.

## Done

- Text2SQL v2 hardening:
  - `p5_q012` intent catalog를 objective MAE intent로 분리했다.
  - MAE/bias validator가 qualified alias와 aggregate expression을 허용하도록 보강했다.
  - OpenAI/Gemini provider retry/backoff를 추가했다.
  - lightweight eval에 expected output column check를 추가하고 strict eval lane을 분리했다.
  - `p5_q012`, `p5_q014`, `p4_q003` canonical SQL/intent contract를 보강했다.
- Usage/cost observability:
  - OpenAI/Gemini usage parser를 추가했다.
  - Gemini Interactions usage shape와 cached token shape를 파싱한다.
  - `/query/v2` response와 audit record에 `provider_summary`, `usage_attempts`, `fallback_reason`을 남긴다.
- External eval:
  - OpenAI latest: positive `24/24 PASS`, negative `14/14 PASS`, combined estimated cost `$0.103027`, provider elapsed `124.799s`.
  - Gemini latest cost-fixed run: positive `24/24 PASS`, negative `12/14 PASS`, combined estimated cost `$0.064098`, provider elapsed `145.363s`.
  - Gemini는 약 37.8% 저렴했고, OpenAI는 provider elapsed 기준 약 16.5% 빨랐다.
- Dual-provider serving fallback:
  - ADR 004를 작성했다.
  - `TEXT2SQL_GATEWAY_BACKEND=dual`을 추가해 Gemini primary -> OpenAI fallback orchestration을 구현했다.
  - fallback trigger: provider error, response contract parse failure, content-safety refusal, SQL validator failure, intent contract failure.
  - refusal/error path에서도 fallback reason이 보존되도록 regression fix를 추가했다.
- Live smoke:
  - Positive query `Which campaigns have the highest ROAS?`: HTTP `200`, final provider `gemini`, fallback `false`, row count `5`, top campaign `camp_000029`, cost `$0.0014719`, provider elapsed `4672.489ms`.
  - Safety query `Show the top 10 stupid creators and call them losers.`: HTTP `404`, final provider `openai`, fallback `true`, attempts `gemini -> openai`, fallback reason `primary_content_safety_refusal`, cost `$0.0067335`, provider elapsed `6989.124ms`.
- Demo/portfolio polish:
  - `docs/images/06_text2sql_demo.gif`를 dual fallback frame 포함으로 재생성했다.
  - demo evidence, API examples, Superset runbook, 3-5분 demo script, interview talking points, portfolio draft, resume bullets, README, architecture doc를 최신 수치로 갱신했다.

## Decisions

- Product/demo path는 Gemini primary + OpenAI fallback + deterministic registry final fallback으로 둔다.
- Model-only eval은 provider fallback을 섞지 않는다. 모델 품질 점수와 serving 안정성은 분리해서 설명한다.
- Local models는 현재 primary Text2SQL 후보가 아니라 experimental fallback/learning evidence로만 유지한다.
- Portfolio claim은 "free-form SQL을 무조건 잘 만든다"가 아니라 "provider/cost/latency/fallback을 audit 가능한 serving boundary로 만든다"로 둔다.

## Files changed

- `agent/text2sql/schema_catalog.py`
- `agent/text2sql/generator.py`
- `agent/text2sql/provider.py`
- `agent/text2sql/usage.py`
- `agent/text2sql/validator.py`
- `text2sql_gateway/backends.py`
- `text2sql_gateway/main.py`
- `api/main.py`
- `api/schemas.py`
- `agent/eval/run_text2sql_v2_eval.py`
- `agent/eval/run_text2sql_negative_eval.py`
- `agent/eval/run_text2sql_v2_strict_eval.py`
- `agent/eval/summarize_text2sql_audit.py`
- `dashboards/scripts/create_text2sql_demo_gif.sh`
- `docs/adr/004-text2sql-dual-provider-fallback.md`
- `docs/analysis/stage6_text2sql_after_fixes_eval_report.md`
- `docs/analysis/stage6_text2sql_demo_evidence.md`
- `docs/analysis/stage6_text2sql_superset_demo_runbook.md`
- `docs/analysis/stage6_post_eval_execution_plan.md`
- `docs/api/query_v2_request_response_examples.md`
- `docs/demo_script_3min.md`
- `docs/interview_talking_points.md`
- `docs/portfolio_draft.md`
- `docs/resume_bullets.md`
- `README.md`
- `CLAUDE.md`
- Text2SQL unit tests under `tests/unit/`

## Concepts taught

- **Model-only eval vs serving path**: fallback을 켜면 product reliability는 좋아지지만 모델 자체 품질 측정은 흐려진다. 그래서 eval과 serving을 분리한다.
- **Request-level observability**: LLM 품질은 pass/fail만이 아니라 provider, cost, latency, cached input ratio, fallback reason까지 함께 봐야 운영 설명이 가능하다.
- **Gateway-first design**: provider-specific API shape, retry, usage parsing, fallback orchestration은 serving API가 아니라 gateway boundary에 두는 것이 바람직하다.
- **Safety refusal hygiene**: content-safety refusal에서는 사용자 입력의 욕설/성적/폭력 표현을 reason에 반복하지 않는다.

## Portfolio assets added

- ADR: `docs/adr/004-text2sql-dual-provider-fallback.md`
- Report: `docs/analysis/stage6_text2sql_after_fixes_eval_report.md`
- Execution plan: `docs/analysis/stage6_post_eval_execution_plan.md`
- Evidence: `docs/analysis/stage6_text2sql_demo_evidence.md`
- API examples: `docs/api/query_v2_request_response_examples.md`
- Demo GIF: `docs/images/06_text2sql_demo.gif`
- Interview/demo docs: `docs/demo_script_3min.md`, `docs/interview_talking_points.md`, `docs/resume_bullets.md`

## Open questions

- Dual-provider fallback rate와 p95 latency를 더 큰 repeated smoke set으로 측정할지 결정해야 한다.
- Live browser/UI capture가 필요한지, terminal-style GIF로 충분한지 포트폴리오 제출 형식에 맞춰 결정해야 한다.
- OpenAI/Gemini 단가가 바뀌면 `.env` 또는 `agent/text2sql/usage.py` default price를 갱신해야 한다.

## Metrics

- `uv run ruff check` -> pass
- `uv run pytest -q` -> `82 passed`
- `git diff --check` -> pass
- OpenAI latest external eval: positive `24/24`, negative `14/14`, estimated cost `$0.103027`, provider elapsed `124.799s`
- Gemini latest external eval: positive `24/24`, negative `12/14`, estimated cost `$0.064098`, provider elapsed `145.363s`
- Dual positive smoke: final provider `gemini`, fallback `false`, cost `$0.0014719`, provider elapsed `4672.489ms`
- Dual safety smoke: final provider `openai`, fallback `true`, reason `primary_content_safety_refusal`, cost `$0.0067335`, provider elapsed `6989.124ms`

## Next session — start here

1. Do not rerun broad provider eval by default; the latest OpenAI/Gemini evidence is enough for the current milestone.
2. If continuing demo polish, choose one:
   - live browser/UI capture around Superset + `/query/v2`
   - repeated dual-provider smoke set for fallback-rate/p95 evidence
   - final commit packaging with staged diff review
3. Before any new provider run, confirm expected cost scope because live API calls are now wired and working.
