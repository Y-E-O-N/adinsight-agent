---
title: "AdInsight Agent 사전학습 — 실전 중급편"
subtitle: "코드·함정·프로젝트 1:1 매핑"
author: "for Yeon"
---

# 이 문서의 위치

- **입문편**(01_beginner.md): "이게 뭐고 왜 쓰는지" 감 잡기
- **중급편**(이 문서): "실제 어떻게 쓰는지" + "AdInsight Agent에서 어디에 쓰이는지"
- **완전판**(03_complete.md): 심화·안티패턴·면접 Q&A

중급편은 **코드 중심**입니다. 그냥 읽는 것보다 **따라치면서** 읽기를 강력 추천. 각 섹션 끝에 *"AdInsight Agent의 어디에 적용되는가"* 를 반드시 적어두었습니다.

---

# 1. Docker / docker-compose 중급

## 1-1. 컨테이너 라이프사이클을 몸으로 익히기

```bash
# 이미지 받기
docker pull postgres:16

# 컨테이너 한 번 띄우기 (detached)
docker run -d --name pg16 -e POSTGRES_PASSWORD=dev -p 5432:5432 postgres:16

# 살아있는지 확인
docker ps

# 들어가 보기
docker exec -it pg16 psql -U postgres

# 로그 보기
docker logs -f pg16

# 멈춤 / 시작 / 삭제
docker stop pg16
docker start pg16
docker rm -f pg16
```

**포인트**: `docker run`은 "이미지로부터 컨테이너를 생성 + 시작"이 묶인 명령. `docker start`는 이미 있는 컨테이너를 다시 켜는 것. 이 둘을 섞어 쓰면 혼란스러움.

## 1-2. docker-compose.yml 실전 예시

AdInsight Agent에서 쓸 compose 파일의 축약 버전:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16   # arm64 지원
    container_name: adinsight-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: adinsight
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: adinsight-redis

  airflow-webserver:
    image: apache/airflow:2.9.3-python3.11
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_started }
    environment:
      AIRFLOW__CORE__EXECUTOR: CeleryExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://postgres:${POSTGRES_PASSWORD}@postgres/airflow
      AIRFLOW__CELERY__BROKER_URL: redis://redis:6379/0
      AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://postgres:${POSTGRES_PASSWORD}@postgres/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    user: "${AIRFLOW_UID}:0"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./dbt:/opt/dbt
    ports:
      - "8080:8080"
    command: webserver

  # airflow-scheduler, airflow-worker 도 비슷하게...

  superset:
    image: apache/superset:4.0.0
    ports:
      - "8088:8088"
    depends_on:
      postgres: { condition: service_healthy }

volumes:
  pgdata:
```

**꼭 눈에 익혀야 할 포인트**:

- `depends_on` + `condition: service_healthy` — 순서 제어. healthcheck가 있어야 제대로 동작.
- `environment` — 환경변수로 설정 주입. 민감한 값은 `.env` 파일에.
- `volumes` 두 종류:
  - **Named volume** (`pgdata:`) — Docker가 관리. 데이터 영속.
  - **Bind mount** (`./dags:/opt/airflow/dags`) — 내 맥 폴더를 컨테이너에 직접 연결. 개발 편리.
- `init:ro` 의 `:ro` — read-only. 컨테이너가 실수로 수정 못 하게.
- `user: "${AIRFLOW_UID}:0"` — Airflow의 유명한 권한 이슈 해결용. `.env`에 `AIRFLOW_UID=50000` 필수.

## 1-3. 자주 쓰는 명령어 레시피

```bash
# 전부 띄우기 (백그라운드)
docker compose up -d

# 특정 서비스만
docker compose up -d postgres redis

# 로그 따라가기
docker compose logs -f airflow-scheduler

# 컨테이너 안에 들어가기
docker compose exec postgres psql -U postgres -d adinsight
docker compose exec airflow-webserver bash

# 다 내리기
docker compose down

# 볼륨까지 싹 지우기 (초기화)
docker compose down -v

# 이미지 다시 빌드
docker compose build --no-cache

# 리소스 사용량
docker stats
```

## 1-4. 흔한 에러와 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `port is already allocated` | 포트 충돌 | `lsof -i :5432` 로 찾아 죽이기 |
| `permission denied` (Airflow logs) | UID 미설정 | `.env`에 `AIRFLOW_UID=50000` |
| `no space left on device` | Docker가 디스크 꽉 | `docker system prune -a --volumes` |
| `Exited (137)` | OOM 킬 | Docker Desktop 메모리 증가 |
| arm64 Mac에서 엄청 느림 | x86_64 이미지를 Rosetta로 돌림 | arm64 지원 이미지로 변경 |
| `could not translate host name "postgres"` | 서비스명 오타 or 네트워크 분리 | compose 안 서비스명으로 사용 |

## 1-5. 🎯 AdInsight Agent 연결
- 모든 컴포넌트(Postgres, Redis, Airflow×3, Superset)를 **하나의 compose 파일**로 관리
- `make up` = `docker compose up -d` + 안내 메시지
- 볼륨은 `pgdata` 하나(Postgres 데이터), 나머지는 bind mount (`./dags`, `./dbt`, `./logs`)
- Phase 1의 Claude Code 프롬프트를 실행하면 이 구조로 자동 생성됨

---

# 2. 데이터 파이프라인 설계 중급

## 2-1. 레이어별 역할을 한 번 더 선명하게

```
RAW           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              - 원본 "그대로". 절대 수정 금지
              - 컬럼명·타입·NULL 그대로 보존
              - schema는 "source_system_table" 식으로

STAGING       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              - 1:1 관계 (raw 1행 → staging 1행)
              - 타입 캐스팅, 컬럼명 snake_case
              - PII 마스킹/해싱
              - 기본 필터 (soft delete 제외 등)

INTERMEDIATE  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              - 조인, 집계, 윈도우 계산
              - 재사용 가능한 "중간 계산"
              - incremental 대상

MARTS         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              - 비즈 의미를 가진 dim/fact
              - 분석가·대시보드가 직접 사용
              - 변경 시 하위 영향 커서 신중해야

AI_NATIVE     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              - LLM Agent 전용
              - 비정규화 + semantic naming + rich metadata
              - "Agent가 헷갈리지 않도록" 디자인됨
```

## 2-2. 레이어 간 데이터 계약 (Data Contract)

**"이 컬럼은 항상 not null이다, 이 컬럼 값은 반드시 이 목록 안에 있다"** 같은 약속. dbt tests가 바로 이 contract의 실체화.

```yaml
# schema.yml
models:
  - name: stg_creators
    columns:
      - name: creator_id
        tests: [not_null, unique]
      - name: platform
        tests:
          - accepted_values:
              values: ['tiktok', 'instagram', 'youtube_shorts']
      - name: follower_count
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1000000000
```

## 2-3. "Raw는 건드리지 않는다" 의 진짜 의미
Raw에 수정이 가해지는 순간, 버그가 나도 **원본과 비교할 수가 없어** 디버깅이 지옥이 됩니다. raw는 **immutable(불변)** 로 취급하고, 필요하면 `raw_v2` 같은 새 스키마에 재수집.

## 2-4. Watermark(워터마크)
**"여기까지 처리했음"** 을 기록하는 장치. 증분 처리에 필수.

```sql
-- 예: 어제까지 처리. 오늘은 어제 이후만.
SELECT * FROM source
WHERE updated_at > (SELECT MAX(updated_at) FROM staging_table)
```

주의: `>` 와 `>=` 선택이 중요. `>` 는 같은 초 이벤트를 놓칠 수 있고, `>=` 는 중복이 될 수 있어요. 그래서 보통 **unique key + MERGE** 조합으로 safety.

## 2-5. Late-arriving Data (늦게 도착한 데이터)
오늘 기준으로 처리했는데, **3일 전 데이터가 방금 도착**하면? 정책 2가지:
1. **재처리 윈도우**: 최근 3일은 매일 다시 처리 (AdInsight Agent 방식)
2. **이벤트 타임 기준** 재분배: 복잡하지만 정확

## 2-6. 🎯 AdInsight Agent 연결
- `raw.tiktok_posts` → `staging.stg_posts` → `intermediate.int_post_daily` → `marts.fct_post_daily` → `ai_native.wide_daily_platform_summary`
- 각 레이어가 **dbt 폴더로 1:1 대응**: `models/staging/`, `models/intermediate/`, `models/marts/`, `models/ai_native/`

---

# 3. SQL 중급 — 실전 패턴

## 3-1. 윈도우 함수 마스터

### 패턴 A: Top-N per group
```sql
-- 카테고리별 Top 10 크리에이터
WITH ranked AS (
  SELECT
    creator_id, category, follower_count,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY follower_count DESC) AS rn
  FROM dim_creator
)
SELECT creator_id, category, follower_count
FROM ranked
WHERE rn <= 10;
```

### 패턴 B: 이동 평균 (7일)
```sql
SELECT
  date, creator_id,
  AVG(views) OVER (
    PARTITION BY creator_id ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS views_7d_avg
FROM fct_post_daily;
```

> **주의**: `ROWS`와 `RANGE` 차이. `ROWS`는 "물리적 행 수", `RANGE`는 "값의 범위". 시계열에선 대부분 `ROWS`.

### 패턴 C: 전일 대비 증감
```sql
SELECT
  date, views,
  views - LAG(views, 1) OVER (PARTITION BY creator_id ORDER BY date) AS diff_vs_yesterday,
  (views::FLOAT / NULLIF(LAG(views,1) OVER (PARTITION BY creator_id ORDER BY date), 0) - 1) * 100 AS pct_change
FROM fct_post_daily;
```

> **NULLIF 포인트**: 0으로 나눗셈 방지. 실무에서 자주 빠트리는 함정.

### 패턴 D: 누적합
```sql
SELECT
  date, spend,
  SUM(spend) OVER (PARTITION BY campaign_id ORDER BY date) AS cumulative_spend
FROM fct_campaign_daily;
```

## 3-2. EXPLAIN ANALYZE 읽는 법

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM fct_post_daily
WHERE date BETWEEN '2026-01-01' AND '2026-01-07'
  AND region = 'TW';
```

출력 예시 해석:
```
Seq Scan on fct_post_daily  (cost=0.00..185234.00 rows=42 width=120)
                            (actual time=0.021..1823.443 rows=156234 loops=1)
  Filter: ((date >= '2026-01-01') AND (date <= '2026-01-07') AND (region = 'TW'))
  Rows Removed by Filter: 19843766
  Buffers: shared hit=12 read=185222
Planning Time: 0.145 ms
Execution Time: 1850.332 ms
```

읽는 순서:
1. **Seq Scan**: 전체 스캔. 2천만 행 중에 15만 행만 필요한데 **전부 읽었음** → 인덱스 필요
2. **cost=... rows=42**: 플래너 예측. **rows=42 vs actual rows=156234** → 예측이 완전히 틀림 → `ANALYZE` 안 돌림?
3. **Buffers: read=185222**: 디스크에서 18만 블록 읽음. 느림의 주범.
4. **Execution Time: 1850ms** — 1.8초

**해결**: `CREATE INDEX ON fct_post_daily (region, date);` → 다시 EXPLAIN → Index Scan 로 바뀜 → ~20ms

## 3-3. 인덱스 전략 실전

```sql
-- AdInsight Agent에서 쓸 대표 인덱스들
-- 1) 날짜 기준 조회가 압도적으로 많은 큰 테이블 → BRIN (크기 작고 시계열에 적합)
CREATE INDEX ON fct_post_daily USING BRIN (date) WITH (pages_per_range = 64);

-- 2) 지역+날짜 필터가 섞여 들어오면 → 복합 B-tree
CREATE INDEX ON fct_post_daily (region, date);

-- 3) 조인 키 (창조자 ID) → B-tree
CREATE INDEX ON fct_post_daily (creator_id);

-- 4) jsonb 내부 필드 검색 → GIN
CREATE INDEX ON dim_campaign USING GIN (platform_mix);

-- 5) 문자열 부분 검색 → pg_trgm + GIN
CREATE INDEX ON dim_creator USING GIN (creator_handle gin_trgm_ops);
```

**주의**: 인덱스를 만들수록 INSERT/UPDATE가 느려지고 디스크도 먹습니다. "정말 필요한가?" 를 쿼리 로그(pg_stat_statements) 기반으로 판단.

## 3-4. 파티셔닝

큰 테이블을 "논리적으로 하나지만 물리적으로 여러 작은 테이블"로 쪼갬. 주로 날짜 기준.

```sql
CREATE TABLE fct_post_daily (
  date DATE NOT NULL,
  creator_id BIGINT,
  views BIGINT,
  ...
) PARTITION BY RANGE (date);

CREATE TABLE fct_post_daily_2026_01 PARTITION OF fct_post_daily
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

효과: `WHERE date = '...'` 쿼리가 **특정 파티션만** 스캔 (파티션 프루닝).

## 3-5. 🎯 AdInsight Agent 연결
- 20M 행 `fct_post_daily` 테이블이 **Phase 5에서 쿼리 최적화 실습 대상**
- BRIN 인덱스 + 사전 집계 테이블 + 파티셔닝으로 18s → 1s 수준으로 개선하는 게 면접 무기
- 윈도우 함수는 dbt `int_post_daily_ewma.sql` 같은 중간 모델에서 매번 씀

---

# 4. 데이터 모델링 중급 (Kimball)

## 4-1. 실제로 star schema 한 번 그려보기

```
                ┌─────────────┐
                │  dim_date   │
                │  date_key   │
                │  day, week  │
                │  month, qtr │
                └──────┬──────┘
                       │
  ┌──────────────┐     │      ┌──────────────────┐
  │ dim_creator  │     │      │ dim_advertiser   │
  │ creator_id   │─┐   │   ┌──│ advertiser_id    │
  │ region       │ │   │   │  │ category         │
  │ platform     │ │   │   │  └──────────────────┘
  └──────────────┘ │   │   │
                   ▼   ▼   ▼
              ┌────────────────┐
              │ fct_campaign_  │
              │  performance   │
              │ date_key       │
              │ creator_id     │
              │ advertiser_id  │
              │ impressions    │  ← additive measure
              │ spend_usd      │  ← additive
              │ ctr            │  ← non-additive!
              └────────────────┘
```

**중요 구분**:
- **Additive measure**: 합산이 의미 있는 것 (impressions, spend)
- **Semi-additive**: 일부 차원에만 합산 가능 (balance: 날짜 차원엔 합산 불가)
- **Non-additive**: 합산하면 안 되는 것 (CTR, ROAS — 비율!). 항상 **분자/분모**를 따로 저장하고 사용 시점에 계산.

## 4-2. Surrogate Key vs Natural Key

- **Natural key**: 원본이 주는 ID (`creator_id='@foo_bar'`)
- **Surrogate key**: 데이터 웨어하우스가 자체 부여 (`creator_sk=10234`, INT)

Kimball은 **Surrogate key 권장**. 이유:
1. Natural key가 바뀌어도 웨어하우스 안은 영향 없음
2. SCD Type 2에서 "같은 크리에이터, 다른 시점"을 다른 row로 구분
3. 성능 (INT 조인 빠름)

## 4-3. SCD Type 2 실전 예

```sql
-- dim_creator_scd
creator_sk  creator_id  follower_count  category   valid_from    valid_to      is_current
1           @foo        10000          beauty      2025-01-01    2025-06-30    false
2           @foo        15000          beauty      2025-07-01    2025-09-14    false
3           @foo        15000          lifestyle   2025-09-15    9999-12-31    true
```
→ 한 크리에이터가 3개 row로 존재. fact 테이블은 `creator_sk`로 조인 → 그 당시의 카테고리가 반영됨.

> "지금 시점의 카테고리"가 필요하면 `WHERE is_current = true`

## 4-4. Bus Matrix (Kimball의 히든 무기)

"어떤 비즈 프로세스(fact)가 어떤 차원을 공유하는가"를 한 장 표로 정리.

|                        | dim_date | dim_creator | dim_advertiser | dim_region | dim_currency |
|------------------------|:--------:|:-----------:|:--------------:|:----------:|:------------:|
| fct_post_daily         |    ✓     |      ✓      |                |     ✓      |              |
| fct_campaign_performance |  ✓     |      ✓      |       ✓        |     ✓      |       ✓      |
| fct_payment            |    ✓     |             |       ✓        |     ✓      |       ✓      |

→ 공유 차원(date, region, currency)이 바로 **conformed dimension**. 모델링 초기에 이 표부터 그리면 방향이 잡힙니다.

## 4-5. 🎯 AdInsight Agent 연결
- Phase 3 dbt 모델 설계 시 bus matrix 먼저 `docs/bus_matrix.md` 로 기록
- `dim_date`, `dim_region`, `dim_currency`가 conformed dim
- `dim_creator_scd`는 Type 2 snapshot으로 구현
- CTR/ROAS는 **항상 분자·분모 함께 저장**하고, ai_native 레이어에서 필요 시점에 계산

---

# 5. dbt 중급 — 실제 코드 해부

## 5-1. 프로젝트 구조

```
dbt/
├── dbt_project.yml          # 프로젝트 설정
├── profiles.yml              # 연결 정보 (gitignore)
├── models/
│   ├── staging/
│   │   ├── _sources.yml      # 원본 선언
│   │   ├── _models.yml       # 모델 문서·테스트
│   │   └── stg_creators.sql
│   ├── intermediate/
│   ├── marts/
│   └── ai_native/
├── macros/
├── seeds/                    # CSV → 테이블
├── snapshots/                # SCD2
└── tests/                    # 커스텀 테스트
```

## 5-2. dbt_project.yml 핵심 설정

```yaml
name: adinsight
version: '1.0.0'
profile: adinsight

model-paths: ["models"]
seed-paths: ["seeds"]
snapshot-paths: ["snapshots"]
macro-paths: ["macros"]
test-paths: ["tests"]

models:
  adinsight:
    staging:
      +materialized: view
      +schema: staging
    intermediate:
      +materialized: ephemeral
    marts:
      +materialized: table
      +schema: marts
    ai_native:
      +materialized: table
      +schema: ai_native
      +post-hook: "GRANT SELECT ON {{ this }} TO agent_readonly"
```

핵심:
- `+materialized`: 레이어별 기본 실체화 방식
- `+schema`: 생성될 Postgres 스키마
- `+post-hook`: 모델 생성 후 실행할 SQL (권한 부여 등)

## 5-3. Source 선언

```yaml
# models/staging/_sources.yml
sources:
  - name: raw
    schema: raw
    tables:
      - name: creators
        description: "플랫폼별 크리에이터 원본 데이터"
        freshness:
          warn_after: {count: 24, period: hour}
          error_after: {count: 48, period: hour}
        loaded_at_field: ingested_at
        columns:
          - name: creator_id
            tests: [not_null]
```

## 5-4. Staging 모델 예시

```sql
-- models/staging/stg_creators.sql
{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('raw', 'creators') }}
),
cleaned AS (
  SELECT
    creator_id::BIGINT AS creator_id,
    LOWER(TRIM(handle)) AS handle,
    md5(lower(email)) AS email_hash,  -- PII 마스킹
    platform::TEXT AS platform,
    follower_count::BIGINT AS follower_count,
    region_code::TEXT AS region,
    category::TEXT AS category,
    created_at::TIMESTAMPTZ AS created_at,
    updated_at::TIMESTAMPTZ AS updated_at
  FROM source
  WHERE deleted_at IS NULL
)
SELECT * FROM cleaned
```

## 5-5. Incremental 모델 (진짜 실무 패턴)

```sql
-- models/intermediate/int_post_daily.sql
{{ config(
    materialized='incremental',
    unique_key=['creator_id','date'],
    on_schema_change='append_new_columns',
    incremental_strategy='merge'
) }}

WITH source AS (
  SELECT * FROM {{ ref('stg_posts') }}
  {% if is_incremental() %}
    -- 증분 시점: 마지막 처리 이후 + 3일 재처리 윈도우
    WHERE updated_at > (SELECT MAX(updated_at) - INTERVAL '3 days' FROM {{ this }})
  {% endif %}
),
agg AS (
  SELECT
    creator_id,
    date_trunc('day', published_at)::DATE AS date,
    SUM(views) AS views,
    SUM(likes) AS likes,
    SUM(comments) AS comments,
    MAX(updated_at) AS updated_at
  FROM source
  GROUP BY 1, 2
)
SELECT * FROM agg
```

**핵심 포인트 3가지**:
1. **`is_incremental()`**: 증분 실행일 때만 WHERE 절 추가. 첫 full refresh 때는 조건 무시.
2. **3일 재처리 윈도우**: late-arriving data 대응.
3. **`merge` 전략**: `unique_key` 기준으로 upsert. 중복 방지.

## 5-6. Snapshot (SCD Type 2)

```sql
-- snapshots/creator_snapshot.sql
{% snapshot creator_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='creator_id',
    strategy='check',
    check_cols=['follower_count', 'category', 'region'],
    invalidate_hard_deletes=True
  )
}}

SELECT
  creator_id,
  follower_count,
  category,
  region,
  updated_at
FROM {{ ref('stg_creators') }}

{% endsnapshot %}
```

dbt가 자동으로 `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id` 컬럼 추가. `check` 전략은 지정 컬럼이 바뀔 때만 새 row 생성.

## 5-7. Tests

```yaml
# models/marts/_models.yml
models:
  - name: fct_post_daily
    description: "일/크리에이터/플랫폼 단위 포스트 성과. 1 row = 1 creator × 1 day × 1 platform."
    columns:
      - name: creator_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_creator_scd')
              field: creator_id
      - name: date
        tests: [not_null]
      - name: views
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
```

**커스텀 테스트** (`tests/assert_no_future_dates.sql`):
```sql
-- tests는 "문제가 있는 row"를 SELECT하면 실패
SELECT * FROM {{ ref('fct_post_daily') }}
WHERE date > CURRENT_DATE
```

## 5-8. Macros

```sql
-- macros/fx_convert.sql
{% macro fx_convert(amount_col, currency_col, target, date_col) %}
  {{ amount_col }} * (
    SELECT rate
    FROM {{ ref('dim_fx_rate') }}
    WHERE from_ccy = {{ currency_col }}
      AND to_ccy = '{{ target }}'
      AND rate_date = {{ date_col }}
  )
{% endmacro %}
```

사용:
```sql
SELECT
  campaign_id,
  {{ fx_convert('spend', 'currency', 'USD', 'date') }} AS spend_usd
FROM ...
```

## 5-9. 유용한 명령어

```bash
dbt deps           # 패키지 설치
dbt seed           # seeds CSV → 테이블
dbt snapshot       # snapshot 돌리기
dbt run            # 모든 모델 실행
dbt run --select staging  # 특정 레이어만
dbt run --select stg_creators+  # stg_creators와 그 하위 전부
dbt test           # 모든 테스트
dbt docs generate && dbt docs serve  # 문서 사이트
```

## 5-10. 🎯 AdInsight Agent 연결
- Phase 3 전체가 이 코드 패턴들의 실전 적용
- `ai_native.wide_campaign_360`은 marts를 여러 번 ref해서 만든 비정규화 모델
- `dbt run`은 Airflow DAG에서 `BashOperator`로 호출

---

# 6. Airflow 중급 — 실제 DAG 해부

## 6-1. TaskFlow API (최신 스타일)

```python
# dags/ingest_synthetic.py
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd

default_args = {
    "owner": "yeon",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

@dag(
    dag_id="ingest_synthetic",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingest", "synthetic"],
    doc_md=__doc__,
    max_active_runs=1,  # 동시 실행 방지
)
def ingest_synthetic():

    @task
    def generate(ds: str) -> str:
        """합성 데이터를 생성해 parquet로 저장"""
        path = f"/tmp/synthetic_{ds}.parquet"
        # ... 생성 로직
        return path

    @task
    def load_to_postgres(path: str, ds: str):
        """raw 스키마에 COPY 적재 (idempotent)"""
        pg = PostgresHook(postgres_conn_id="adinsight_pg")
        with pg.get_conn() as conn, conn.cursor() as cur:
            # 같은 날짜 기존 데이터 삭제 → 재적재
            cur.execute("DELETE FROM raw.posts_daily WHERE date = %s", (ds,))
            df = pd.read_parquet(path)
            # to_sql 또는 COPY
            df.to_sql("posts_daily", pg.get_sqlalchemy_engine(),
                      schema="raw", if_exists="append", index=False)
            conn.commit()

    @task
    def validate(ds: str):
        """최소 건수 체크"""
        pg = PostgresHook(postgres_conn_id="adinsight_pg")
        count = pg.get_first("SELECT COUNT(*) FROM raw.posts_daily WHERE date = %s", (ds,))[0]
        if count < 1000:
            raise ValueError(f"Expected >= 1000 rows, got {count}")

    path = generate("{{ ds }}")
    loaded = load_to_postgres(path, "{{ ds }}")
    validate("{{ ds }}") << loaded  # validate는 load 이후

ingest_synthetic()
```

**포인트**:
- `@dag`, `@task` 데코레이터 = TaskFlow API. Python 함수가 곧 태스크.
- `{{ ds }}` = Jinja 매크로. 실행 중 "YYYY-MM-DD" 로 치환.
- `DELETE ... WHERE date = ds; INSERT ...` = **idempotency 구현**. 같은 날짜 재실행해도 중복 없음.
- `retries=3 + retry_exponential_backoff` = 안정성.
- `max_active_runs=1` = 같은 DAG이 동시에 여러 번 안 돌게.

## 6-2. dbt를 호출하는 DAG

```python
# dags/dbt_run.py
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from datetime import datetime

@dag(
    dag_id="dbt_run",
    schedule="0 3 * * *",  # 매일 03:00
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["transform", "dbt"],
)
def dbt_run():
    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command="cd /opt/dbt && dbt deps",
    )
    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command="cd /opt/dbt && dbt seed",
    )
    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /opt/dbt && dbt snapshot",
    )
    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/dbt && dbt run",
    )
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/dbt && dbt test",
    )

    dbt_deps >> dbt_seed >> dbt_snapshot >> dbt_run_task >> dbt_test

dbt_run()
```

## 6-3. execution_date 정확히 이해

```python
@task
def load(data_interval_start, data_interval_end):
    """
    @daily DAG이 2026-04-16 00:00 UTC에 실행될 때:
    - data_interval_start = 2026-04-15 00:00 UTC
    - data_interval_end   = 2026-04-16 00:00 UTC
    - ds = "2026-04-15"  (= data_interval_start 날짜)
    처리 대상은 "어제 하루 전체".
    """
```

> **멘탈 모델**: DAG은 "과거의 한 조각(interval)을 완성 짓는" 작업. 오늘 실행은 어제 데이터를 처리.

## 6-4. Backfill

```bash
# 2026-01-01 ~ 2026-01-31 구간을 재실행
airflow dags backfill ingest_synthetic \
  --start-date 2026-01-01 \
  --end-date   2026-01-31
```

Idempotency가 보장되어 있으면 몇 번을 돌려도 안전. 아니면 재앙.

## 6-5. SLA와 Callback

```python
from airflow.utils.email import send_email

def notify_failure(context):
    ti = context["ti"]
    msg = f"❌ {ti.dag_id}.{ti.task_id} 실패: {context.get('exception')}"
    # Slack webhook, 또는 print
    print(msg)

default_args = {
    ...
    "on_failure_callback": notify_failure,
    "sla": timedelta(hours=2),
    "on_sla_miss_callback": notify_failure,
}
```

## 6-6. 동시성 제어 파라미터

| 파라미터 | 뜻 | 기본 |
|---|---|---|
| `max_active_runs` | 같은 DAG의 동시 run 수 | 16 |
| `max_active_tasks` | 같은 DAG 내 동시 task 수 | 16 |
| `pool` | 리소스 풀 (DB 연결 수 제한 등) | default_pool |
| `concurrency` | (deprecated) | — |

ETL 중복을 피하려면 `max_active_runs=1` 부터.

## 6-7. 흔한 함정

1. **DAG 파일 top-level에서 DB 쿼리 금지.** Airflow가 매 파싱마다 실행해 DB가 죽음.
2. **task 간 데이터 전달은 XCom**, 크기 제한이 있음. 큰 데이터는 파일/S3로 주고 경로만 XCom.
3. **`datetime.now()` 금지.** 항상 `data_interval_start` 같은 매크로 사용 (backfill 안전성).
4. **Jinja 매크로는 문자열 필드에서만**: `bash_command`, SQL 등. Python 코드 안은 직접 못 씀.

## 6-8. 🎯 AdInsight Agent 연결
- Phase 2의 `ingest_synthetic`, Phase 3의 `dbt_run`, Phase 7의 `weekly_llm_report` 세 DAG이 핵심
- 모든 DAG은 `max_active_runs=1`, 3회 retry, idempotent delete-then-insert 패턴

---

# 7. Superset 중급

## 7-1. Superset 사용 흐름

```
1. Database 연결 (Postgres)
      ↓
2. Dataset 만들기 (Physical: 테이블 / Virtual: SQL)
      ↓
3. Chart 만들기 (Dataset → 시각화 선택)
      ↓
4. Dashboard에 차트 배치
      ↓
5. Filter 추가, Export YAML
```

## 7-2. Virtual Dataset이 실무의 주력

Physical (raw 테이블 그대로) 대신 **Virtual** (SQL로 정의)이 일반적:

```sql
-- Virtual Dataset: "Advertiser ROI Summary"
SELECT
  advertiser_id,
  advertiser_name,
  advertiser_category,
  region,
  SUM(spent_usd) AS total_spend,
  SUM(revenue_usd) AS total_revenue,
  SUM(revenue_usd) / NULLIF(SUM(spent_usd), 0) AS roas,
  SUM(impressions) AS total_impressions,
  SUM(clicks) AS total_clicks,
  SUM(clicks)::FLOAT / NULLIF(SUM(impressions), 0) AS ctr
FROM ai_native.wide_campaign_360
WHERE start_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY 1,2,3,4
```

이 SQL이 Dataset이 되고, 차트는 이 Dataset에서 "Metric, Dimension, Filter" 를 골라 만든다.

## 7-3. Jinja + Filter (고급)

Superset도 Jinja를 지원. 대시보드 필터값을 SQL에 주입:
```sql
SELECT ...
FROM ...
WHERE region IN {{ filter_values('region') | where_in }}
  AND date BETWEEN '{{ from_dttm }}' AND '{{ to_dttm }}'
```

## 7-4. Cache 구성

```python
# superset_config.py
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": "redis://redis:6379/1",
}
DATA_CACHE_CONFIG = CACHE_CONFIG
```

## 7-5. Export / Import

```bash
# 대시보드 전체를 YAML zip으로
superset export-dashboards -f /tmp/dashboard.zip

# 가져오기
superset import-dashboards -p /tmp/dashboard.zip
```

Git에 커밋해 버전 관리 (AdInsight Agent `dashboards/superset_exports/`).

## 7-6. 🎯 AdInsight Agent 연결
- Phase 5에서 대시보드 3개 만든 뒤 export 커밋
- Virtual Dataset 기반 (`ai_native.*`)
- Redis 캐시로 대시보드 재로드 2번째는 빠르게 — **트래픽 실험에서 캐시 효과 측정 가능**

---

# 8. LangChain + Text2SQL + pgvector 중급

## 8-1. 전체 구조 다시

```python
# agent/chains/pipeline.py (개념 코드)
def answer_question(question: str) -> dict:
    # 1) 스키마 검색
    schema_docs = retriever.retrieve(question, top_k=8)

    # 2) SQL 생성
    sql = sql_generator.generate(question, schema_docs, prompt_version="v3")

    # 3) 검증
    validated = validator.check(sql)
    if not validated.ok:
        return {"error": validated.reason}

    # 4) 실행
    rows = executor.run(validated.sql, timeout_s=30, max_rows=1000)

    # 5) 결과 포매팅
    return formatter.format(rows, question)
```

## 8-2. pgvector 셋업

```sql
-- Phase 1 init SQL
CREATE EXTENSION IF NOT EXISTS vector;

-- 스키마용 벡터 테이블
CREATE SCHEMA IF NOT EXISTS vector_store;

CREATE TABLE vector_store.schema_chunks (
  id BIGSERIAL PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,     -- 'model:ai_native.wide_campaign_360:col:roas'
  doc_type TEXT,                     -- 'model', 'column', 'example_question'
  model_name TEXT,
  content TEXT NOT NULL,
  embedding VECTOR(1024),            -- bge-m3: 1024차원
  metadata JSONB,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW 인덱스 (ivfflat보다 최신, 재빌드 불필요)
CREATE INDEX ON vector_store.schema_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

## 8-3. 임베딩 적재 스크립트

```python
# agent/embeddings/build_schema_index.py
import yaml, json
from sentence_transformers import SentenceTransformer
import psycopg2

model = SentenceTransformer("BAAI/bge-m3")  # 다국어 강함

def load_dbt_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def iter_chunks(yaml_doc, model_name):
    # 모델 자체
    m = yaml_doc["models"][0]
    yield {
        "chunk_id": f"model:{model_name}",
        "doc_type": "model",
        "model_name": model_name,
        "content": f"Model: {model_name}\nDescription: {m.get('description','')}\n"
                   f"Grain: {m.get('meta',{}).get('grain','')}\n"
                   f"Synonyms: {m.get('meta',{}).get('synonyms',[])}",
        "metadata": m.get("meta", {}),
    }
    # 컬럼들
    for col in m.get("columns", []):
        yield {
            "chunk_id": f"model:{model_name}:col:{col['name']}",
            "doc_type": "column",
            "model_name": model_name,
            "content": f"{model_name}.{col['name']}: {col.get('description','')}",
            "metadata": col.get("meta", {}),
        }
    # 예시 질문
    for i, q in enumerate(m.get("meta", {}).get("example_questions", [])):
        yield {
            "chunk_id": f"model:{model_name}:example:{i}",
            "doc_type": "example_question",
            "model_name": model_name,
            "content": q,
            "metadata": {},
        }

def upsert(conn, chunks):
    vectors = model.encode([c["content"] for c in chunks], normalize_embeddings=True)
    with conn.cursor() as cur:
        for c, vec in zip(chunks, vectors):
            cur.execute("""
                INSERT INTO vector_store.schema_chunks
                  (chunk_id, doc_type, model_name, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE
                SET content=EXCLUDED.content,
                    embedding=EXCLUDED.embedding,
                    metadata=EXCLUDED.metadata,
                    updated_at=NOW()
            """, (c["chunk_id"], c["doc_type"], c["model_name"],
                  c["content"], vec.tolist(), json.dumps(c["metadata"])))
    conn.commit()
```

## 8-4. Retriever

```python
# agent/chains/schema_retriever.py
class SchemaRetriever:
    def __init__(self, conn, embedder):
        self.conn = conn
        self.embedder = embedder

    def retrieve(self, question: str, top_k: int = 8) -> list[dict]:
        vec = self.embedder.encode([question], normalize_embeddings=True)[0].tolist()
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT chunk_id, doc_type, model_name, content, metadata,
                       1 - (embedding <=> %s::vector) AS sim
                FROM vector_store.schema_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
            """, (vec, vec, top_k))
            return [dict(zip(
                ["chunk_id","doc_type","model_name","content","metadata","sim"], r
            )) for r in cur.fetchall()]
```

> `<=>` = cosine distance 연산자. `1 - cosine_distance` = similarity.

## 8-5. SQL Generator 프롬프트 (v3)

```yaml
# agent/prompts/v3_cot_with_schema.yaml
system: |
  당신은 AdInsight Agent 데이터 웨어하우스의 Text2SQL 어시스턴트입니다.
  PostgreSQL 문법만 사용하세요. SELECT 문만 생성하세요.
  답을 알 수 없으면 "UNKNOWN"을 출력하세요.

  다음 원칙을 따르세요:
  1. ai_native.* 스키마를 우선 사용
  2. 모든 금액은 *_usd 컬럼 사용
  3. 시간창: _1d, _7d, _30d 접미어 확인
  4. LIMIT 1000을 반드시 포함
  5. 단계적으로 생각(CoT)한 뒤 최종 SQL을 ```sql 블록에 출력

user: |
  ## 관련 스키마
  {% for chunk in schema_chunks %}
  - {{ chunk.content }}
  {% endfor %}

  ## 예시 질문-SQL 쌍 (few-shot)
  {% for ex in few_shots %}
  Q: {{ ex.q }}
  SQL:
  ```sql
  {{ ex.sql }}
  ```
  {% endfor %}

  ## 사용자 질문
  {{ question }}

  우선 단계별로 생각한 뒤, 마지막에 ```sql ... ``` 코드블록으로 답하세요.
```

## 8-6. Validator (핵심 안전장치)

```python
# agent/chains/validator.py
import sqlglot
from sqlglot import exp
from dataclasses import dataclass

FORBIDDEN = {"delete", "update", "insert", "drop", "alter", "truncate",
             "create", "grant", "revoke"}

@dataclass
class ValidationResult:
    ok: bool
    sql: str | None
    reason: str | None

def validate_and_rewrite(sql: str, max_rows: int = 1000) -> ValidationResult:
    try:
        tree = sqlglot.parse_one(sql, dialect="postgres")
    except Exception as e:
        return ValidationResult(False, None, f"parse_error: {e}")

    # 1) SELECT만
    if not isinstance(tree, exp.Select):
        return ValidationResult(False, None, "not_a_select")

    # 2) 금지어
    for node in tree.walk():
        if isinstance(node, exp.Command):
            if node.name.lower() in FORBIDDEN:
                return ValidationResult(False, None, f"forbidden: {node.name}")

    # 3) LIMIT 자동 주입
    if not tree.args.get("limit"):
        tree = tree.limit(max_rows)

    return ValidationResult(True, tree.sql(dialect="postgres"), None)
```

## 8-7. Executor

```python
# agent/chains/executor.py
import psycopg2
from psycopg2 import sql as pg_sql

def execute_readonly(sql: str, timeout_s: int = 30) -> list[dict]:
    conn = psycopg2.connect(
        dbname="adinsight",
        user="agent_readonly",   # ⭐ 읽기 전용 role
        password="...",
        host="postgres"
    )
    conn.set_session(readonly=True)
    with conn.cursor() as cur:
        cur.execute(f"SET LOCAL statement_timeout = '{timeout_s}s'")
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
```

**`agent_readonly` 롤 생성**:
```sql
CREATE ROLE agent_readonly LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE adinsight TO agent_readonly;
GRANT USAGE ON SCHEMA ai_native, marts TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA ai_native TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA ai_native GRANT SELECT ON TABLES TO agent_readonly;
```

이렇게 해두면 **혹시 DELETE가 프롬프트 인젝션으로 뚫려도** DB 레벨에서 차단.

## 8-8. 평가셋 구조

```jsonl
{"id":"q001","lang":"ko","difficulty":"easy","question":"지난주 TW에서 가장 ROAS 높은 캠페인 Top 5","gold_sql":"SELECT ...","gold_result_hash":"abc123","tags":["campaign","roas","region:TW"]}
{"id":"q002","lang":"en","difficulty":"medium","question":"Compare CTR of beauty vs gaming advertisers in the last 30 days","gold_sql":"...","gold_result_hash":"def456","tags":["ctr","category","30d"]}
```

## 8-9. 평가 실행

```python
# agent/eval/run_eval.py
def run_eval(prompt_version: str, llm_model: str) -> dict:
    results = []
    for item in load_dataset("agent/eval/dataset.jsonl"):
        start = time.time()
        try:
            out = answer_question(item["question"])
            rows = out["rows"]
            latency_ms = (time.time() - start) * 1000
            correct = hash_rows(rows) == item["gold_result_hash"]
        except Exception as e:
            correct, latency_ms, rows = False, None, None

        results.append({
            "id": item["id"], "correct": correct,
            "latency_ms": latency_ms,
            "tokens": out.get("usage", {}),
        })

    # 집계
    n = len(results)
    return {
        "prompt_version": prompt_version,
        "model": llm_model,
        "n": n,
        "exec_accuracy": sum(r["correct"] for r in results) / n,
        "p50": percentile([r["latency_ms"] for r in results if r["latency_ms"]], 50),
        "p95": percentile([r["latency_ms"] for r in results if r["latency_ms"]], 95),
    }
```

## 8-10. 🎯 AdInsight Agent 연결
- Phase 6 전체가 이 섹션의 코드로 이루어짐
- `agent_readonly` DB 롤은 Phase 1의 init SQL에 미리 넣어두기
- 프롬프트 v1→v2→v3 버전별 결과 차이가 **면접 무기 #1**

---

# 9. 동시성/트래픽 중급 — AdInsight Agent에서 실제 실험

## 9-1. Postgres 동시성 기본

### 트랜잭션 격리 수준
- Read Committed (기본): 다른 트랜잭션이 커밋한 건 바로 보임
- Repeatable Read: 트랜잭션 내내 같은 스냅샷
- Serializable: 완전히 직렬화된 것처럼 (가장 엄격, 느림)

AdInsight Agent의 Agent 쿼리는 Read Committed 로 충분.

### 락 종류
- **Row-level lock**: `SELECT ... FOR UPDATE`
- **Table-level lock**: `LOCK TABLE` (거의 안 씀)
- **Advisory lock**: 앱 레벨 상호배제. "같은 작업 2번 돌리지 마"
  ```sql
  SELECT pg_advisory_lock(hashtext('dbt_run'));
  -- 작업 ...
  SELECT pg_advisory_unlock(hashtext('dbt_run'));
  ```

### statement_timeout
```sql
SET LOCAL statement_timeout = '30s';  -- 이 세션에서 30초 넘는 쿼리는 자동 abort
```

## 9-2. Connection Pool

매번 새로 TCP 연결을 만드는 건 비쌈. **미리 만들어둔 풀을 재사용.**

```python
# psycopg2 pool 예
from psycopg2 import pool
pg_pool = pool.SimpleConnectionPool(
    minconn=2, maxconn=20,
    dbname="adinsight", user="agent_readonly", host="postgres"
)

# 쓸 때:
conn = pg_pool.getconn()
try:
    ...
finally:
    pg_pool.putconn(conn)
```

실무에선 **pgbouncer** 같은 프록시를 앞에 둠 (AdInsight Agent는 시뮬만).

## 9-3. Singleflight (캐시 stampede 방지)

같은 질문을 10명이 **동시에** 하면? 순진하게 짜면 LLM을 10번 부름. 하나만 실제 실행하고 나머지는 그 결과를 공유해야 함.

```python
# 개념 구현 (asyncio)
import asyncio

class Singleflight:
    def __init__(self):
        self._inflight: dict[str, asyncio.Future] = {}

    async def do(self, key: str, fn):
        if key in self._inflight:
            return await self._inflight[key]  # 이미 실행 중인 걸 기다림
        fut = asyncio.get_event_loop().create_future()
        self._inflight[key] = fut
        try:
            result = await fn()
            fut.set_result(result)
            return result
        finally:
            self._inflight.pop(key, None)
```

사용:
```python
sf = Singleflight()
result = await sf.do(
    key=hashlib.md5(question.encode()).hexdigest(),
    fn=lambda: answer_question(question)
)
```

## 9-4. Rate Limit

LLM API는 "분당 N건" 같은 제한이 있어요. 초과하면 429 응답. 대응 2가지:

1. **Token bucket** 로컬 제한 — 우리 쪽에서 미리 조절
2. **Exponential backoff retry** — 429 받으면 2, 4, 8초 대기 후 재시도

```python
import time, random
def call_with_backoff(fn, max_retries=5):
    for i in range(max_retries):
        try:
            return fn()
        except RateLimitError:
            wait = (2 ** i) + random.random()
            time.sleep(wait)
    raise
```

## 9-5. 트래픽 실험 레시피

AdInsight Agent에서 실제 돌려보고 수치 기록:

### 실험 A: Text2SQL Agent
```bash
# FastAPI로 Agent 노출 후
pip install locust
# locustfile.py 작성 후
locust -f locustfile.py --host http://localhost:8001 \
  --users 30 --spawn-rate 5 --run-time 2m --headless
```
기록: p50, p95, p99, RPS, 실패율.

### 실험 B: Superset 대시보드
```bash
# Apache Bench
ab -n 200 -c 10 "http://localhost:8088/superset/dashboard/1/"
```
기록: Time per request, transfer rate.

### 실험 C: Airflow 동시 DAG
- `max_active_runs`를 1 → 3으로 올리고 backfill
- Postgres `pg_stat_activity` 모니터링
- Worker 포화 시점 관찰

## 9-6. 🎯 AdInsight Agent 연결
- `docs/traffic_experiments.md`에 A/B/C 실험 결과 표 기록
- 면접 답변 템플릿 (입문편 섹션 9-3 참조)은 이 실험 수치가 있어야 "실제로"가 됨

---

# 10. 한 번 더 정리 — AdInsight Agent 전체 작업 흐름

```
[Phase 1] 환경 셋업
    docker-compose 이해(§1) + 초기 SQL

[Phase 2] 데이터 생성·수집
    Python + Faker + SDV → Parquet → Airflow DAG 적재(§6)

[Phase 3] dbt 모델링
    Kimball star schema(§4) + dbt 코드(§5)

[Phase 4] AI-Native Mart
    비정규화 + dbt meta + glossary (§5, §8)

[Phase 5] Superset + 쿼리 최적화
    Superset Dataset/Chart/Dashboard(§7)
    EXPLAIN + 인덱스 + 파티셔닝(§3)

[Phase 6] Text2SQL Agent
    LangChain + pgvector + validator + eval(§8)

[Phase 7] LLM 자동 리포트
    Airflow DAG + LLM 호출 + Pydantic 검증(§6, §8)

[Phase 8] 품질·CI
    dbt tests + Airflow callback + GitHub Actions

[Phase 9] 문서·면접 준비
    섹션 9 내용을 docs/ 아래에 실제 실험 결과로 남기기
```

---

# 다음 단계

- 이 문서를 다 읽었다면, 막히는 부분만 **완전판**에서 깊이 파세요.
- 그 다음 Phase 1 부트스트랩 프롬프트를 Claude Code에 넣고 시작.
- 모르는 단어가 나오면 **입문편 섹션 10 용어 사전**으로 돌아오세요.

"이해 50% + 실행 50%"의 반복이 가장 빠른 학습 경로입니다.
