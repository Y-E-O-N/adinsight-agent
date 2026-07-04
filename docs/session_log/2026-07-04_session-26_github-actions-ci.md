# Session 26 — GitHub Actions CI (2026-07-04)

**Phase**: Phase 8C — CI/CD
**Duration**: ~20m
**Operator**: Yeon (with Codex)

## Goals
- Full ruff cleanup 이후 GitHub Actions CI를 추가한다.
- push/PR마다 Python quality gate를 자동 실행한다.
- README와 portfolio draft에 CI asset을 반영한다.

## Done
- [x] `.github/workflows/ci.yml`을 추가했다.
- [x] CI workflow가 Python 3.11에서 실행되도록 했다.
- [x] `uv sync --dev --frozen`으로 lockfile 기반 dependency install을 사용했다.
- [x] CI steps에 `uv run ruff check`와 `uv run pytest -q`를 추가했다.
- [x] README 상단에 CI badge를 추가했다.
- [x] `docs/portfolio_draft.md` Phase 8 품질·CI 항목과 checklist를 갱신했다.
- [x] `CLAUDE.md`, session index, metrics를 갱신했다.

## Decisions
- **dbt CI는 아직 보류한다**: 현재 GitHub-hosted runner에서 Postgres/dbt profile까지 구성하면 scope가 커진다. 첫 CI는 Python quality gate로 고정한다.
- **uv lockfile 기반으로 설치한다**: 로컬과 CI dependency 해석 차이를 줄이기 위해 `uv sync --dev --frozen`을 사용한다.

## Files changed
- `.github/workflows/ci.yml` — GitHub Actions workflow
- `README.md` — CI badge and Phase table update
- `docs/portfolio_draft.md` — CI badge/checklist update
- `CLAUDE.md` — current quality gate and session summary update
- `docs/session_log/2026-07-04_session-26_github-actions-ci.md` — current handoff
- `docs/session_log/README.md` — session index update
- `metrics/run_results.jsonl` — CI workflow metric append

## Concepts taught
- **CI quality gate** — 로컬에서 통과한 `ruff`와 `pytest`를 원격 push/PR마다 반복 실행해 regression을 막는 자동 검사다.
- **Frozen dependency install** — lockfile과 다른 dependency resolution이 CI에서 생기지 않게 막는다.

## Portfolio assets added
- README CI badge
- `.github/workflows/ci.yml`

## Open questions
- GitHub Actions 첫 원격 실행 결과를 확인해 badge가 pass 상태인지 확인한다.
- dbt parse/test를 CI에 추가할지는 별도 checkpoint로 판단한다.

## Metrics
- Local `uv run ruff check` -> pass
- Local `uv run pytest -q` -> `13 passed`
- `git diff --check` -> pass

## Next session — start here
1. Check GitHub Actions status for the latest push.
2. If CI passes, choose next:
   - real provider integration design for Text2SQL v2
   - or dbt CI expansion.
