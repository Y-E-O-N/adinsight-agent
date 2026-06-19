# Session 06 — Codex Session Logging (2026-05-07)

**Phase**: Project operations — 세션 운영 규칙 정비
**Duration**: ~20m
**Operator**: Yeon (with Codex)

## Goals
- Codex 대화 내역도 세션별로 추적할 수 있게 프로젝트 규칙을 정리한다.
- Claude 중심 세션 로그 규칙을 Codex 에도 적용한다.

## Done
- [x] Codex raw 로그 저장 위치 확인: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
- [x] 기존 Claude 스타일 raw 로그 저장 위치 확인: `logs/session_YYYYMMDD_HHMMSS.log`
- [x] Codex 가 읽을 프로젝트 지침 파일 `AGENTS.md` 추가
- [x] `docs/session_log/README.md` 를 Claude/Codex 공통 세션 로그 규칙으로 갱신
- [x] 현재 Codex 세션을 Session 06 으로 기록

## Decisions
- **raw log 와 프로젝트 요약 로그를 분리**: 대화 전문에 가까운 raw log 의 기본 저장 위치는 `logs/session_*.log` 로 고정하고, 프로젝트 공식 요약은 `docs/session_log/*.md` 에 사람이 읽기 좋은 형태로 남긴다. Why: 원본 대화 전체와 포트폴리오용 작업 기록의 용도가 다르기 때문.
- **`AGENTS.md` 추가**: Codex 세션 시작 시 읽을 전용 지침 파일을 둔다. Why: 기존 `CLAUDE.md` 는 Claude Code 중심이고, Codex 에서는 `AGENTS.md` 가 더 직접적인 프로젝트 컨텍스트 역할을 한다.

## Files changed
- `AGENTS.md` — Codex 작업 원칙과 raw/summary 세션 로그 저장 규칙 추가
- `docs/session_log/README.md` — 세션 정의를 Claude Code/Codex 공통으로 확장, `logs/session_*.log` raw 로그 위치 명시
- `docs/session_log/2026-05-07_session-06_codex-session-logging.md` — 이 세션 로그
- `CLAUDE.md` — 직전 세션 요약에 Session 06 추가

## Concepts taught (학습 강화)
- **raw log vs session summary** — raw log 는 전체 대화·도구 호출을 보관하는 원본 기록이고, session summary 는 다음 작업자가 빠르게 맥락을 복구할 수 있게 정리한 문서.
- **`AGENTS.md`** — Codex 가 저장소별 작업 지침을 확인하는 프로젝트 컨텍스트 파일.

## Portfolio assets added
- 해당 없음. 이번 세션은 프로젝트 운영 규칙 정비.

## Open questions
- Codex 세션 종료 때마다 `docs/session_log/` 마크다운 로그를 반드시 작성할지, 큰 작업 세션에만 작성할지 운영 강도 결정 필요.

## Metrics
- 신규 운영 문서: 1개 (`AGENTS.md`)
- 갱신된 세션 로그 규칙 문서: 1개

## Next session — start here
1. Phase 2 Stage 1 로 복귀: `raw.ig_posts` 테이블 설계
2. `infra/postgres/init/03_raw_schema.sql` 의 현재 변경사항 확인
3. `data_generation/collectors/loaders/postgres_loader.py` 와 DAG load task 연결 상태 확인
4. 멱등 5회 검증 절차 설계
