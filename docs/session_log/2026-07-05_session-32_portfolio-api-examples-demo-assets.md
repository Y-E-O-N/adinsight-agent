# Session 32 — Portfolio API Examples + Demo Assets (2026-07-05)

**Phase**: Phase 8C — portfolio closeout assets
**Duration**: ~25m
**Operator**: Yeon (with Codex)

## Goals
- `/query/v2` API hardening 결과를 request/response examples로 정리한다.
- Text2SQL/Superset/ROAS prediction 흐름을 3-5분 demo script로 만든다.
- 면접에서 바로 설명할 수 있는 talking points를 정리한다.

## Done
- [x] `docs/api/query_v2_request_response_examples.md` 추가
- [x] `docs/demo_script_3min.md` 추가
- [x] `docs/interview_talking_points.md` 추가
- [x] README에서 새 포트폴리오 자산 링크
- [x] `docs/portfolio_draft.md` 체크리스트와 면접 증거 매핑 업데이트
- [x] `CLAUDE.md`와 session index 갱신

## Decisions
- **실제 provider live eval은 보류한다**: `TEXT2SQL_PROVIDER_URL` 또는 API key가 필요하므로 지금은 gateway-ready boundary까지만 문서화한다.
- **문서도 검증 가능한 산출물로 취급한다**: API examples, demo script, talking points를 README와 portfolio checklist에 연결한다.
- **v2 limitation을 숨기지 않는다**: mock provider, refusal, no-LIMIT guardrail을 면접용 설명 자산으로 남긴다.

## Files changed
- `docs/api/query_v2_request_response_examples.md`
- `docs/demo_script_3min.md`
- `docs/interview_talking_points.md`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `20 passed`
- `git diff --check` -> pass

## Next session — start here
1. If provider credentials exist, run `TEXT2SQL_PROVIDER=http_json` eval.
2. Otherwise continue portfolio closeout:
   - architecture diagram export
   - README final polish
   - resume bullets
   - query tuning / reliability playbook
