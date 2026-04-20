# Session 02 — Portfolio Workflow Setup (2026-04-16)

**Phase**: Phase 0 — Repository Bootstrap (마무리)
**Duration**: ~25m
**Operator**: Yeon (with Claude Code)

## Goals
- `docs/adinsight_portfolio_template.md` (~990 줄) 의 메시지를 **CLAUDE.md / 작업 흐름 / 메모리** 에 흡수해, Phase 진행 중에 자동으로 포트폴리오가 적립되도록 워크플로 셋업
- 사용자(Yeon) 의 추가 요청 반영: **단계별 진행 시 관련 개념·코드·구조도 친절히 설명** → CLAUDE.md 에 *Teaching-First* 5요소 원칙 신설
- 매 세션 시작 시 단일 진입점(CLAUDE.md) 만 읽으면 두 축(포트폴리오 First / Teaching-First) 모두 작동하도록

## Done
- [x] `CLAUDE.md` 통째 갱신 — 신규 섹션 §0 메타 원칙 / §7 Teaching-First / §8 포트폴리오 First / 불변 규칙에 안티패턴 회피 4건 추가 (#10~#13) / 디렉토리 규칙 보강
- [x] `docs/portfolio_draft.md` 신규 — 템플릿 §7 메트릭 카탈로그 + §8 스크린샷 체크리스트 + ADR 작성 큐 + 면접 토크포인트 매핑 + 최종 완성도 체크리스트를 **빈 자리(TBD)** 양식으로 통합
- [x] `docs/daily_log.md` 신규 — 부록 A "매일 10분 적립 루틴" 양식, 오늘 항목 1줄 기재
- [x] `docs/images/.gitkeep` — 스크린샷 디렉토리 신설
- [x] `docs/session_log/README.md` 갱신 — 템플릿에 **Concepts taught** + **Portfolio assets added** 항목 추가 + 두 항목 의미 설명
- [x] 메모리 신규 2건: `feedback_portfolio_first.md`, `feedback_teaching_mode.md`
- [x] 메모리 신규 1건: `reference_portfolio_template.md`
- [x] `MEMORY.md` 인덱스 3줄 추가
- [x] 본 세션 로그 작성

## Decisions
- **CLAUDE.md 통째 재작성 vs 부분 Edit**: 변경량 30%+ 이고 신규 섹션 4개 (§0/§7/§8/§12 보강) 추가. 통째 재작성이 더 명확.
- **Phase별 메트릭은 별도 파일 (`portfolio_draft.md`) 에**: CLAUDE.md 에 모두 넣으면 매 세션 로드 비용 ↑. CLAUDE.md 에는 *어디에 어떤 메트릭을 적립* 한다는 1줄 표만, 상세는 작업장 파일.
- **세션 로그 템플릿에 Concepts taught + Portfolio assets added 분리**: Decisions 와 합칠 수도 있었지만, 두 축(학습/포트폴리오) 의 *준수 여부 추적* 이 목적이므로 명시 칸 필요.
- **새 세션(Session 02) 분리 vs Session 01 확장**: 같은 채팅이지만 작업 단위가 다름 (스켈레톤 vs 워크플로 메타). 분리하는 편이 사용자가 명시한 *"세션 단위로 진행사항 정리"* 의 정신에 더 부합.
- **portfolio_draft.md 양식**: 모든 칸을 `**TBD**` 로 두되, 이미 알 수 있는 값(예: `.env.example` 변수 수 18개) 은 채워둠. 빈 칸이 어디에 있는지 한눈에 보이도록.

## Files changed
- `CLAUDE.md` — 통째 갱신. §0 메타 원칙 / §4 불변 규칙 #10~#14 (안티패턴) / §5 디렉토리 규칙 보강 / §7 Teaching-First / §8 포트폴리오 First / §9 세션 로그 템플릿 두 항목 추가 / §11 직전 세션 요약 갱신.
- `docs/portfolio_draft.md` — 신규. Part A (Phase별 메트릭) / Part B (스크린샷 체크리스트) / Part C (ADR 큐) / Part D (면접 매핑) / Part E (최종 완성도).
- `docs/daily_log.md` — 신규. 매일 10분 루틴 + 오늘 항목.
- `docs/images/.gitkeep` — 신규 폴더.
- `docs/session_log/README.md` — 템플릿에 Concepts taught + Portfolio assets added 항목, 두 항목의 의미, 인덱스에 Session 02 추가.
- `~/.claude/projects/.../memory/feedback_portfolio_first.md` — 신규.
- `~/.claude/projects/.../memory/feedback_teaching_mode.md` — 신규.
- `~/.claude/projects/.../memory/reference_portfolio_template.md` — 신규.
- `~/.claude/projects/.../memory/MEMORY.md` — 3줄 추가.

## Concepts taught (학습 강화)
이번 세션은 워크플로 셋업이라 코드 개념보다 **메타 원칙** 위주로 사용자에게 전달:
- **포트폴리오 First** — 코드 + 메트릭 + 이미지 + ADR 동시 적립 원칙. 부록 A 의 "끝난 뒤 정리하면 늦는다" 메시지 흡수.
- **Teaching-First 5요소** — Concept / Structure / Walkthrough / References / Verify. Phase 1+ 부터 신규 도구·SQL·DAG 도입 시마다 사용 예정.
- **안티패턴 7가지** (부록 B) — Claude 의 작업 시 자동 회피 규칙으로 변환 (CLAUDE.md §4 #10~#14).
- **세션 로그의 "Concepts taught" 칸** — 매 세션이 학습 강화 축을 준수했는지 자체 추적용.

## Portfolio assets added
- **Drafts (작업장)**: `docs/portfolio_draft.md` 신규 — Phase 1~9 빈 자리 + ADR 큐 (6건) + 면접 매핑 (8건) + 완성도 체크리스트
- **Daily log**: `docs/daily_log.md` 신규 + 2026-04-16 항목 1건
- **Images dir**: `docs/images/` 신설 (.gitkeep)
- **Metrics**: `metrics/run_results.jsonl` 에 본 세션 종료 시 1건 append (`p0.portfolio_workflow_setup`)
- **이미지·ADR**: 이번 세션은 메타 작업이라 신규 캡처/ADR 없음

## Open questions
- **ADR 001 (Postgres 단일 스택) 작성 시점**: Phase 1 시 함께 작성할지, 또는 일찍 (지금) 작성할지. 현재는 Phase 1 큐로 둠.
- **사용자가 한국어로 면접 본다고 가정** — 영문 README 우선순위는 Phase 9 시 재논의.

## Metrics
- 신규 파일 4개 (`CLAUDE.md` 갱신 / `portfolio_draft.md` / `daily_log.md` / 이미지 폴더), 메모리 3개, 세션 로그 1개
- 측정값: `metrics/run_results.jsonl` p0/portfolio_workflow_setup 1건

## Next session — start here
1. **세션 시작 체크**: 이 파일 + `2026-04-16_session-01_bootstrap.md` 의 Next 섹션 + `CLAUDE.md` §10 현재 Phase
2. **사전 환경 확인** (한 번만):
   - `uv sync` → `make help` 정상 출력
   - Docker Desktop 메모리 12GB 할당 (Settings → Resources)
   - 포트 충돌 없음 확인 (5432 / 8080 / 8088 / 6379 / 5555)
3. **Phase 1 본격 진입** — 블루프린트 §5 의 Phase 1 Claude Code 프롬프트 사용:
   - `docker-compose.yml` (postgres+pgvector / airflow{web,scheduler,worker} / redis / superset / flower)
   - `infra/postgres/init/01_extensions.sql` (vector / pg_trgm / pg_stat_statements + adinsight / airflow_meta / superset_meta DB 생성)
   - `infra/airflow/Dockerfile` + `requirements.txt`
   - `infra/superset/Dockerfile` + `superset_config.py`
   - `dags/sample_smoke_test.py` (Postgres `SELECT 1`)
4. **Teaching-First 5요소 적용**: docker-compose 작성 시 각 서비스마다 Concept(왜 필요)/Structure(어디 위치)/Walkthrough(핵심 옵션)/References/Verify(`make up && curl http://localhost:8080`) 함께 제공.
5. **포트폴리오 적립**: `time make up` 결과를 `docs/portfolio_draft.md` Phase 1 칸에 기록 + `docker compose ps` 캡처 → `docs/images/01_compose_ps.png`.
6. 완료 후 새 세션 로그 `2026-XX-XX_session-03_phase1-compose.md` 작성.
