# ADR 001 — 단일 Postgres 컨테이너에 warehouse / airflow_meta / superset_meta 공존

**날짜**: 2026-04-19
**상태**: 수용(Accepted)
**결정자**: Yeon (with Claude Code, Session 03)

---

## 배경

Phase 1 에서 로컬 docker-compose 스택을 구성할 때 다음 3개의 Postgres 데이터베이스가 필요하다:

1. **adinsight** — 메인 데이터 웨어하우스 (raw · staging · marts · ai_native)
2. **airflow_meta** — Airflow 메타데이터 (DAG 실행 이력 · 커넥션 · 변수)
3. **superset_meta** — Superset 메타데이터 (대시보드 · 차트 · 유저)

이를 **단일 Postgres 컨테이너** 에 여러 DB 로 분리할지, **서비스별로 별도 컨테이너**로 분리할지 결정이 필요했다.

---

## 결정

**단일 Postgres 컨테이너 (`pgvector/pgvector:pg16`) 에 3개 DB 를 논리적으로 분리**하기로 한다.
- `adinsight` (POSTGRES_DB 기본값, 웨어하우스)
- `airflow_meta` (Airflow 메타, `02_databases.sh` 에서 생성)
- `superset_meta` (Superset 메타, `02_databases.sh` 에서 생성)

---

## 근거

### 선택한 이유 (단일 컨테이너)

| 항목 | 설명 |
|---|---|
| **리소스** | MacBook 로컬 환경 (Docker Desktop 12GB 할당). 컨테이너 3개면 각각 최소 256MB+ 오버헤드. 단일 컨테이너로 ~600MB 절약. |
| **운영 단순성** | docker-compose 서비스 수 감소 (9개 → 7개). `make psql` 한 곳으로 접속. |
| **pgvector 일원화** | `vector` · `pg_trgm` · `pg_stat_statements` 확장은 한 번만 설치. 컨테이너 간 설정 불일치 없음. |
| **학습 우선** | 포트폴리오 목적의 로컬 환경 — 운영 격리보다 "동작하는 스택으로 빠르게 실습" 이 우선. |

### 대안과 기각 이유

| 대안 | 기각 이유 |
|---|---|
| **3개 Postgres 컨테이너 분리** | 로컬 메모리 압박, compose 복잡도 증가, pgvector 3번 설정 — 학습 오버헤드 대비 실익 없음 |
| **airflow_meta 는 SQLite** | Airflow CeleryExecutor 는 SQLite 미지원 (동시 쓰기 이슈). 운영 환경 유사성 ↓ |
| **superset_meta 를 SQLite** | Phase 5 Superset 대시보드 성능 측정 시 메타 조회 병목 가능성. 일관성을 위해 Postgres 유지. |

---

## 트레이드오프

| 장점 | 단점 |
|---|---|
| 리소스 절약 · 운영 단순 | DB 간 완전한 프로세스 격리 불가 (한 컨테이너 크래시 시 3개 DB 모두 영향) |
| pgvector 일원 관리 | 운영 환경에서는 각 시스템이 별도 RDS 인스턴스를 가지는 게 표준 |
| 빠른 부트스트랩 | Postgres 버전 충돌 시 모든 DB 동시 영향 |

**운영 환경과의 차이**: 실제 데이터 플랫폼에서는 웨어하우스(RDS/Aurora) · Airflow 메타(별도 RDS) · Superset 메타(별도 RDS 또는 SQLite) 를 분리하는 것이 일반적. 이 결정은 **로컬 개발 환경 한정**이며, 인프라 코드를 분리 구조로 마이그레이션하는 것은 Phase 9 에서 검토.

---

## 결과

- `docker-compose.yml` 에 `postgres` 서비스 1개
- `infra/postgres/init/02_databases.sh` 에서 `airflow_meta` · `superset_meta` 추가 생성
- `agent_readonly` role 도 동일 컨테이너에 생성 (Phase 6 Text2SQL Agent 용)

---

## Known Limitations

- 단일 Postgres 컨테이너 장애 시 Airflow · Superset 동시 다운
- 로컬 볼륨(`postgres_data`) 삭제 시 3개 DB 데이터 동시 손실 → `make up` 전 `docker volume ls` 확인 권장
- 운영 이관 시 각 DB 를 개별 인스턴스로 분리하는 마이그레이션 필요
