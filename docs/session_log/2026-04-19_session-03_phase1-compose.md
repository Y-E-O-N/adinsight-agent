# Session 03 — Phase 1 docker-compose 스택 구축 (2026-04-19)

**Phase**: Phase 1 — 환경 셋업 & 스켈레톤
**Duration**: ~3h
**Operator**: Yeon (with Claude Code)

## Goals
- Phase 1 Docker Compose 스택 8개 파일 작성
- 가이드 모드(Yeon 직접 타이핑) 전환 및 워크플로 확립
- YAML 구조 검증

## Done
- [x] **가이드 모드 전환 결정** — CLAUDE.md §6 갱신, `memory/feedback_guided_mode.md` 신규
- [x] `dags/sample_smoke_test.py` — Airflow TaskFlow API smoke DAG (3차 수정 후 통과)
- [x] `infra/postgres/init/01_extensions.sql` — vector / pg_trgm / pg_stat_statements
- [x] `infra/postgres/init/02_databases.sh` — airflow_meta · superset_meta DB + agent_readonly role (\gexec + DO 블록)
- [x] `infra/airflow/requirements.txt` — 4개 패키지 버전 pin
- [x] `infra/airflow/Dockerfile` — constraints 파일 기반 pip install
- [x] `infra/superset/Dockerfile` — USER root → pip → USER superset 패턴
- [x] `infra/superset/superset_config.py` — os.environ, f-string, FEATURE_FLAGS
- [x] `docker-compose.yml` — 9개 서비스, YAML 앵커, healthcheck, depends_on condition (4섹션 분할 작성)
- [x] `docker compose config --quiet` YAML 검증 통과 (에러 0건, 경고는 .env 없어서 예상된 결과)
- [x] `docs/adr/001-single-postgres-stack.md` 작성
- [x] `README.md` Quick Start 섹션 실제 내용으로 갱신
- [x] `metrics/run_results.jsonl` append
- [x] `docs/daily_log.md` 2026-04-19 항목 추가

## Decisions
- **가이드 모드 채택**: Yeon 이 초보자이며 장기 기억·면접 답변력을 위해 프로덕션 파일 직접 타이핑. Claude 는 매우 상세한 설명 + 참고 스니펫 + 리뷰만.
- **기초 파일부터 순서**: smoke DAG → SQL → sh → requirements → Dockerfile × 2 → config.py → compose. 각 파일 이해 후 종합하는 구조.
- **`.sh` 채택 (02_databases)**: `.sql` 은 bash 변수 치환 불가 → 환경변수 주입에 `.sh` 필요. 공식 Postgres 이미지 권장 패턴.
- **Flower + Triggerer 포함**: 실무 Airflow 스택 표준 컴포넌트. 포트폴리오에 모니터링 UI 캡처 추가 가치.
- **단일 Postgres 컨테이너**: ADR 001 참조. 로컬 환경 리소스 절약 + 운영 단순성.

## Files changed
- `dags/sample_smoke_test.py` — 신규
- `infra/postgres/init/01_extensions.sql` — 신규
- `infra/postgres/init/02_databases.sh` — 신규 (원래 .sql 계획에서 .sh 로 변경)
- `infra/airflow/requirements.txt` — 신규
- `infra/airflow/Dockerfile` — 신규
- `infra/superset/Dockerfile` — 신규
- `infra/superset/superset_config.py` — 신규
- `docker-compose.yml` — 신규
- `docs/adr/001-single-postgres-stack.md` — 신규
- `README.md` — Quick Start 섹션 실제 내용으로 갱신, Phase 1 진행 상태 업데이트
- `metrics/run_results.jsonl` — Phase 1 완료 항목 append
- `docs/daily_log.md` — 2026-04-19 항목 추가
- `CLAUDE.md` — §6 가이드 모드 규칙 추가
- `memory/feedback_guided_mode.md` — 신규
- `memory/MEMORY.md` — 인덱스 1줄 추가

## Concepts taught (학습 강화)
- **Airflow DAG / TaskFlow API** — `@dag` 데코레이터, `schedule=None`, `catchup=False`, `start_date` 리터럴 규칙, `SQLExecuteQueryOperator` vs deprecated `PostgresOperator`
- **Airflow Connection 주입** — `AIRFLOW_CONN_*` env var 패턴
- **CeleryExecutor 아키텍처** — Scheduler → Redis 큐 → Celery Worker 흐름, Flower 모니터링
- **Celery vs Thread** — 레이어 차이 (분산 프로세스 vs 단일 프로세스 내 동시성)
- **Docker healthcheck CMD vs CMD-SHELL** — shell 유무, `$${HOSTNAME}` 이스케이프
- **Dockerfile 패턴** — `ARG` 스코프(FROM 앞/뒤), `USER root → USER 복귀`, `--no-cache-dir`, constraints 파일
- **YAML anchor (`&` / `*` / `<<:`)** — Airflow 5개 서비스 공통 설정 재사용
- **`>-` block scalar** — 긴 연결 문자열 여러 줄 작성
- **`\gexec` 트릭** — Postgres `CREATE DATABASE IF NOT EXISTS` 흉내
- **DO 블록 + dollar-quoting** — `DO $$ ... $$;`, bash heredoc 에서 `\$\$` 이스케이프
- **GRANT 3단 계층** — CONNECT → USAGE → SELECT + `ALTER DEFAULT PRIVILEGES`
- **Superset** — BI 대시보드 도구, `superset_config.py` import 메커니즘
- **bash strict mode** — `set -euo pipefail`
- **heredoc** — `<<-EOSQL`, 변수 확장 여부 (`<<'EOF'` vs `<<EOF`)

## Portfolio assets added
- **ADR**: `docs/adr/001-single-postgres-stack.md` — 단일 Postgres 컨테이너 결정 근거
- **README**: Quick Start 섹션 완성 (7단계 실행 절차)
- **Metrics**: `metrics/run_results.jsonl` Phase 1 항목 (YAML 검증 통과, 파일 수 8개)
- **Daily log**: `docs/daily_log.md` 2026-04-19 항목
- **스크린샷 대기**: `make up` 후 `docker compose ps` → `docs/images/01_compose_ps.png` (다음 세션)

## Open questions
- `make up` 실제 기동 시간 측정 미완 (이미지 pull 필요) → 다음 세션 시작 전에 Yeon 이 직접 `time make up` 실행 권장
- Docker Desktop 메모리 12GB 할당 확인 필요
- Superset 4.0.2 arm64 이미지 실제 기동 확인 필요

## Metrics
- 파일 작성: 8개 (Yeon 직접 타이핑)
- 오타·수정 이력: smoke DAG 3회, postgres sh 2회, compose 각 섹션 1~2회
- YAML 검증: 에러 0건

## Next session — start here
1. **전제 확인**:
   ```bash
   # Docker Desktop 메모리 12GB 설정 확인
   cp .env.example .env   # .env 아직 없으면
   # .env 열어서 비밀번호 설정
   ```
2. **스택 기동 + 메트릭 측정**:
   ```bash
   time make up           # 기동 시간 기록 → portfolio_draft.md Phase 1
   make ps                # 모든 서비스 healthy 확인
   docker system df       # 이미지 총 크기 기록
   ```
3. **스크린샷 캡처** → `docs/images/01_compose_ps.png`
4. **Smoke test**: Airflow UI `sample_smoke_test` DAG 트리거 → 성공 확인
5. **Superset 초기화**: `make superset-init`
6. **portfolio_draft.md Phase 1 칸 채우기** (기동 시간, 이미지 크기)
7. **Phase 1 완전 완료 확인 후 Phase 2 진입**
