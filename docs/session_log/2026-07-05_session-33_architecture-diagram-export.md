# Session 33 — Architecture Diagram Export (2026-07-05)

**Phase**: Phase 8C — portfolio visual asset
**Duration**: ~20m
**Operator**: Yeon (with Codex)

## Goals
- Mermaid 원본으로만 남아 있던 architecture diagram을 README에 바로 표시 가능한 SVG 자산으로 만든다.
- 최신 Text2SQL v2, CI, AWS target mapping까지 한 화면에 반영한다.

## Done
- [x] `docs/images/00_architecture.svg` 추가
- [x] README architecture section에 SVG embed 추가
- [x] `docs/portfolio_draft.md` screenshot/evidence checklist 갱신
- [x] `CLAUDE.md`와 session index 갱신

## Decisions
- **SVG를 직접 버전 관리한다**: README/PDF/포트폴리오에서 바로 재사용 가능하고, Mermaid 렌더링 도구가 없어도 GitHub에서 표시된다.
- **현재 구현과 target mapping을 함께 보여준다**: 로컬 구현과 AWS 전환 계획을 같은 다이어그램에서 설명할 수 있게 한다.

## Files changed
- `docs/images/00_architecture.svg`
- `README.md`
- `docs/portfolio_draft.md`
- `CLAUDE.md`
- `docs/session_log/README.md`
- `docs/session_log/2026-07-05_session-33_architecture-diagram-export.md`
- `metrics/run_results.jsonl`

## Metrics
- `uv run ruff check` -> pass
- `uv run pytest -q` -> `20 passed`
- `git diff --check` -> pass
- `xmllint --noout docs/images/00_architecture.svg` -> pass
- `file docs/images/00_architecture.svg` -> `SVG Scalable Vector Graphics image`

## Next session — start here
1. README final polish or resume bullets.
2. Real provider eval if `TEXT2SQL_PROVIDER_URL` becomes available.
3. Query tuning / reliability playbook if continuing portfolio closeout.
