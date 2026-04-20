---
title: "AdInsight Agent 용어 심화 사전"
subtitle: "ARM64 · OLTP/OLAP · Cron · Index · Ephemeral · Lineage"
author: "for Yeon"
---

# 이 문서에 대해

기본 용어 사전(`01_beginner.md` 섹션 10)에서 짧게 다룬 항목들 중 면접 단골이거나 프로젝트에서 깊이 이해해야 할 6개를 자세히 풀어쓴 문서입니다.

각 용어는 다음 5단계로 설명합니다.

1. **한 문장 정의**
2. **왜 이게 존재하는가** (없으면 어떻게 되는가)
3. **자세히 — 어떻게 동작하는가**
4. **비교/대안** (이것 말고 어떤 선택지가 있는가)
5. **AdInsight Agent 연결** (이 프로젝트의 어디서 만나는가)

---

# 1. ARM64 (Apple Silicon, aarch64)

## 1-1. 한 문장 정의
**컴퓨터 CPU의 명령어 집합 구조(ISA) 중 하나로, 64비트 ARM 아키텍처. Apple M1/M2/M3/M4 칩이 모두 이 계열.**

## 1-2. 왜 이게 중요한가

옛날 Mac은 Intel x86_64 CPU를 썼어요. 2020년 Apple Silicon 전환 후 Mac은 ARM64로 바뀌었습니다. 문제는 **세상의 대부분의 Docker 이미지가 x86_64로 빌드되어 있다**는 것.

ARM64 Mac에서 x86_64 이미지를 돌리면 Docker가 **Rosetta 2** 또는 **QEMU 에뮬레이션**으로 변환해 실행해요. 이 변환이 느립니다 — 보통 **2~5배 느려지고**, 메모리도 더 먹고, 가끔 미묘한 버그(특히 jemalloc 같은 메모리 할당자 관련)가 납니다.

## 1-3. 자세히

### CPU 아키텍처 종류
| 이름 | 별칭 | 사용처 |
|---|---|---|
| **x86_64** | amd64, x64 | 대부분의 PC, Intel/AMD CPU, 클라우드 VM 기본 |
| **ARM64** | aarch64, arm64v8 | Apple Silicon, AWS Graviton, Raspberry Pi 4+ |
| arm32 | armv7 | 구형 Raspberry Pi, 임베디드 |

### Docker가 멀티 아키텍처를 다루는 법

Docker 이미지는 **manifest list**라는 매니페스트로 여러 아키텍처를 한 태그로 묶어요.
```
postgres:16
├── linux/amd64    ← x86_64 환경
├── linux/arm64    ← Apple Silicon, Graviton
└── linux/arm/v7   ← Raspberry Pi
```

`docker pull postgres:16` 하면 호스트 아키텍처에 맞는 걸 자동으로 받습니다. 그런데 **어떤 이미지는 amd64만 있어요**. 그러면 ARM64 Mac은 에뮬레이션으로 돌리거나, "no matching manifest" 에러를 봅니다.

### 직접 확인하는 법
```bash
# 내 맥의 아키텍처
uname -m
# arm64 → Apple Silicon
# x86_64 → Intel Mac

# 이미지가 어떤 아키텍처를 지원하는지
docker buildx imagetools inspect postgres:16

# 컨테이너가 실제로 어떤 아키텍처로 도는지
docker inspect <container_id> | grep Architecture

# 강제로 아키텍처 지정
docker run --platform linux/amd64 ...
```

### compose 파일에서
```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    platform: linux/arm64    # 명시
```

## 1-4. AdInsight Agent에서 자주 부딪히는 함정

| 컴포넌트 | ARM64 지원 상황 | 권장 |
|---|---|---|
| `postgres:16` | 공식 ARM64 ✅ | 그대로 사용 |
| `pgvector/pgvector:pg16` | 공식 ARM64 ✅ | 그대로 사용 |
| `apache/airflow:2.9.x` | 공식 ARM64 ✅ | 그대로 사용 |
| `apache/superset:4.0.x` | ARM64 있지만 일부 의존성 빌드 필요 | 처음 부팅 느림 (5~10분), 그 다음은 정상 |
| `redis:7-alpine` | 공식 ARM64 ✅ | 그대로 |

> **체감 차이**: Apple Silicon(M2 기준) 네이티브 ARM64 이미지는 경험상 동급 Intel Mac 보다 빠르거나 비슷. 반면 amd64 에뮬레이션은 체감으로 답답할 정도.

## 1-5. 면접 답변 프레임

> "Apple Silicon 환경에서 AdInsight Agent를 개발했기 때문에, 모든 Docker 이미지를 ARM64 네이티브 지원 여부로 먼저 검증했습니다. Postgres는 공식 ARM64 이미지가 있고, pgvector 도 `pgvector/pgvector:pg16` 으로 ARM64 빌드를 제공해서 그대로 사용했습니다. Superset은 ARM64를 지원하지만 일부 Python 의존성을 컨테이너 내에서 컴파일하는 단계가 있어서 첫 부팅이 느린 점만 README 에 기록해두었습니다. 만약 클라우드 배포로 넘어간다면 AWS Graviton (ARM64) 인스턴스를 쓸 때 그대로 이미지 재사용이 가능하다는 장점도 있습니다."

---

# 2. OLTP vs OLAP

## 2-1. 한 문장 정의
- **OLTP** (Online Transaction Processing): **운영 시스템**의 짧고 많은 트랜잭션 처리.
- **OLAP** (Online Analytical Processing): **분석 시스템**의 큰 집계 쿼리 처리.

## 2-2. 왜 둘로 나뉘었나

처음엔 한 데이터베이스에서 다 했어요. 문제: 분석 쿼리(예: "지난 1년 매출 합계")가 거대한 스캔을 일으켜 **운영 시스템이 멈추는** 사고가 반복됨. 결제 처리하다 멈추는 거죠.

해결: **목적이 다른 두 시스템으로 분리**. 운영 DB는 가볍게 트랜잭션만, 별도 분석 DB는 무거운 집계만.

## 2-3. 자세히 — 무엇이 어떻게 다른가

### 워크로드 비교
|  | OLTP | OLAP |
|---|---|---|
| **요청 단위** | 1건당 짧음 (ms) | 1건당 김 (s~m) |
| **건수** | 초당 수천~수만 | 분당 수십~수백 |
| **읽는 행 수** | 1~수십 행 | 수만~수억 행 |
| **쓰기 비율** | 50% 가까이 | 거의 0% (배치 쓰기만) |
| **트랜잭션 격리** | 엄격 (Read Committed+) | 느슨해도 됨 |
| **인덱스 전략** | 많은 PK/FK 인덱스 | 적은 인덱스, 컬럼 스토어 |
| **사용자 수** | 많음 (수천~수만 동시) | 적음 (분석가, 대시보드) |
| **예시 쿼리** | `INSERT INTO orders ...` `SELECT * FROM users WHERE id=?` | `SELECT region, SUM(spend) FROM ... GROUP BY ...` |

### 저장 방식 차이
- **OLTP = 행 지향(row-oriented)**: 한 row의 모든 컬럼이 디스크에 나란히. 1건 조회/수정에 유리.
- **OLAP = 열 지향(column-oriented)**: 한 컬럼의 모든 값이 나란히. **집계와 압축에 유리**.

```
행 지향                      열 지향
[id1,name1,age1]             [id1,id2,id3,...]
[id2,name2,age2]             [name1,name2,name3,...]
[id3,name3,age3]             [age1,age2,age3,...]
↑ "id=2 행 전체" 빠름         ↑ "age 컬럼 평균" 빠름
```

### 대표 시스템
| 카테고리 | OLTP | OLAP |
|---|---|---|
| 전통 RDBMS | PostgreSQL, MySQL, Oracle | (가능하지만 느림) |
| 분석 전용 | — | BigQuery, Snowflake, Redshift, ClickHouse |
| 하이브리드 (HTAP) | TiDB, SingleStore, Postgres+columnar 확장 | 양쪽 다 |

## 2-4. ETL/ELT의 본질도 OLTP→OLAP

데이터 엔지니어링의 큰 그림은 결국:
```
[OLTP source DB]  ──ingest──▶  [OLAP warehouse]  ──BI/Agent──▶  [insight]
  결제·주문·이벤트                  분석용 컬럼 스토어
```
- ETL의 **E**(추출)는 OLTP에서, **L**(적재)은 OLAP으로.
- 그래서 **CDC**, **Source Freshness** 같은 개념이 등장 (운영 DB의 변경을 분석 DB에 빠르게 전파).

## 2-5. AdInsight Agent에서

AdInsight Agent는 로컬 편의성 때문에 **단일 PostgreSQL로 OLTP/OLAP 둘 다 시뮬레이션**합니다. 실제 LINE Pay 같은 환경에서는:

| AdInsight Agent 단순화 | 실무 분리 |
|---|---|
| Postgres `raw` 스키마 | OLTP DB (예: Postgres, MySQL) → CDC로 추출 |
| Postgres `marts`, `ai_native` | OLAP 웨어하우스 (BigQuery, Snowflake, Hive) |
| Postgres에서 직접 dbt 실행 | OLAP 웨어하우스 위에서 dbt-bigquery, dbt-snowflake |

## 2-6. 면접 답변 프레임

> "AdInsight Agent는 로컬 환경의 단순함을 위해 Postgres 하나로 OLTP 같은 raw 적재와 OLAP 같은 분석 마트를 모두 시뮬레이션했습니다. 실제 프로덕션이라면 운영 DB는 Postgres/MySQL 같은 행 지향 OLTP를 두고, 분석은 BigQuery 나 Snowflake 같은 열 지향 OLAP에서 dbt 로 처리하는 구조가 될 겁니다. 분리가 필요한 본질적인 이유는 워크로드가 정반대이기 때문입니다 — OLTP는 짧고 많은 트랜잭션, OLAP는 길고 적은 집계 쿼리라서, 같은 시스템에 두면 분석 쿼리가 운영 트랜잭션을 막아 사고가 납니다."

---

# 3. Cron

## 3-1. 한 문장 정의
**유닉스 계열 OS에서 "이 명령을 이 시간에 정기적으로 실행해라" 라고 등록하는 스케줄러. 1970년대부터 있는 표준.**

## 3-2. 왜 알아야 하나

Airflow, GitHub Actions, Kubernetes CronJob, AWS EventBridge — **거의 모든 스케줄러가 cron 문법을 차용**합니다. 한 번 익혀두면 평생 씀.

## 3-3. 자세히 — Cron 문법 완전 정복

### 기본 5필드 (Airflow도 동일)
```
 ┌───────────── 분 (0 - 59)
 │ ┌─────────── 시 (0 - 23)
 │ │ ┌───────── 일 (1 - 31)
 │ │ │ ┌─────── 월 (1 - 12)
 │ │ │ │ ┌───── 요일 (0 - 6, 0=일요일)
 │ │ │ │ │
 * * * * *  command
```

### 특수 기호

| 기호 | 의미 | 예 |
|---|---|---|
| `*` | 모든 값 | `* * * * *` = 매분 |
| `,` | 여러 값 나열 | `0,15,30,45 * * * *` = 매시 0/15/30/45분 |
| `-` | 범위 | `0 9-18 * * *` = 매일 9시~18시 정각 |
| `/` | 간격 | `*/5 * * * *` = 5분마다 |
| `?` | "지정 안 함" (일/요일에서) | (Airflow는 미지원, Quartz용) |

### 자주 쓰는 패턴

| 표현 | 의미 |
|---|---|
| `0 * * * *` | 매시 정각 |
| `*/5 * * * *` | 5분마다 |
| `0 3 * * *` | 매일 새벽 3시 |
| `0 3 * * 1` | 매주 월요일 새벽 3시 |
| `0 9 * * 1-5` | 평일(월~금) 오전 9시 |
| `0 0 1 * *` | 매월 1일 자정 |
| `30 2 * * 0` | 매주 일요일 02:30 |
| `0 0 1 1 *` | 매년 1월 1일 자정 |
| `15,45 * * * *` | 매시 15분, 45분 |

### Airflow의 프리셋 (편의 별칭)

| 프리셋 | 의미 |
|---|---|
| `@once` | 한 번만 |
| `@hourly` | `0 * * * *` |
| `@daily` (=`@midnight`) | `0 0 * * *` |
| `@weekly` | `0 0 * * 0` (일요일 자정) |
| `@monthly` | `0 0 1 * *` |
| `@yearly` (=`@annually`) | `0 0 1 1 *` |

### Python `timedelta` 도 가능 (Airflow)
```python
schedule=timedelta(minutes=15)   # 15분마다
schedule=timedelta(days=2)       # 2일마다
```
> 단, `timedelta` 는 "마지막 실행으로부터 X 후" 라서 cron 처럼 "정시"가 아님. 기준 시간이 흘러갈 수 있어요.

## 3-4. 흔한 함정

### ① **타임존 함정 (가장 흔함)**
크론 표현은 "어느 시간대 기준?"인지 명시가 필요. Airflow는 기본 **UTC**입니다. `0 3 * * *` = UTC 03:00 = **KST 12:00** (낮 정오). 한국 시간 새벽 3시에 돌리려면:
```python
@dag(
    schedule="0 3 * * *",
    timezone="Asia/Seoul",   # Airflow 2.5+ DAG 인자로 가능
    ...
)
# 또는 cron을 UTC 18:00 (= KST 03:00) 로 바꿔서 schedule="0 18 * * *"
```

### ② **요일 0과 7 둘 다 일요일**
대부분 구현에서 0=일, 7=일 (월~토는 1~6). Airflow도 동일.

### ③ **31일 매월?**
`0 0 31 * *` = "매월 31일 자정". 30일까지인 달엔 안 돔. 매월 마지막 날을 원한다면 cron만으로는 어려움 → 매일 돌리되 코드 안에서 "오늘이 월말인가?" 체크.

### ④ **catchup 결합**
Airflow에서 `start_date`가 과거이고 `catchup=True`면, cron이 가리키는 모든 과거 시각에 대해 한꺼번에 backfill 시도 → 폭주. 실수로 **수백 개 DAG run** 생성됨. 처음엔 `catchup=False` 권장.

### ⑤ **DST(서머타임) 경계**
미국·유럽은 일년에 두 번 시계가 1시간 이동. UTC 기반이면 안전, 로컬 시간 기반이면 일년에 한 번 02:30 같은 cron이 두 번 돌거나 한 번도 안 돕니다. **분석 파이프라인은 UTC 기반 권장.**

## 3-5. AdInsight Agent에서 사용

```python
# dags/dbt_run.py
@dag(schedule="0 18 * * *", ...)   # UTC 18:00 = KST 03:00
def dbt_run(): ...

# dags/weekly_llm_report.py
@dag(schedule="0 19 * * 0", ...)   # UTC 일 19:00 = KST 월 04:00
def weekly_llm_report(): ...

# dags/agent_eval_nightly.py
@dag(schedule="@daily", ...)       # 가독성 위해 프리셋 사용
def agent_eval_nightly(): ...
```

## 3-6. 디버깅 팁

```bash
# crontab 표현이 다음에 언제 돌지 확인 (Python)
python3 -c "from croniter import croniter; from datetime import datetime; \
  c = croniter('0 18 * * *', datetime.utcnow()); \
  print([c.get_next() for _ in range(5)])"

# 또는 웹: crontab.guru — 표현을 자연어로 풀이
# 예: 0 18 * * * → "At 18:00."
```

> **꿀팁**: 면접 자리에서 cron 표현이 헷갈리면 "crontab.guru에서 검증하는 습관이 있다"고 솔직히 말하는 게 모르는 척 짐작하는 것보다 낫습니다.

---

# 4. Index — B-tree, BRIN, GIN, Hash

## 4-1. 한 문장 정의
**테이블에서 특정 조건의 row를 빠르게 찾기 위한 보조 자료구조. 책의 색인(index)과 같은 역할.**

## 4-2. 왜 인덱스 종류가 여러 개인가

데이터 패턴이 모두 다르기 때문. "정렬된 시계열에 적합한 구조"와 "JSON 내부 검색에 적합한 구조"는 완전히 달라요. Postgres는 워크로드별로 5종 이상의 인덱스를 제공합니다.

## 4-3. 종류별 자세히

### ① B-tree (Balanced Tree) — 기본값, 90% 케이스

**구조**: 균형 이진 트리(엄밀히는 B-tree 는 다중 분기). 트리 높이가 항상 비슷해 모든 검색이 O(log N).

**잘하는 것**
- 같음 비교 (`=`)
- 범위 비교 (`<`, `>`, `BETWEEN`)
- 정렬 (`ORDER BY`)
- prefix LIKE (`LIKE 'abc%'`)

**못하는 것**
- 부분 LIKE (`LIKE '%abc%'`)
- jsonb 내부 검색
- 배열 안 검색

**언제 쓰나**: 대부분. 의심스러우면 B-tree.

```sql
CREATE INDEX ON dim_creator (creator_id);            -- 같음
CREATE INDEX ON fct_post_daily (region, date);       -- 복합 (순서 중요!)
CREATE INDEX ON dim_creator (LOWER(handle));         -- 함수 인덱스
```

**복합 인덱스 순서 규칙**: WHERE에서 자주 쓰는 컬럼을 **앞에**. `(region, date)` 인덱스는:
- ✅ `WHERE region='TW'` (앞부터 사용)
- ✅ `WHERE region='TW' AND date>...` (앞+뒤)
- ❌ `WHERE date>...` (뒤만, 인덱스 미사용 또는 부분 사용)

### ② BRIN (Block Range INdex) — 시계열의 비밀병기

**구조**: 테이블을 "블록 범위(기본 128 페이지)" 로 묶고, 각 범위의 **min/max만** 저장. 인덱스 자체가 매우 작음.

**잘하는 것**
- 데이터가 **물리적으로 정렬**되어 있을 때 (시계열, 자동증가 ID)
- 큰 테이블에 대한 범위 스캔
- 인덱스 크기를 극도로 작게 유지하고 싶을 때

**못하는 것**
- 데이터가 정렬 안 되어 있을 때 (효과 0)
- 같음 비교 (덜 효율적)

**얼마나 작나**: 1억 행 테이블에 B-tree 인덱스가 수 GB라면, BRIN은 **수 MB**. 100~1000배 차이.

```sql
-- AdInsight Agent 의 fct_post_daily (날짜 정렬)
CREATE INDEX ON fct_post_daily USING BRIN (date)
  WITH (pages_per_range = 64);

-- pages_per_range: 작을수록 정확하고 큼, 클수록 작고 덜 정확
-- 64 (기본 128보다 작음) = 더 정확, 약간 큰 인덱스
```

**언제 쓰나**: 시계열 fact 테이블의 date 컬럼. 거의 공식.

### ③ GIN (Generalized Inverted iNdex) — 다중 값 검색

**구조**: 역인덱스(검색 엔진의 그것). "이 값을 포함하는 row 들" 을 빠르게 찾음.

**잘하는 것**
- 배열 안 검색 (`tags @> ARRAY['beauty']`)
- jsonb 내부 검색 (`metadata->'platform' = 'tiktok'`)
- 전문(full-text) 검색 (`tsvector @@ tsquery`)
- 부분 LIKE (with `pg_trgm` 확장)

**못하는 것**
- 범위 비교 (B-tree가 더 빠름)
- 정렬 (인덱스가 정렬을 보장하지 않음)

```sql
-- jsonb 내부 검색
CREATE INDEX ON dim_campaign USING GIN (platform_mix);
SELECT * FROM dim_campaign WHERE platform_mix @> '{"tiktok": true}';

-- 배열 검색
CREATE INDEX ON dim_creator USING GIN (tags);
SELECT * FROM dim_creator WHERE tags && ARRAY['beauty', 'fashion'];

-- 부분 LIKE (pg_trgm)
CREATE EXTENSION pg_trgm;
CREATE INDEX ON dim_creator USING GIN (handle gin_trgm_ops);
SELECT * FROM dim_creator WHERE handle ILIKE '%foo%';
```

### ④ Hash — 거의 안 쓰는 특수목적

**구조**: 해시 테이블. O(1) 같음 비교.

**잘하는 것**: 정확히 같음(`=`) 만.
**못하는 것**: 범위, 정렬, 다른 모든 것.

**왜 거의 안 쓰나**: B-tree도 같음 비교는 충분히 빠르고(O(log N) 이지만 N=10억이어도 30단계), 게다가 B-tree는 범위·정렬도 다 됨. 인덱스 한 개로 더 많은 쿼리를 커버.

**예외**: 인덱스 크기를 극단적으로 줄여야 하는 hash partitioning 키 같은 케이스.

### ⑤ HNSW / IVFFlat — 벡터 인덱스 (pgvector)

**구조**
- **HNSW** (Hierarchical Navigable Small World): 다층 그래프. 빠른 ANN.
- **IVFFlat**: 클러스터 기반. 빌드는 빠르지만 데이터 추가 시 재빌드 필요.

**잘하는 것**: 벡터 유사도 (cosine, L2, inner product) 의 근사 최근접 검색.

```sql
-- AdInsight Agent: 스키마 임베딩 검색용
CREATE INDEX ON vector_store.schema_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- 쿼리 시점 정확도/속도 조절
SET hnsw.ef_search = 40;
SELECT * FROM vector_store.schema_chunks
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

## 4-4. 인덱스 비교 한눈에

| 종류 | 같음 | 범위 | 정렬 | LIKE 'a%' | LIKE '%a%' | jsonb | 배열 | 벡터 | 인덱스 크기 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| B-tree | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | 보통 |
| BRIN | △ | ✅ (정렬시) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **매우 작음** |
| GIN | △ | ❌ | ❌ | ❌ | ✅ (trgm) | ✅ | ✅ | ❌ | 큼 |
| Hash | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 작음 |
| HNSW | — | — | — | — | — | — | — | ✅ | 큼 |

## 4-5. 인덱스 안티패턴 (절대 피할 것)

### ① 모든 컬럼에 인덱스
인덱스마다 INSERT/UPDATE 시 비용이 추가됨. 컬럼 10개에 인덱스 10개 = INSERT가 10배 느림.
**원칙**: 실제로 WHERE/JOIN/ORDER BY 에 쓰이는 컬럼에만.

### ② 저선택도(low cardinality) 컬럼에 일반 인덱스
예: `is_active BOOLEAN` (값이 두 개뿐). 플래너가 무시함. 대신 **부분 인덱스**:
```sql
CREATE INDEX ON users (created_at) WHERE is_active = true;
```

### ③ NULL 가득한 컬럼에 인덱스
B-tree는 기본적으로 NULL 도 인덱스함. NULL 비율이 99% 같으면 부분 인덱스로:
```sql
CREATE INDEX ON orders (delivered_at) WHERE delivered_at IS NOT NULL;
```

### ④ 함수로 감싼 컬럼 검색
```sql
WHERE LOWER(email) = 'foo@bar.com'   -- email 컬럼 인덱스 안 씀!
```
해결: **함수 인덱스**
```sql
CREATE INDEX ON users (LOWER(email));
```

### ⑤ 사용 안 되는 인덱스 방치
```sql
-- 사용된 적 없는 인덱스 찾기
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```
사용 안 되는 인덱스는 **삭제하는 게 이득**.

## 4-6. AdInsight Agent 인덱스 전략

```sql
-- 1. fct_post_daily (20M+ rows, 시계열)
CREATE INDEX ON fct_post_daily USING BRIN (date) WITH (pages_per_range = 64);
CREATE INDEX ON fct_post_daily (region, date);
CREATE INDEX ON fct_post_daily (creator_id);

-- 2. dim_creator
CREATE INDEX ON dim_creator (creator_id);
CREATE INDEX ON dim_creator USING GIN (handle gin_trgm_ops);  -- 부분 검색

-- 3. dim_campaign (jsonb 필드)
CREATE INDEX ON dim_campaign USING GIN (platform_mix);

-- 4. vector_store.schema_chunks (Agent retrieval)
CREATE INDEX ON vector_store.schema_chunks
  USING hnsw (embedding vector_cosine_ops);
```

## 4-7. 면접 답변 프레임

> "AdInsight Agent에서는 워크로드 패턴에 맞춰 4종의 인덱스를 조합했습니다. fct_post_daily 가 2천만 행 시계열이라서 date 컬럼에 BRIN을 — 이게 B-tree 대비 인덱스 크기를 1000배쯤 줄여주면서 정렬된 데이터엔 충분합니다. region+date 같은 자주 함께 쓰는 필터는 복합 B-tree로. 광고 캠페인의 platform_mix 가 jsonb 라서 GIN. 마지막으로 Agent 의 스키마 검색용 1024차원 벡터에는 pgvector 의 HNSW 인덱스를 cosine 거리로 걸었습니다. 그리고 무엇보다 pg_stat_user_indexes 로 사용 안 되는 인덱스를 정기적으로 정리하는 습관 — 인덱스는 공짜가 아니라 INSERT 비용으로 환산되니까요."

---

# 5. Ephemeral (dbt materialization)

## 5-1. 한 문장 정의
**dbt 모델의 실체화 방식 중 하나로, 테이블도 뷰도 만들지 않고 "다른 모델 안에 CTE로 inline 되는" 가상 모델.**

## 5-2. 왜 이게 존재하나

dbt 모델을 만들다 보면 **"다른 모델에서만 쓰이고, 자체적으로는 굳이 테이블/뷰가 필요 없는" 중간 계산**이 생겨요. 매번 테이블/뷰를 만들면:
- 웨어하우스에 객체가 늘어남 (관리 부담)
- 디스크/스토리지 비용
- 단순 재사용일 뿐인데 거창함

ephemeral 은 "이건 그냥 SQL 조각"으로 취급. 컴파일 시점에 **부모 모델의 CTE로 펼쳐짐**.

## 5-3. 자세히 — 4가지 materialization 비교

| 종류 | 실체 | 디스크 | 빠름 | 적합한 곳 |
|---|---|---|---|---|
| **view** | CREATE VIEW | 거의 0 | 매번 SELECT | 단순 변환, 자주 안 쓰는 |
| **table** | CREATE TABLE | 큼 | 인덱스/캐시 효과 | 자주 조회, marts |
| **incremental** | CREATE TABLE + MERGE | 큼 | 신규만 추가 | 대용량 fact |
| **ephemeral** | CTE만 (객체 없음) | 0 | 부모에 inline | 재사용용 SQL 조각 |

### ephemeral 동작 예

`models/intermediate/int_active_creators.sql` (ephemeral):
```sql
{{ config(materialized='ephemeral') }}

SELECT creator_id
FROM {{ ref('stg_creators') }}
WHERE last_active_at > CURRENT_DATE - INTERVAL '30 days'
```

이걸 다른 모델에서 ref:
```sql
-- models/marts/fct_active_post.sql
SELECT p.*
FROM {{ ref('stg_posts') }} p
JOIN {{ ref('int_active_creators') }} a USING (creator_id)
```

dbt가 컴파일하면 **이렇게 펼쳐집니다**:
```sql
WITH __dbt__cte__int_active_creators AS (
  SELECT creator_id
  FROM staging.stg_creators
  WHERE last_active_at > CURRENT_DATE - INTERVAL '30 days'
)
SELECT p.*
FROM staging.stg_posts p
JOIN __dbt__cte__int_active_creators a USING (creator_id)
```

→ Postgres에 객체 없이, 부모 SQL의 CTE로 동작.

## 5-4. ephemeral 의 장점

1. **객체 없음** — 웨어하우스 깔끔
2. **재사용 가능** — 동일 SQL 조각을 여러 모델에서 ref
3. **이름·문서·테스트 가능** — 일반 dbt 모델처럼 schema.yml 적용

## 5-5. ephemeral 의 함정

### ① 너무 많이 쓰면 부모 SQL 폭발
ephemeral A → B → C → D 체인이면 D 한 모델 SQL 안에 A,B,C가 전부 inline 됨. 디버깅 시 1000줄 짜리 SQL을 쳐다봐야 함.

**원칙**: ephemeral 체인은 1~2단계까지만.

### ② 직접 SELECT 불가
`SELECT * FROM int_active_creators` 가 안 됨 (객체 없음). 디버깅 시 일시로 view 로 바꿔서 확인 후 되돌리기.

### ③ 실행 계획 최적화 한계
거대한 inline SQL 은 플래너가 최적화하기 어려울 수 있음. 성능 문제 있으면 view/table 로 변경.

### ④ 테스트 실행 시 비효율
`dbt test` 가 ephemeral 모델 테스트할 때마다 부모 쿼리를 다시 실행. 큰 데이터셋이면 느림.

## 5-6. AdInsight Agent 에서 ephemeral 권장 케이스

`dbt_project.yml`:
```yaml
models:
  adinsight:
    intermediate:
      +materialized: ephemeral   # 중간 계산은 기본 ephemeral
    staging:
      +materialized: view
    marts:
      +materialized: table
    ai_native:
      +materialized: table
```

intermediate 폴더에:
- `int_active_creators.sql` — 활성 크리에이터 필터
- `int_post_with_currency.sql` — 통화 변환된 결과
- `int_campaign_normalized.sql` — 캠페인 정규화

이런 "한 번 정의해서 여러 marts에서 재사용" 패턴이 ephemeral 의 정석.

## 5-7. 면접 답변 프레임

> "AdInsight Agent 의 intermediate 레이어는 기본 ephemeral 로 설정했습니다. 이유는 두 가지입니다. 첫째, intermediate 모델들은 marts 의 빌딩 블록일 뿐 자체로 쿼리할 일이 없어서 웨어하우스에 객체로 남길 필요가 없습니다. 둘째, ephemeral 은 부모 모델의 CTE로 inline 되어 컴파일된 SQL 한 덩어리로 실행되기 때문에 별도 객체 생성 비용이 없고, 그러면서도 dbt schema.yml 로 description 과 테스트는 그대로 적용됩니다. 다만 ephemeral 체인은 2단계 이내로 제한했습니다 — 그 이상이면 컴파일된 SQL 이 거대해져 디버깅이 어려워지기 때문입니다. 성능 문제가 있는 모델은 ephemeral → view 또는 table 로 일시 전환해 EXPLAIN 으로 확인하는 워크플로우를 따랐습니다."

---

# 6. Lineage (리네이지)

## 6-1. 한 문장 정의
**데이터의 "출처와 흐름"을 추적하는 개념. "이 컬럼이 어디서 와서 어디로 가는지" 를 그래프로 보여주는 것.**

## 6-2. 왜 이게 중요한가

데이터 시스템이 복잡해지면 다음과 같은 질문이 일상이 됩니다:
- "이 대시보드 숫자가 어떤 raw 테이블에서 왔지?"
- "raw.creators 컬럼명을 바꾸면 어디까지 깨지지?"
- "이 모델을 삭제해도 안전한가? 누가 쓰지?"
- "이 숫자가 이상한데, 어느 단계에서 잘못된 거지?"

리네이지가 없으면 이 질문들에 답하려면 **수십 개 SQL 파일을 grep** 해야 해요. 리네이지가 있으면 클릭 몇 번.

## 6-3. 자세히 — 두 종류

### ① Table-level lineage (테이블 단위)
"테이블 A → 테이블 B → 테이블 C" 수준. 충분한 경우 많음. dbt 가 자동 제공.

```
raw.tiktok_posts
    ↓
stg_posts (view)
    ↓
int_post_daily (ephemeral)
    ↓
fct_post_daily (table)
    ↓
ai_native.wide_daily_platform_summary (table)
    ↓
[Superset Dashboard: Creator Performance]
```

### ② Column-level lineage (컬럼 단위)
"`fct_post_daily.views` 가 `raw.tiktok_posts.view_count` 와 `raw.instagram_posts.video_views` 를 SUM 한 것" 수준.

훨씬 강력하지만 구현 어려움. 도구:
- **dbt + dbt-utils** (제한적)
- **OpenLineage**
- **DataHub**, **Marquez**, **Atlan**, **Monte Carlo** (전문 도구)

## 6-4. dbt 가 리네이지를 자동으로 만드는 원리

dbt 모델은 SQL 안에 `{{ ref('other_model') }}` 또는 `{{ source('schema', 'table') }}` 매크로를 씁니다. dbt 컴파일러는 이걸 파싱해 **DAG (의존성 그래프)** 를 자동 구축.

```sql
-- models/marts/fct_post_daily.sql
SELECT ...
FROM {{ ref('int_post_daily') }} p
JOIN {{ ref('dim_creator_scd') }} c USING (creator_id)
```

→ dbt 가 "fct_post_daily 는 int_post_daily, dim_creator_scd 에 의존" 을 자동 인식.

`dbt docs generate && dbt docs serve` 하면:
- 전체 DAG 시각화
- 각 모델 클릭 → 상위/하위 의존성
- 컬럼별 description

## 6-5. Exposures — 리네이지를 BI/Agent 까지 확장

dbt 모델은 자기들끼리는 ref 로 연결되지만, **그 너머 (Superset 대시보드, Text2SQL Agent, 주간 리포트)** 는 dbt 가 모릅니다. Exposure 가 이걸 메꿉니다.

```yaml
# models/exposures.yml
exposures:
  - name: superset_advertiser_roi_dashboard
    type: dashboard
    url: http://localhost:8088/superset/dashboard/1/
    description: "광고주 ROI 대시보드 (Superset)"
    depends_on:
      - ref('wide_campaign_360')
      - ref('agg_advertiser_daily')
    owner:
      name: Yeon
      email: yeon@example.com

  - name: text2sql_agent
    type: application
    description: "AdInsight Agent Text2SQL BI Agent"
    depends_on:
      - ref('wide_campaign_360')
      - ref('wide_daily_platform_summary')
      - ref('glossary')
    owner:
      name: Yeon

  - name: weekly_llm_report
    type: notebook
    description: "주간 LLM 자동 리포트 (Airflow DAG)"
    depends_on:
      - ref('agg_advertiser_weekly')
    owner:
      name: Yeon
```

이걸로 dbt docs 의 lineage 그래프가 **모델 → 대시보드/Agent/리포트** 까지 확장됩니다.

## 6-6. 리네이지의 실전 가치

### ① Impact analysis (변경 영향 분석)
"`raw.tiktok_posts.view_count` 를 `views` 로 컬럼명 바꾸면 어디 깨지지?"
→ dbt docs에서 `raw.tiktok_posts` 노드를 클릭해 downstream 전부 확인.

```bash
dbt ls --select source:raw.tiktok_posts+    # 이 source 의 모든 후손
```

### ② 디버깅
"이 대시보드 숫자가 이상한데"
→ exposure 에서 시작해서 거꾸로 raw 까지. 어느 단계에서 변환이 잘못됐는지 추적.

### ③ 신뢰도 추적
"이 컬럼이 SCD2 snapshot 을 거쳤나? 어떤 테스트가 걸려 있나?"
→ 리네이지 + 메타데이터로 한눈에.

### ④ 데드 코드 식별
"6개월간 아무도 안 쓴 모델 = 삭제 후보"
→ exposure가 없고 다른 모델의 ref 도 없는 leaf node.

## 6-7. AdInsight Agent 의 리네이지 전략

| 레벨 | 도구 | 자동화 |
|---|---|---|
| Table-level | dbt docs | 자동 (ref/source 파싱) |
| Column-level | dbt-utils + 수동 description | 부분 자동 |
| BI/Agent 까지 확장 | dbt exposures | 수동 선언 |
| External catalog | (생략, OpenLineage 언급만) | — |

`docs/lineage_screenshot.png` 로 dbt docs 의 그래프 캡처해서 README에 박기. 이 한 장이 "데이터 시스템의 전체 그림" 을 강력하게 보여줌.

## 6-8. 면접 답변 프레임

> "AdInsight Agent 에서는 두 층위로 리네이지를 관리했습니다. 첫째, 테이블 단위는 dbt 가 ref/source 매크로를 파싱해 자동 생성하는 DAG 를 그대로 사용했고, dbt docs serve 로 시각화했습니다. 둘째, BI 와 Agent 까지의 다운스트림은 dbt exposures 로 명시적으로 선언했습니다 — Superset 대시보드 3개, Text2SQL Agent, 주간 LLM 리포트 DAG 를 모두 exposure 로 등록해 dbt docs 에서 모델→소비처까지 한 그래프로 보입니다. 컬럼 단위 리네이지는 description 에 'derived from X.Y' 를 적는 수동 방식이었는데, 운영 규모에서는 OpenLineage 나 DataHub 같은 외부 카탈로그 도입이 정답이라고 생각합니다. 리네이지의 실전 가치는 단순 시각화보다는 변경 영향 분석에 있다고 생각합니다 — raw 컬럼명 변경 같은 작은 일이 어느 대시보드를 깰지 사전에 알 수 있는 건 SQL grep 으로는 절대 따라갈 수 없는 보장입니다."

---

# 부록 — 용어 간 관계 한눈에

```
┌─ 인프라 ─────────────────────────────────────────────────┐
│  ARM64 ── Docker 이미지 호환 ── compose 모든 서비스         │
│                                                            │
│  Cron ── Airflow schedule ── DAG 실행 시각                 │
└────────────────────────────────────────────────────────────┘
              │
              ▼
┌─ 데이터 흐름 ────────────────────────────────────────────┐
│                                                            │
│  raw (OLTP-like)                                          │
│    │                                                       │
│    ▼  Index 적용 (B-tree, BRIN, GIN)                      │
│  staging                                                   │
│    │                                                       │
│    ▼  ephemeral 중간 계산                                  │
│  intermediate                                              │
│    │                                                       │
│    ▼  table materialization                                │
│  marts (OLAP-like)                                        │
│    │                                                       │
│    ▼  비정규화                                             │
│  ai_native                                                 │
│    │                                                       │
│    ▼  exposures                                            │
│  [Superset · Text2SQL Agent · LLM Report]                 │
│                                                            │
│   ↑                                                        │
│   └── 전 과정이 Lineage 로 추적 가능                        │
└────────────────────────────────────────────────────────────┘
```

이 6개 용어가 AdInsight Agent 의 **인프라부터 데이터 흐름의 끝까지** 를 대부분 설명합니다. 각 용어를 설명할 때 "다른 용어와 어떻게 연결되는지" 까지 함께 말하면 면접에서 시스템적 사고를 보여줄 수 있어요.
