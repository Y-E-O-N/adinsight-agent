# Session 03 개념·관계 정리 — Phase 1 Docker Compose (2026-04-19)

> 이 세션에서 작성한 8개 파일 각각의 핵심 개념, 그리고 컴포넌트 간 관계도.

---

## 목차

1. [파일별 핵심 개념](#1-파일별-핵심-개념)
2. [컴포넌트 관계도](#2-컴포넌트-관계도)
3. [오타·실수 패턴](#3-오타실수-패턴)
4. [용어 빠른 참조](#4-용어-빠른-참조)

---

## 1. 파일별 핵심 개념

---

### `dags/sample_smoke_test.py`

**목적**: 스택 기동 후 Airflow → Postgres 연결이 정상인지 확인하는 최소 DAG.

```python
from __future__ import annotations       # Python 3.10+ 타입힌트 하위호환
from datetime import datetime
from airflow.decorators import dag
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

@dag(
    dag_id="sample_smoke_test",
    schedule=None,                        # 수동 트리거만 (자동 스케줄 없음)
    start_date=datetime(2026, 1, 1),      # 과거 고정값 — relative 금지
    catchup=False,                        # start_date 이후 밀린 실행 안 함
    tags=["phase1", "smoke"],
)
def sample_smoke_test():
    SQLExecuteQueryOperator(
        task_id="select_one",
        conn_id="warehouse",              # AIRFLOW_CONN_WAREHOUSE 환경변수로 주입
        sql="SELECT 1;",
    )

sample_smoke_test()   # ← 이 줄 없으면 DAG 등록 안 됨! 가장 흔한 실수
```

**핵심 포인트**:
- `SQLExecuteQueryOperator` = 현재 권장. `PostgresOperator` 는 deprecated.
- `conn_id="warehouse"` → Airflow 가 `AIRFLOW_CONN_WAREHOUSE` 환경변수를 자동으로 찾음
- 파일 끝 함수 호출 누락 = 조용한 실패 (에러 없이 DAG 목록에 안 뜸)
- `catchup=False`: 없으면 `start_date` 부터 현재까지 밀린 실행을 한꺼번에 시도함

---

### `infra/postgres/init/01_extensions.sql`

**목적**: Postgres 컨테이너 최초 기동 시 확장 기능 설치.

```sql
CREATE EXTENSION IF NOT EXISTS vector;             -- pgvector: 임베딩 벡터 저장·검색
CREATE EXTENSION IF NOT EXISTS pg_trgm;            -- 트라이그램: LIKE 검색 가속
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- 슬로우 쿼리 추적
```

**동작 방식**: `docker-entrypoint-initdb.d/` 안의 파일은 컨테이너 **최초 기동 시 1회만** 알파벳 순서 실행.
- `01_extensions.sql` → `02_databases.sh` 순서로 실행됨
- Postgres 볼륨(`postgres_data`)이 이미 있으면 재실행 안 됨

---

### `infra/postgres/init/02_databases.sh`

**목적**: airflow_meta · superset_meta DB 생성 + agent_readonly 롤 생성.

**왜 `.sql` 이 아닌 `.sh`?**
- `.sql` 파일에서는 bash 변수 치환(`${AIRFLOW_DB}`) 불가
- 환경변수로 DB명·패스워드를 주입하려면 `.sh` 필요
- 공식 Postgres Docker 이미지 권장 패턴

**핵심 패턴**:

```bash
#!/usr/bin/env bash
set -euo pipefail   # e: 에러 시 즉시 중단 / u: 미정의 변수 에러 / o pipefail: 파이프 에러 전파

psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
  -- \gexec 트릭: Postgres 에 IF NOT EXISTS DATABASE 가 없어서 이렇게 우회
  SELECT 'CREATE DATABASE ${AIRFLOW_DB}'
   WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${AIRFLOW_DB}')\gexec

  -- DO 블록: PL/pgSQL 익명 블록으로 조건부 실행
  DO \$\$          -- heredoc 안에서 $$ → \$\$ 로 이스케이프
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${AGENT_DB_USER}') THEN
      CREATE ROLE ${AGENT_DB_USER} WITH LOGIN PASSWORD '${AGENT_DB_PASSWORD}';
    END IF;
  END
  \$\$;            -- 세미콜론 필수
EOSQL
```

**GRANT 3단 계층** (Text2SQL Agent 용 최소 권한):

```sql
GRANT CONNECT ON DATABASE adinsight TO agent_readonly;          -- 1단: DB 접속
GRANT USAGE ON SCHEMA public TO agent_readonly;                 -- 2단: 스키마 진입
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;  -- 3단: 읽기
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO agent_readonly;                     -- 앞으로 만들 테이블에도 적용
```

---

### `infra/airflow/requirements.txt`

**목적**: Airflow 기본 이미지에 없는 패키지를 추가 설치 목록으로 관리.

```
apache-airflow-providers-postgres==5.10.2
apache-airflow-providers-common-sql==1.14.2
psycopg2-binary==2.9.9
pgvector==0.3.2
```

**왜 버전을 고정?** 버전 미고정 시 나중에 이미지를 다시 빌드하면 다른 버전이 설치될 수 있음 → 재현 가능한 빌드를 위해 핀.

---

### `infra/airflow/Dockerfile`

**핵심 패턴 — ARG 스코프**:

```dockerfile
# FROM 앞 ARG: FROM 의 이미지 이름에만 유효
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# FROM 이후 레이어에서 쓰려면 다시 선언해야 함 (스코프 리셋)
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11
ARG CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/\
constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    -r /tmp/requirements.txt \
    -c "${CONSTRAINTS_URL}"
```

**constraints 파일의 역할**: Airflow 공식 팀이 "이 버전 조합은 테스트 완료" 라고 보증한 파일.
`-c` 옵션으로 넘기면 pip 가 이 파일의 버전 범위 안에서만 설치 → 의존성 충돌 방지.

---

### `infra/superset/Dockerfile`

**핵심 패턴 — USER 전환**:

```dockerfile
FROM apache/superset:4.0.2
ENV PIP_NO_CACHE_DIR=1
USER root               # pip 설치는 root 권한 필요
RUN pip install psycopg2-binary==2.9.9 pgvector==0.3.2
USER superset           # 보안: 애플리케이션은 최소 권한 유저로 실행
```

**원칙**: 컨테이너를 root 로 실행하면 컨테이너 탈출 시 호스트 파일시스템 접근 가능.
작업이 끝나면 반드시 비root 유저로 복귀.

---

### `infra/superset/superset_config.py`

**목적**: Superset 이 시작 시 이 파일을 import 해서 DB 연결·시크릿키 등 설정을 읽음.

```python
import os   # 표준 라이브러리는 소문자 (import OS ❌)

_db_user     = os.environ.get("POSTGRES_USER", "postgres")
_db_password = os.environ.get("POSTGRES_PASSWORD", "")
_db_host     = os.environ.get("POSTGRES_HOST", "postgres")
_db_port     = os.environ.get("POSTGRES_PORT", "5432")
_db_name     = os.environ.get("SUPERSET_META_DB", "superset_meta")

SQLALCHEMY_DATABASE_URI = (              # 괄호로 여러 줄 이어쓰기
    f"postgresql+psycopg2://{_db_user}:{_db_password}"
    f"@{_db_host}:{_db_port}/{_db_name}"
)

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me-in-production")

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ALERT_REPORTS": False,   # ALERT (경보), ALTER (SQL 명령) 와 혼동 주의
}
```

**시크릿 주입 흐름**: `.env` → Compose `env_file:` → 컨테이너 환경변수 → `os.environ.get()`.
시크릿을 코드에 하드코딩하면 git 에 노출되므로 절대 금지.

---

### `docker-compose.yml`

**핵심 패턴 — YAML 앵커**:

```yaml
# x- 접두사: Compose 가 서비스로 인식 안 함 (확장 필드 선언 전용)
x-airflow-common:
  &x-airflow-common          # & = 앵커 정의 (이 블록에 북마크)
  image: ${AIRFLOW_IMAGE:-apache/airflow:2.9.3-python3.11}
  environment:
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    # ... 공통 환경변수 ...

services:
  airflow-webserver:
    <<: *x-airflow-common    # * = 앵커 참조, <<: = 블록 머지
    ports:
      - "8080:8080"          # 이 서비스만의 추가 설정
  airflow-scheduler:
    <<: *x-airflow-common    # 같은 앵커 재사용
    command: scheduler
```

**왜 쓰나?** webserver / scheduler / worker / triggerer 4개 서비스가 동일한 이미지·환경변수 공유.
앵커 없으면 4번 복붙 → 환경변수 하나 바꿀 때 4곳 모두 수정해야 함.

**`>-` block scalar**:
```yaml
# 긴 문자열을 여러 줄로 작성 — >- 는 줄바꿈을 공백으로 접어 한 줄로 만듦
AIRFLOW_CONN_WAREHOUSE: >-
  postgresql+psycopg2://airflow:${POSTGRES_PASSWORD}
  @postgres:5432/adinsight
# 실제 값: postgresql+psycopg2://airflow:...@postgres:5432/adinsight (한 줄)
```

---

## 2. 컴포넌트 관계도

### 전체 스택 관계

```
.env 파일 (시크릿·설정값)
  │ env_file: 로 주입
  ▼
docker-compose.yml
  │
  ├── postgres (pgvector/pgvector:pg16)
  │     ├── 01_extensions.sql ──► vector, pg_trgm, pg_stat_statements 설치
  │     └── 02_databases.sh   ──► airflow_meta, superset_meta DB + agent_readonly 롤
  │
  ├── redis ──► 메시지 큐 (Airflow Scheduler ↔ Celery Worker 중계)
  │
  ├── airflow-init ──► DB 마이그레이션 1회 후 종료
  │
  ├── airflow-webserver (:8080) ─┐
  ├── airflow-scheduler          ├── x-airflow-common 앵커로 설정 공유
  ├── airflow-worker  ◄──Redis──┘
  ├── airflow-triggerer
  │
  ├── flower (:5555) ──► Celery Worker 상태 웹 모니터링
  │
  └── superset (:8088)
        └── superset_config.py ──► Postgres superset_meta DB 연결
```

### Airflow task 실행 흐름

```
dags/sample_smoke_test.py
  │ Scheduler 가 파싱 → 실행 스케줄 결정
  ▼
airflow-scheduler
  │ "select_one task 지금 실행" 명령을 큐에 넣음
  ▼
redis (메시지 큐)
  │ airflow-worker 가 꺼내서 실행
  ▼
airflow-worker (Celery Worker)
  │ conn_id="warehouse" → AIRFLOW_CONN_WAREHOUSE 환경변수 참조
  ▼
postgres:5432/adinsight (warehouse DB)
  │ SELECT 1 실행 → 결과 반환
  ▼
postgres:5432/airflow_meta
  │ 실행 성공 이력 기록
  ▼
airflow-webserver UI (:8080) ──► 초록색 task 표시
```

### Connection 주입 흐름

```
.env
  AIRFLOW_CONN_WAREHOUSE=postgresql+psycopg2://airflow:...@postgres:5432/adinsight
    │ docker-compose env_file:
    ▼
컨테이너 환경변수
    │ Airflow 내부: AIRFLOW_CONN_* 패턴을 자동으로 connection 으로 파싱
    ▼
conn_id="warehouse" 로 접근 가능
    │
    ▼
SQLExecuteQueryOperator(conn_id="warehouse", sql="SELECT 1;")
```

### Postgres 스키마·DB 구조

```
postgres 컨테이너 (단일)
  │
  ├── adinsight DB (웨어하우스)
  │     ├── raw        ← 원본 보존
  │     ├── staging    ← 정제·PII 해시
  │     ├── intermediate
  │     ├── marts      ← Kimball star schema
  │     └── ai_native  ← LLM 친화 비정규화 (Phase 4 ⭐)
  │
  ├── airflow_meta DB (Airflow 메타데이터)
  │     └── DAG 실행 이력, 커넥션, 변수 등
  │
  └── superset_meta DB (Superset 메타데이터)
        └── 대시보드, 차트, 유저 정보
```

---

## 3. 오타·실수 패턴

이번 세션 발생 오류 유형별 정리. 다음 파일 작성 시 의식적으로 확인.

### 대소문자 혼동

| 잘못된 것 | 올바른 것 | 발생 영향 |
|---|---|---|
| `import OS` | `import os` | `ModuleNotFoundError` |
| `From apache/superset` | `FROM apache/superset` | Dockerfile 관례 위반 (동작은 하지만) |

### 철자 오타

| 잘못된 것 | 올바른 것 | 발생 영향 |
|---|---|---|
| `AGEND_DB_PASSWORd` | `AGENT_DB_PASSWORD` | `set -u` 로 즉시 crash |
| `pgverctor` | `pgvector` | pip 설치 실패 |
| `postgers:` | `postgres:` | Compose 서비스 참조 에러 |
| `localhosst` | `localhost` | healthcheck 항상 실패 |
| `comand:` | `command:` | Compose 가 키 무시 → init 실행 안 됨 |
| `adsight-airflow-init` | `adinsight-airflow-init` | 컨테이너 이름 불일치 |
| `"ALTER_REPORTS"` | `"ALERT_REPORTS"` | Superset 플래그 미적용 |

### 구두점·문법 누락

| 잘못된 것 | 올바른 것 | 발생 영향 |
|---|---|---|
| `catchup=False` 뒤 쉼표 없음 | `catchup=False,` | 다음 인자 파싱 에러 |
| `\$\$` 뒤 세미콜론 없음 | `\$\$;` | DO 블록 SQL 에러 |
| `SQLExecuteQueryOperator9` | `SQLExecuteQueryOperator(` | `SyntaxError` |

### 구조 실수

| 실수 | 원인 | 올바른 방법 |
|---|---|---|
| `sample_smoke_test()` 호출 누락 | DAG 파일 끝 함수 호출 필요한 것 몰랐음 | 파일 끝 항상 확인 |
| `redis:` 두 번 중첩 | 서비스 이름 vs 이미지 이름 혼동 | 서비스 이름은 `services:` 아래 한 번만 |
| shebang 앞 빈 줄 | 에디터 기본 빈 줄 | `.sh` 파일 첫 줄 반드시 `#!/usr/bin/env bash` |

### 파일 저장 전 체크리스트

```
□ 첫 줄: shebang(sh) 또는 import(py) 또는 FROM(Dockerfile) 바로 시작
□ 대소문자: import, FROM, ENV, RUN, USER 키워드 확인
□ 구두점: trailing comma, 세미콜론, 닫는 괄호·따옴표
□ 환경변수명 오타: _PASSWORD, _USER, _DB 등 확인
□ DAG 파일: 마지막 줄에 함수 호출 `dag_func()` 있는지 확인
```

---

## 4. 용어 빠른 참조

| 용어 | 정의 | 관련 파일 |
|---|---|---|
| **DAG** | Directed Acyclic Graph. Airflow 작업 흐름 단위 | `dags/*.py` |
| **TaskFlow API** | `@dag`, `@task` 데코레이터로 DAG 를 파이썬 함수처럼 작성 | `sample_smoke_test.py` |
| **catchup** | `start_date` 이후 밀린 실행 소급 여부. `False` = 소급 없음 | `sample_smoke_test.py` |
| **CeleryExecutor** | Airflow task 를 Celery Worker 에 분산 실행하는 실행자 | `docker-compose.yml` |
| **pgvector** | Postgres 확장. 벡터(임베딩) 저장 + 유사도 검색 (`<->` 연산자) | `01_extensions.sql` |
| **pg_trgm** | 트라이그램 기반 LIKE/ILIKE 검색 가속 인덱스 확장 | `01_extensions.sql` |
| **`\gexec`** | psql 메타명령. 쿼리 결과를 SQL 로 실행. `CREATE DATABASE IF NOT EXISTS` 우회에 사용 | `02_databases.sh` |
| **DO 블록** | PL/pgSQL 익명 블록. 조건부 DDL 실행 | `02_databases.sh` |
| **dollar-quoting** | `$$` 로 SQL 문자열 감싸기. heredoc 안에서는 `\$\$` | `02_databases.sh` |
| **bash strict mode** | `set -euo pipefail`. 에러 즉시 중단 + 미정의 변수 에러 + 파이프 에러 전파 | `02_databases.sh` |
| **heredoc** | `<<-EOSQL ... EOSQL`. 여러 줄 문자열 작성. `-` 는 앞 탭 허용 | `02_databases.sh` |
| **constraints 파일** | Airflow 가 테스트한 의존성 버전 조합 보증 파일 | `airflow/Dockerfile` |
| **ARG 스코프** | Dockerfile `ARG` 는 `FROM` 앞뒤로 스코프 분리. `FROM` 이후 재선언 필요 | `airflow/Dockerfile` |
| **YAML anchor** | `&name` 정의, `*name` 참조, `<<:` 머지. 반복 설정 재사용 | `docker-compose.yml` |
| **`>-` scalar** | YAML 블록 스칼라. 여러 줄 작성, 줄바꿈을 공백으로 접음 | `docker-compose.yml` |
| **BI** | Business Intelligence. 데이터를 차트·대시보드로 시각화해 의사결정에 활용 | Superset |
| **healthcheck** | 컨테이너 정상 여부 주기적 확인. `depends_on: condition: service_healthy` 의 전제 | `docker-compose.yml` |
| **`env_file`** | Compose 서비스가 `.env` 파일을 환경변수로 로드하는 설정 키 | `docker-compose.yml` |

---

*다음: `session-04_concepts.md` (Phase 2 데이터 수집·적재)*
