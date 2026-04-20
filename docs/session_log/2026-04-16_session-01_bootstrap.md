# Session 01 — Bootstrap (2026-04-16)

**Phase**: Phase 0 — Repository Bootstrap
**Duration**: ~30m
**Operator**: Yeon (with Claude Code)

## Goals
- 블루프린트(`docs/adinsight_project_blueprint.md`)에 따라 프로젝트 진행 가능한 상태로 세팅
- CLAUDE.md (Claude Code 컨텍스트) 작성
- 세션 단위 진행 로그 시스템 구축
- README 덮어쓰기, Makefile, pyproject(uv), .env.example 등 부트스트랩 파일 생성

## Done
- [x] `CLAUDE.md` 작성 (블루프린트 섹션 13-3 템플릿 + 세션 로그 규율 추가)
- [x] `README.md` 덮어쓰기 (1줄 → JD 매핑표 + Quick Start placeholder + Phase 진행 상황)
- [x] `Makefile` 작성 (블루프린트 섹션 13-4)
- [x] `pyproject.toml` 작성 (uv 기반, dev 도구만; 런타임 의존성은 Phase별 추가)
- [x] `.env.example` 작성 (Airflow / Postgres / Superset / Redis / LLM / Agent / Slack)
- [x] `.sqlfluff` 작성 (dialect = postgres)
- [x] `.python-version` 작성 (3.11)
- [x] `.gitignore` 보강 (pgdata, dbt/profiles.yml, dbt/target, agent eval results, reports, parquet, raw)
- [x] `metrics/recorder.py` 작성 (블루프린트 섹션 7-3)
- [x] `metrics/portfolio_metrics.md` 작성 (TBD 템플릿)
- [x] `metrics/run_results.jsonl` 빈 파일 생성
- [x] `docs/session_log/README.md` 작성 (이 시스템의 사용 규율)
- [x] 본 세션 로그 작성
- [x] 누락 폴더 생성 + `.gitkeep`
- [x] Claude 메모리에 user / project / feedback / reference 저장

## Decisions
- **세션 로그 디렉토리 위치**: `docs/session_log/` — `docs/` 하위에 두는 편이 면접 시 "데이터 리터러시 / 문서화" 스토리에 자연스럽게 통합됨.
- **`api/` 폴더 유지**: 블루프린트엔 없지만 사용자 명시 요청. 향후 FastAPI 등 추가 시 활용. CLAUDE.md 디렉토리 규칙에 "현재 미사용, 유지" 명기.
- **`logs/` 폴더 유지**: Airflow 로그 마운트용. `.gitignore`에 이미 등록됨.
- **`docker-compose.yml` 미생성**: Phase 1 본격 작업의 핵심이라 부트스트랩에서 분리. README Quick Start에 "Phase 1 완료 후 활성화" 주석.
- **runtime 의존성 비워둠**: Phase별로 점진 추가. 부트스트랩 단계에서 무거운 패키지(airflow / dbt / langchain) 미리 깔지 않음 → `uv sync` 빠름.
- **메트릭 기록기 위치**: `metrics/recorder.py` 단일 모듈. 모든 DAG·스크립트가 `from metrics.recorder import log` 로 사용.

## Files changed
- `CLAUDE.md` — 신규. 모든 후속 세션에서 읽힐 컨텍스트.
- `README.md` — 덮어쓰기. JD 매핑표 + Phase 진행 상황 + Quick Start placeholder.
- `Makefile` — 신규. up/down/logs/psql/airflow-cli/superset-init/dbt-*/test/fmt/lint/clean.
- `pyproject.toml` — 신규. uv + Python 3.11 + dev tools.
- `.env.example` — 신규. 모든 비밀값 placeholder.
- `.sqlfluff` — 신규.
- `.python-version` — 신규.
- `.gitignore` — append (pgdata, dbt/profiles.yml, dbt/target, agent/eval/results, reports, *.parquet, raw/).
- `metrics/recorder.py` — 신규.
- `metrics/portfolio_metrics.md` — 신규 (TBD 템플릿).
- `metrics/run_results.jsonl` — 신규 빈 파일.
- `docs/session_log/README.md` — 신규.
- `docs/session_log/2026-04-16_session-01_bootstrap.md` — 본 파일.
- 다수 디렉토리에 `.gitkeep` 추가.

## Open questions
- **Superset 메타DB 분리 전략**: 같은 Postgres 컨테이너의 별도 DB 로 분리 (블루프린트 따름). Phase 1 시 init SQL 에서 `CREATE DATABASE superset_meta` 처리 예정.
- **LLM provider 우선순위**: 블루프린트는 Gemini 2.5 Flash 1순위, Claude Haiku 4.5 fallback. 사용자 의향 재확인 필요할 수 있음.
- **Superset 오픈소스 기여**: 시간 분배 어떻게 할지 (Phase 9 vs 평행).

## Metrics
- 이번 세션은 부트스트랩이라 측정 데이터 없음. 다음 세션부터 `metrics/run_results.jsonl` 에 append 시작.

## Next session — start here
1. **Phase 1 시작 가능 상태 확인**:
   - `uv sync` 실행 → `make help` 정상 출력 확인
   - Docker Desktop 메모리 12GB 할당 확인 (Settings → Resources)
2. **Phase 1 본격 작업** — 블루프린트 섹션 5 의 **Phase 1 Claude Code 프롬프트 템플릿** 그대로 사용:
   - `docker-compose.yml` 작성 (postgres + pgvector / airflow{web,scheduler,worker} / redis / superset)
   - `infra/postgres/init/01_extensions.sql` (vector, pg_trgm, pg_stat_statements + adinsight / airflow_meta / superset_meta DB 생성)
   - `infra/airflow/Dockerfile` + `requirements.txt`
   - `infra/superset/Dockerfile` + `superset_config.py`
   - `dags/sample_smoke_test.py` (`SELECT 1` from Postgres)
   - `make up` → Airflow / Superset UI 접속 확인
3. 완료 후 새 세션 로그 `2026-XX-XX_session-02_phase1-compose.md` 작성.
