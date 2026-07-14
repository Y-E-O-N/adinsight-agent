# Stage 6 Post-Eval Execution Plan

## Scope

운영 정책 ADR은 이번 순서에서 제외한다. 이 문서는 eval을 더 확장하지 않고, 이미 얻은 OpenAI/Gemini 평가 결과를 실제 demo, 관측성, 포트폴리오 자산으로 연결하기 위한 실행 순서를 정리한다.

## Milestones

| 순서 | 마일스톤 | 상태 | 산출물 |
|---:|---|---|---|
| 1 | Text2SQL demo API 정리 | Done | `/query/v2` response/audit에 `provider_summary` 추가, API 예시 문서 갱신 |
| 2 | Demo 화면 또는 Superset 연결 갱신 | Done | demo runbook/evidence를 v2 provider-summary 기준으로 갱신 |
| 3 | Audit 기반 운영 관측성 | Done | `logs/text2sql_audit.jsonl`에서 provider별 cost/latency/failure를 요약하는 스크립트 |
| 4 | Safety/quality hardening | Done | Gemini unsafe echo sanitizer, `p4_q003` sponsored-rate intent split |
| 5 | Portfolio packaging | Done | README, portfolio draft, resume bullets, interview talking points 최신 수치 반영 |
| 6 | Dual-provider serving fallback | Done | `TEXT2SQL_GATEWAY_BACKEND=dual`에서 Gemini primary → OpenAI fallback 구현 |

## Current Checkpoint

완료한 내용:

- `/query/v2` 응답에 `provider_summary`를 추가했다.
- success/refused/blocked/fallback audit record에도 provider/cost/latency 요약을 남긴다.
- `docs/api/query_v2_request_response_examples.md`에 external provider usage 예시와 Gemini/OpenAI 비용 비교를 추가했다.
- `docs/demo_script_3min.md`를 최신 provider-backed Text2SQL 흐름에 맞게 갱신했다.
- `docs/analysis/stage6_text2sql_superset_demo_runbook.md`에 `/query/v2` provider-summary demo step을 추가했다.
- `docs/analysis/stage6_text2sql_demo_evidence.md`에 v2 provider-summary evidence와 최신 Gemini/OpenAI 비용 비교를 추가했다.
- `agent/eval/summarize_text2sql_audit.py`로 audit JSONL provider/cost/latency 요약 CLI를 추가했다.
- `tests/unit/test_text2sql_audit_summary.py`로 Gemini/OpenAI/fallback/legacy audit record 집계를 검증했다.
- content-safety refusal reason sanitizer를 gateway에 추가해 abusive/sexual/violent refusal에서 사용자 표현을 반복하지 않게 했다.
- `p4_q003`용 sponsored candidate rate intent를 분리해 `total_posts`를 필수 SELECT column으로 요구하게 했다.
- Korean sponsored-rate 질문은 기존 output contract를 유지하도록 별도 regression test를 추가했다.
- README, portfolio draft, resume bullets, interview talking points에 최신 OpenAI/Gemini 결과와 `provider_summary` observability를 반영했다.
- `text2sql_gateway`에 Gemini primary + OpenAI fallback orchestration을 추가했다.
- gateway response contract에 `usage_attempts`와 `fallback_reason`을 추가하고, `/query/v2 provider_summary`가 최종 provider, attempt 비용/latency, fallback 여부를 합산하도록 했다.
- `TEXT2SQL_GATEWAY_BACKEND=dual` live smoke를 실행했다.
- positive request는 Gemini primary 단일 attempt로 성공했고, safety refusal request는 Gemini refusal 후 OpenAI fallback으로 최종 refusal 처리되며 `fallback_reason=primary_content_safety_refusal`을 남겼다.

검증:

- `uv run ruff check`
- `uv run pytest -q`
- `git diff --check`
- `git diff --check -- docs/api/query_v2_request_response_examples.md docs/demo_script_3min.md`
- `uv run python agent/eval/summarize_text2sql_audit.py`

## Next Session Start

후속 작업은 post-eval packaging 이후의 별도 라운드로 다룬다.

1. `/query/v2` `provider_summary`가 보이는 terminal-style demo GIF는 갱신 완료했다.
2. OpenAI/Gemini dual-provider fallback 정책은 `docs/adr/004-text2sql-dual-provider-fallback.md`로 작성 완료했다.
3. dual backend 실제 `/query/v2` smoke와 audit summary evidence 갱신을 완료했다.
4. 다음 구현 라운드는 live UI capture 또는 dashboard-facing demo polish다.
5. 필요하면 세션 로그를 작성해 다음 세션이 live UI capture부터 이어가게 한다.
