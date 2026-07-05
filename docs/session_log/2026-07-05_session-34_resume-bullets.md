# Session 34 — Resume Bullets (2026-07-05)

**Phase**: Phase 8C — portfolio closeout assets
**Duration**: ~15m
**Operator**: Yeon (with Codex)

## Goals
- 현재까지의 AdInsight 산출물을 이력서 bullet로 바로 옮길 수 있게 정리한다.

## Done
- [x] `docs/resume_bullets.md` 추가
- [x] README에서 resume bullets 링크 추가
- [x] `docs/portfolio_draft.md` 포트폴리오 배포물 체크리스트 갱신
- [x] `CLAUDE.md`와 session index 갱신

## Decisions
- **성과를 과장하지 않는다**: synthetic payment, small training set, mock provider 한계를 숨기지 않고 bullet에서 역할과 검증 기준을 분리한다.
- **수치가 있는 bullet을 우선한다**: Text2SQL eval, ROAS MAE, CI/test 결과처럼 검증 가능한 지표를 포함한다.

## Files changed
- `docs/resume_bullets.md`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `docs/session_log/2026-07-05_session-34_resume-bullets.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `20 passed`
- `git diff --check` -> pass

## Next session — start here
1. Real provider eval if `TEXT2SQL_PROVIDER_URL` is available.
2. README final polish.
3. Reliability playbook or query tuning evidence.
