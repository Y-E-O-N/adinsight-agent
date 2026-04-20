# Session Log

세션마다 한 개의 마크다운 파일을 추가합니다. 세션 = Claude Code 한 번 실행 단위 (≈ 1~3시간).

## 파일명 규칙
```
YYYY-MM-DD_session-NN_<topic-kebab-case>.md
```
예) `2026-04-16_session-01_bootstrap.md`, `2026-04-23_session-03_phase1-compose.md`

## 작성 규율
- **세션 시작 시**
  1. `CLAUDE.md` 읽기
  2. 이 폴더의 가장 최신 1~2개 파일 읽고 **"Next session — start here"** 확인
  3. 오늘 할 일을 사용자와 합의

- **세션 종료 시**
  1. 이 폴더에 새 파일 작성 (아래 템플릿)
  2. 이 `README.md` 인덱스 한 줄 추가
  3. 루트 `CLAUDE.md` 의 **§11 직전 세션 요약** 갱신
  4. (해당 시) `docs/daily_log.md` 한 줄 append + `metrics/run_results.jsonl` append

## 템플릿

```markdown
# Session NN — <Topic> (YYYY-MM-DD)

**Phase**: Phase X — <name>
**Duration**: ~XXm
**Operator**: Yeon (with Claude Code)

## Goals
- ...

## Done
- [x] ...

## Decisions
- **<무엇을>**: <왜 그렇게 결정했는가>

## Files changed
- `path/to/file` — 한 줄 설명

## Concepts taught (학습 강화)
- **<용어/도구/패턴>** — 어떤 맥락에서 어떤 식으로 설명했는지 1줄 (CLAUDE.md §7 Teaching-First 5요소 적용)

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl` 에 append 한 항목
- 이미지: `docs/images/NN_*.png` 신규 캡처
- ADR: `docs/adr/00X-...md` 신규
- 작업장 갱신: `docs/portfolio_draft.md` 어느 칸을 어떤 값으로 채웠는지

## Open questions
- ...

## Metrics
- (수치 요약 — Portfolio assets 와 중복 시 생략 가능)

## Next session — start here
- 다음 세션 시작점 / 우선순위
```

> **두 신규 항목의 의미**
> - **Concepts taught** — 이 프로젝트는 학습 프로젝트. Teaching-First 원칙(CLAUDE.md §7) 준수 여부를 추적.
> - **Portfolio assets added** — 이 프로젝트는 포트폴리오 First. 매 세션이 면접 자산을 적립했는지 추적.

---

## Index
- [2026-04-16 · Session 01 · Bootstrap](2026-04-16_session-01_bootstrap.md) — 폴더 스켈레톤 / CLAUDE.md / Makefile / 메트릭 인프라 / 세션 로그 시스템 셋업
- [2026-04-16 · Session 02 · Portfolio Workflow Setup](2026-04-16_session-02_portfolio-workflow.md) — CLAUDE.md 확장 (포트폴리오 First + Teaching-First) / portfolio_draft / daily_log / images 폴더
- [2026-04-19 · Session 03 · Phase 1 docker-compose 스택](2026-04-19_session-03_phase1-compose.md) — 가이드 모드 전환 + 8개 파일 직접 작성 (smoke DAG / postgres init / airflow / superset / compose) + YAML 검증
- [2026-04-20 · Session 04 · Phase 1 스택 기동 완료](2026-04-20_session-04_phase1-live.md) — make up 버그 3개 디버깅 + 전체 스택 healthy + Smoke DAG 성공 + 스크린샷 + GitHub 푸시
