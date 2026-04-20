# Session 04 — Phase 1 스택 기동 완료 (2026-04-20)

**Phase**: Phase 1 — 환경 셋업
**Duration**: ~2h
**Operator**: Yeon (with Claude Code)

## Goals
- `make up` 실행 → 전체 스택 healthy 확인
- Smoke DAG 트리거 → 성공 확인
- 포트폴리오 스크린샷 캡처 + GitHub 푸시

## Done
- [x] `make up` 실행 → 버그 3개 디버깅 후 전체 스택 기동 성공
- [x] Smoke DAG 트리거 → success (1s)
- [x] 스크린샷 2장: `docs/images/01_airflow_ui.png`, `01_smoke_test_success.png`
- [x] `metrics/run_results.jsonl` Phase 1 live 항목 append
- [x] `docs/portfolio_draft.md` Phase 1 메트릭 실측값 업데이트
- [x] `docs/learning/session-04_concepts.md` 신규 작성
- [x] `docs/session_log/README.md` 인덱스 추가
- [x] CLAUDE.md §9 세션 종료 규칙에 learning 폴더 항목 추가
- [x] CLAUDE.md §10·§11 갱신
- [x] GitHub 푸시 완료 (`10245d9`)

## Decisions
- **Airflow webserver 포트 8080 → 8081**: Docker Desktop 자체가 8080 점유 중
- **`02_databases.sh` chmod +x**: git clone 후 실행 권한 유실 방지 필요 → `.gitattributes` 추가 고려 (Phase 2 전)

## Files changed
- `infra/airflow/Dockerfile` — FROM 이후 ARG 재선언 추가
- `infra/airflow/requirements.txt` — provider 버전 핀 제거, pgvector 0.3.2→0.3.1
- `docker-compose.yml` — webserver 포트 8081로 변경
- `infra/postgres/init/02_databases.sh` — chmod +x (실행 권한 부여)
- `docs/images/01_airflow_ui.png` — 신규
- `docs/images/01_smoke_test_success.png` — 신규
- `metrics/run_results.jsonl` — Phase 1 live 항목 append
- `docs/portfolio_draft.md` — Phase 1 메트릭 TBD → 실측값
- `docs/learning/session-04_concepts.md` — 신규
- `CLAUDE.md` — §9 learning 항목 추가, §10·§11 갱신

## Concepts taught (학습 강화)
- **Docker ARG 스코프** — FROM 경계에서 ARG 소멸, FROM 이후 재선언 필요. 베이스 이미지 ENV가 ARG를 가리는 현상
- **pip constraints vs requirements 분업** — Airflow provider는 constraints에 위임, 일반 패키지만 requirements에 직접 핀
- **파일 실행 권한 (`chmod +x`)** — `-rw-r--r--` vs `-rwxr-xr-x`, docker-entrypoint.sh가 `.sh` 파일 실행 시 권한 확인
- **Postgres init 스크립트 실행 조건** — 볼륨이 비어있을 때만 `/docker-entrypoint-initdb.d/` 실행, 볼륨 재사용 시 스킵
- **Docker 볼륨 재초기화** — `docker volume rm`으로 볼륨 삭제 후 재기동

## Portfolio assets added
- **이미지**: `docs/images/01_airflow_ui.png`, `01_smoke_test_success.png`
- **Metrics**: `metrics/run_results.jsonl` — make_up_seconds: 10.7, containers_healthy: 8, smoke_dag_duration_sec: 1
- **portfolio_draft.md**: Phase 1 메트릭 칸 완성

## Open questions
- `02_databases.sh` 실행 권한을 `.gitattributes`로 영구 보존할지 검토 (`text eol=lf` + `chmod`)

## Metrics
- `make up` 기동 시간: **10.7s** (이미지 캐시 후)
- 이미지 총 크기: **8.7 GB**
- 컨테이너 healthy: **8/8**
- Smoke DAG 실행 시간: **1s**

## Next session — start here
1. **Phase 2 진입**: `docs/adinsight_project_blueprint.md` §Phase2 Claude Code 프롬프트 확인
2. **스키마 ERD 설계 먼저** — `dim_creator`, `dim_advertiser`, `dim_campaign`, `fact_post`, `fact_post_metrics_daily`, `fact_campaign_match`, `fact_payment` 7개 테이블
3. **파일 목록 confirm 후** `data_generation/generators/` 하위 모듈 가이드 모드로 작성 시작
