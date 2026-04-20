---
title: "AdInsight Agent 사전학습 — 입문 요약본"
subtitle: "DE 초보자를 위한 빠른 훑어보기"
author: "for Yeon"
---

# 이 문서에 대해

이 문서는 AdInsight Agent 프로젝트를 시작하기 전, **"이게 뭐고 왜 쓰는지"** 만 빠르게 잡아두기 위한 요약본입니다. 깊이 대신 **감각**에 집중했어요. 각 주제당 5~10분이면 읽힙니다.

**읽는 순서 추천**
1. 섹션 1~2 (Docker, DE 큰 그림) — 반드시 먼저
2. 섹션 3~4 (SQL, 데이터 모델링) — 기초 체력
3. 섹션 5~6 (dbt, Airflow) — 프로젝트 양대 축
4. 섹션 7 (Superset) — 빠르게
5. 섹션 8~9 (LangChain Text2SQL, 동시성) — 프로젝트 차별화 포인트
6. 섹션 10 (용어 사전) — 필요할 때만 찾아보기

**이 문서를 다 읽고 나면 할 수 있어야 하는 것**
- "데이터 엔지니어링이 뭐하는 건지" 한 문단으로 설명
- "dbt와 Airflow가 뭐가 다른지" 한 문장으로 설명
- "star schema가 왜 필요한지" 감으로 이해
- Claude Code가 생성한 docker-compose.yml을 읽고 대강 이해
- 면접에서 "Text2SQL이 왜 어려운가요?" 에 기본적인 답 가능

그 이상은 **중급편**에서 다룹니다.

---

# 1. Docker와 docker-compose 입문

## 1-1. 한 문장 요약
**"내 맥북을 더럽히지 않고, 여러 프로그램(Postgres, Airflow, Superset…)을 한꺼번에 깔끔하게 띄웠다 내릴 수 있게 해주는 도구."**

## 1-2. 왜 쓰나?
옛날에는 Postgres를 쓰려면 Mac에 직접 설치했어요. 버전이 꼬이고, 다른 프로젝트랑 충돌나고, 삭제하기도 귀찮았죠. Docker는 **"각 프로그램을 격리된 박스(컨테이너)에 넣고, 필요할 때만 꺼내서 돌리는"** 방식으로 이 문제를 해결합니다.

**비유**: 집에 요리할 때마다 아예 새 부엌을 차렸다가, 요리 끝나면 부엌째로 치워버리는 것. 내 집(맥북)은 그대로.

## 1-3. 꼭 알아야 할 용어 5개

| 용어 | 뜻 | 비유 |
|---|---|---|
| **이미지 (image)** | 프로그램의 "설치본" 같은 것. 바뀌지 않음 | 붕어빵 틀 |
| **컨테이너 (container)** | 이미지를 실행한 상태. 실제 돌아가는 인스턴스 | 틀로 찍어낸 붕어빵 |
| **볼륨 (volume)** | 컨테이너가 꺼져도 사라지지 않는 데이터 저장소 | 냉장고 |
| **네트워크** | 컨테이너들끼리 이름으로 서로 부를 수 있게 해주는 통로 | 집 안 와이파이 |
| **포트 매핑 (port mapping)** | 컨테이너 안 포트를 내 맥북 포트와 연결 | 집 전화 ↔ 휴대폰 착신전환 |

## 1-4. docker-compose는 뭔가?
여러 컨테이너를 **YAML 파일 한 장으로** 정의하고 `docker compose up` 명령 한 번으로 전부 띄우는 도구. AdInsight Agent는 Postgres + Redis + Airflow(웹/스케줄러/워커) + Superset 을 한 compose 파일로 관리합니다.

**최소 예시**:
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"   # 호스트 5432 → 컨테이너 5432
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```
이걸 저장하고 `docker compose up -d` 하면 Postgres가 띄워지고, `psql -h localhost -U postgres` 로 접속 가능.

## 1-5. 초보가 자주 당하는 함정 3개

1. **"컨테이너 껐는데 데이터가 날아갔어요"** → 볼륨을 안 걸었기 때문. 중요한 데이터는 **반드시 volume 마운트**.
2. **"포트가 이미 사용 중"** → 맥에 이미 Postgres가 깔려 있거나, 다른 컨테이너가 점유 중. `lsof -i :5432` 로 확인.
3. **"Apple Silicon에서 이미지가 너무 느려요"** → arm64 지원 이미지가 아닌 경우. compose에 `platform: linux/arm64` 명시하거나 arm64 지원 이미지(예: `ankane/pgvector`) 사용.

## 1-6. 1분 요약
- Docker = 프로그램을 격리 상자(컨테이너)에서 실행
- docker-compose = 여러 컨테이너를 YAML로 한꺼번에 관리
- `up -d` / `down` / `logs -f` / `exec` 네 개 명령어만 우선 익히면 됨
- 맥(Apple Silicon)에서는 arm64 이미지 우선, 메모리 넉넉히

---

# 2. 데이터 엔지니어링 큰 그림

## 2-1. DE가 하는 일, 한 문장
**"여기저기 흩어진 raw 데이터를, 분석가와 AI 모델이 바로 쓸 수 있는 모양으로 모으고 정제하고 늘 최신 상태로 유지하는 일."**

## 2-2. 전형적인 데이터 파이프라인 계층

```
[Source]  ──▶  [Ingestion]  ──▶  [Raw]  ──▶  [Staging]  ──▶  [Marts]  ──▶  [BI/AI]
  실제 소스       수집            원본 보존    1차 정제      비즈 모델     대시보드/Agent
  (API,DB,파일)   (배치/스트림)    (immutable) (타입,마스킹) (star schema)
```

- **Raw**: 원본을 그대로 저장. "증거물" 같은 것. **절대 수정하지 않음.**
- **Staging**: 원본을 "1:1 정제"만 한 층. 타입 캐스팅, 컬럼명 snake_case, PII 해싱.
- **Marts**: 비즈니스 관점 모델. dim/fact 테이블. 분석가가 주로 사용.
- **AI-Native Mart** (AdInsight Agent 특화): LLM Agent가 쉽게 쓸 수 있게 **비정규화된** 전용 레이어.

## 2-3. ETL vs ELT
- **ETL**: Extract → Transform → Load. 옛날 방식. 변환을 외부 서버에서.
- **ELT**: Extract → Load → Transform. **요즘 주류.** 일단 웨어하우스(Postgres/BigQuery)에 부어넣고, 거기서 SQL로 변환. dbt가 바로 이 T를 담당.

> AdInsight Agent는 ELT 방식. Raw로 부어넣고 → dbt가 변환.

## 2-4. OLTP vs OLAP
- **OLTP**: 실시간 주문·결제 같은 "운영 DB". 짧은 트랜잭션, 많은 동시성. (예: 쇼핑몰 주문 DB)
- **OLAP**: 분석용 DB. 긴 집계 쿼리, 컬럼 지향, 대용량 스캔. (예: BigQuery, Snowflake)

> AdInsight Agent는 로컬 편의상 **Postgres 하나로 둘 다 시뮬레이션**합니다. 실제 LINE Pay 같은 환경에선 OLAP 따로 (Hadoop, Hive, BigQuery 등).

## 2-5. Data Lake vs Data Warehouse vs Lakehouse
- **Lake**: 파일 그대로 저장 (Parquet, JSON). 자유도↑, 거버넌스↓
- **Warehouse**: 테이블 구조로 저장. 거버넌스↑, 자유도↓
- **Lakehouse**: 둘의 장점을 합친 최신 패턴 (Delta Lake, Iceberg)

> AdInsight Agent에서는 Parquet(lake 느낌) → Postgres 테이블(warehouse) 흐름을 단순 재현.

## 2-6. 1분 요약
- DE는 "원본 → 레이어 거치며 점점 깔끔해지는 파이프라인"을 만드는 일
- Raw는 건드리지 마라, 변환은 staging부터
- 요즘은 ELT가 주류이고 dbt가 T 담당
- OLTP/OLAP 구분은 면접 단골 개념

---

# 3. SQL 재복습 (DE 관점)

## 3-1. 왜 또 SQL?
분석가 시절 SQL과 DE의 SQL은 **강조점이 다릅니다**. 분석가는 "답을 얻으면 OK", DE는 "이 쿼리가 내일 10배 데이터에서도 버틸까"를 고민해요.

## 3-2. 꼭 알아야 할 5가지 (초보)

### ① 조인은 타입과 NULL에 민감하다
```sql
-- 조인 키가 한쪽은 INT, 한쪽은 VARCHAR면 조용히 실패
-- NULL은 NULL과도 같지 않다 (=으로 비교 안 됨)
```
→ 스테이징에서 **타입 정리**가 중요한 이유.

### ② 윈도우 함수 (DE에서 제일 자주 등장)
"그룹 안에서 줄 번호 매기기", "7일 이동평균", "전날 대비 증감" — 전부 윈도우 함수.

```sql
SELECT
  creator_id,
  date,
  views,
  SUM(views) OVER (PARTITION BY creator_id ORDER BY date
                   ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS views_7d_sum,
  ROW_NUMBER() OVER (PARTITION BY category ORDER BY views DESC) AS rank_in_category
FROM fct_post_daily;
```

외워두면 좋은 함수:
- `ROW_NUMBER()` / `RANK()` / `DENSE_RANK()`
- `LAG()` / `LEAD()` — 전날/다음날 값
- `SUM/AVG OVER (...)` — 이동 집계
- `FIRST_VALUE()` / `LAST_VALUE()`

### ③ CTE (WITH 구문)
복잡한 쿼리를 "여러 단계"로 나눠 읽기 쉽게. dbt 모델은 거의 전부 CTE로 작성합니다.

```sql
WITH daily AS (
  SELECT creator_id, date, SUM(views) AS views
  FROM fct_post_daily
  GROUP BY 1,2
),
ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY views DESC) AS rnk
  FROM daily
)
SELECT * FROM ranked WHERE rnk <= 10;
```

### ④ EXPLAIN / EXPLAIN ANALYZE
쿼리가 "어떻게 실행될지" 보여주는 도구. 느린 쿼리 진단의 출발점.

```sql
EXPLAIN ANALYZE
SELECT * FROM fact_post_metrics_daily WHERE date = '2026-01-01';
```

봐야 할 핵심:
- **Seq Scan**: 전체 스캔 (보통 나쁨, 작은 테이블에선 괜찮음)
- **Index Scan**: 인덱스 사용 (좋음)
- **Rows**: 예상과 실제
- **Time**: planning time, execution time

### ⑤ 인덱스는 공짜가 아니다
인덱스는 **읽기를 빠르게 하는 대신 쓰기를 느리게 합니다**. 또 디스크도 먹어요. "넣을수록 좋다"가 아니라 "필요한 곳에만". 자주 쓰는 종류:

- **B-tree**: 기본. 범위·정렬·같음 비교.
- **BRIN**: 시계열처럼 **정렬되어 있는 큰 테이블**에 적합. 크기 작고 빠름.
- **GIN**: jsonb, 전문검색, 배열.
- **Hash**: 정확 일치만. 거의 안 씀.

## 3-3. 1분 요약
- 윈도우 함수 / CTE / EXPLAIN / 인덱스 — 이 4개가 DE SQL 기본기
- 쿼리가 느리면 "EXPLAIN ANALYZE"부터
- 인덱스는 "왜 이 컬럼에 이 타입으로 거는지" 설명할 수 있어야 함

---

# 4. 데이터 모델링 이론 (Kimball · star schema)

## 4-1. 왜 모델링?
원본 테이블을 그대로 두면 쿼리마다 **조인 지옥**에 빠지고, 분석가마다 다른 정의로 같은 지표를 계산해서 숫자가 맞지 않아요. 모델링은 **"조직 전체가 같은 정의를 쓰게 만들기"** 위한 설계입니다.

## 4-2. 두 학파

- **Kimball (차원 모델링, star schema)**: 분석 친화. 비즈니스 중심. **요즘 dbt 진영의 기본.**
- **Inmon (3NF 기반 EDW)**: 엔터프라이즈, 정규화 중심.

> 실무·면접은 Kimball 기반이 압도적. AdInsight Agent도 Kimball.

## 4-3. Star Schema 감 잡기

**Fact 테이블**: "일어난 사건". 숫자(measure)를 가짐.
- 예: `fct_post_daily` — 어떤 크리에이터가 어떤 날 몇 번 노출됐는지

**Dimension 테이블**: "그 사건의 맥락". 속성을 가짐.
- 예: `dim_creator` — 크리에이터의 이름, 지역, 카테고리
- 예: `dim_date` — 날짜, 요일, 주차, 월

**그림으로**:
```
        dim_date
           │
dim_creator ── fct_post_daily ── dim_advertiser
           │
        dim_region
```
Fact가 한가운데 있고, 주변에 Dim이 별처럼 붙어 있다고 해서 **star** schema.

## 4-4. Grain (입자)
Fact 테이블에서 가장 중요한 개념. **"1 row가 무엇을 의미하는지"** 를 한 문장으로 적을 수 있어야 합니다.

- "1 row = 1 creator × 1 post × 1 day" ← 좋음
- "1 row = 상황에 따라 다름" ← 재앙

Grain이 명확하지 않으면 집계할 때 중복·누락이 생깁니다.

## 4-5. SCD (Slowly Changing Dimension)
크리에이터의 팔로워 수, 카테고리는 **시간에 따라 변합니다**. 이걸 어떻게 기록할지가 SCD.

| 타입 | 설명 | 예 |
|---|---|---|
| Type 1 | 덮어쓰기. 역사 없음 | 가장 최근 값만 |
| Type 2 | 변경 시점마다 새 row. `valid_from`/`valid_to` | 역사 전체 보존 |
| Type 3 | 컬럼으로 "이전 값" 보관 | 제한적 |

AdInsight Agent는 **Type 2**를 dbt snapshot으로 구현.

## 4-6. Conformed Dimension (공유 차원)
여러 fact가 **같은 dim을 공유**하는 것. `dim_date`, `dim_region`, `dim_currency`는 여러 팩트가 공유. 이렇게 해야 지역별 비교, 통화별 합산이 가능.

## 4-7. 1분 요약
- Kimball = fact + dim = star schema
- Grain을 한 문장으로 설명할 수 있어야 함
- 변하는 속성은 SCD Type 2
- 공유 차원(date, region, currency)을 만들어라

---

# 5. dbt 입문

## 5-1. 한 문장 요약
**"SQL로 데이터를 변환하는 일을, 소프트웨어 개발처럼(버전 관리·테스트·문서화) 할 수 있게 해주는 도구."**

## 5-2. dbt 없이 어떻게 하던 시절이었나?
분석가들이 노션/스프레드시트에 SQL을 모아두고, 누군가 한 번씩 복사-붙여넣기해서 테이블을 만들고, 그 테이블을 누가 언제 만든 건지 아무도 모르고, 컬럼 설명은 구두로 전해지고… 한마디로 **"재현 불가능한 SQL 스파게티"**.

dbt는 이걸 "SELECT 하나 = 모델 하나 = 파일 하나"로 묶고, 의존성을 자동으로 풀고, 테스트/문서/리네이지를 공짜로 주는 프레임워크입니다.

## 5-3. 꼭 알아야 할 개념 5개

### ① Model = SELECT 파일
`models/staging/stg_creators.sql` 안에 `SELECT ... FROM {{ source('raw','creators') }}` 같은 SQL을 쓰면 dbt가 자동으로 테이블/뷰를 만들어 줍니다.

### ② ref()와 source()
- `{{ source('raw', 'creators') }}` — 외부에서 들어온 원본 테이블
- `{{ ref('stg_creators') }}` — 다른 dbt 모델

이 두 매크로 덕분에 **의존성 그래프(DAG)** 가 자동으로 그려집니다. "stg_creators 먼저, 그 다음 dim_creator" 순서를 사람이 정할 필요 없음.

### ③ Materialization
모델이 실제로 **어떤 형태로** 실행되는지:
- `view`: 매번 SELECT (기본). 빠른 개발.
- `table`: 실제 테이블로 저장. 반복 조회 빠름.
- `incremental`: 새로 들어온 것만 추가. 큰 테이블에 필수.
- `ephemeral`: 테이블 안 만들고 CTE로만 inline.

### ④ Tests
YAML로 선언만 하면 끝. 실행하면 자동으로 SQL로 변환돼서 돌아감.
```yaml
models:
  - name: dim_creator
    columns:
      - name: creator_id
        tests: [not_null, unique]
      - name: region_code
        tests:
          - accepted_values:
              values: [TW, TH, KR, JP]
```

### ⑤ dbt docs
`dbt docs generate && dbt docs serve` 하면 브라우저에서 **전체 모델 그래프, 컬럼 설명, 리네이지** 를 볼 수 있는 정적 사이트가 뜹니다. 면접용 스크린샷 재료로 훌륭.

## 5-4. dbt vs Airflow — 초보가 가장 헷갈리는 것

| 질문 | dbt | Airflow |
|---|---|---|
| 뭘 하나? | **데이터를 변환** (T) | **파이프라인을 스케줄링·오케스트레이션** |
| 언어는? | SQL 중심 | Python 중심 |
| 담당 범위 | 웨어하우스 안에서만 | 웨어하우스 밖 + 안 전부 |
| 비유 | "요리 레시피" | "주방 전체 운영" |

**한 문장**: *Airflow가 "dbt run을 매일 새벽 3시에 실행하라" 라고 지시하는 거고, dbt는 그 명령을 받아 SQL을 실행.*

## 5-5. 초보 함정
- dbt는 **데이터를 옮기지 않는다**. 이미 웨어하우스에 들어온 데이터를 "그 안에서" 변환할 뿐. 수집은 Airflow/Python 몫.
- 모든 SQL을 dbt 모델로 관리하라. 애드혹 SQL은 금방 쌓이고 아무도 관리 못함.
- `dbt run` 돌리기 전에 `dbt compile` 로 먼저 SQL을 확인하는 습관.

## 5-6. 1분 요약
- dbt = "SELECT 파일 → 테이블" 을 관리하는 프레임워크
- ref() / source() 덕분에 의존성 자동
- materialized는 4가지, 그중 incremental이 실무 핵심
- tests + docs는 공짜이니 무조건 챙길 것
- Airflow는 집사, dbt는 요리사

---

# 6. Airflow 입문

## 6-1. 한 문장 요약
**"언제, 어떤 순서로, 어떤 태스크들을 실행할지 Python으로 적어두면, Airflow가 그대로 돌려주고 실패했을 때 재시도·알림까지 해주는 스케줄러."**

## 6-2. 핵심 개념

### ① DAG (Directed Acyclic Graph)
"유향 비순환 그래프". 쉽게 말해 **태스크들의 실행 순서**를 그린 것. 같은 태스크를 절대 두 번 거치지 않음(acyclic).

```python
@dag(schedule="@daily", start_date=datetime(2026,1,1), catchup=False)
def ingest_tiktok():
    extract = PythonOperator(task_id="extract", python_callable=fetch_data)
    load    = PythonOperator(task_id="load",    python_callable=load_to_postgres)
    extract >> load   # "extract 끝나고 load 실행"
```

### ② Task / Operator
하나의 "할 일". 종류:
- `PythonOperator` — 파이썬 함수 실행
- `BashOperator` — 쉘 명령
- `PostgresOperator` — SQL 실행
- `BranchPythonOperator` — 조건 분기

### ③ Schedule
언제 돌지. cron 문자열(`"0 3 * * *"`) 또는 프리셋(`"@daily"`, `"@hourly"`) 또는 `timedelta`.

### ④ Execution Date (data_interval)
**초보가 가장 헷갈리는 개념.** Airflow에서 "2026-01-15 에 실행된 @daily DAG" 는 사실 **2026-01-14 데이터를 처리**하는 것. 왜냐면 그 날이 **끝나야** 그 날의 데이터가 전부 들어오니까.

> 데이터 기준일 = logical date ≠ 실제 실행 시각

### ⑤ Backfill
과거 특정 구간을 **다시 돌리는** 것. 데이터를 놓쳤거나 로직이 바뀌었을 때.

### ⑥ Idempotency (아이뎀포턴시, 멱등성)
**"같은 입력으로 몇 번을 돌려도 결과가 같다"** 는 성질. 파이프라인의 **가장 중요한 설계 원칙**. 재시도·백필이 망가지지 않으려면 필수.

> 나쁜 예: `INSERT INTO table VALUES (...)` — 돌릴 때마다 중복 쌓임
> 좋은 예: `INSERT ... ON CONFLICT DO UPDATE` (upsert) 또는 `DELETE WHERE date=... ; INSERT ...`

### ⑦ Executor
실제로 task를 어디서 돌릴지.
- `LocalExecutor` — 같은 머신, 병렬 O
- `CeleryExecutor` — 여러 워커 분산 (AdInsight Agent가 쓸 것)
- `KubernetesExecutor` — 각 task를 별도 Pod에서

## 6-3. 초보 함정 4개

1. **catchup 함정**: `start_date`를 과거로 잡고 `catchup=True`(기본값)면 그 사이의 모든 날짜를 한꺼번에 돌려버림. 처음엔 `catchup=False` 권장.
2. **execution_date 오해**: 위 ④번 그대로.
3. **DAG 파일이 안 보임**: 파일이 문법 오류거나 import 에러면 조용히 안 보임. `airflow dags list-import-errors` 로 확인.
4. **max_active_runs**: 동시 실행 가능한 run 수. 데이터 경쟁을 피하려면 1로.

## 6-4. 1분 요약
- DAG = task 순서 그래프
- 스케줄은 cron, execution_date는 "데이터 기준일"
- Idempotency가 파이프라인의 생명
- 초보는 `catchup=False`부터
- AdInsight Agent에서 dbt run을 매일 호출하는 게 Airflow의 핵심 역할

---

# 7. Superset BI 입문

## 7-1. 한 문장 요약
**"SQL로 차트 만들고, 차트들을 묶어 대시보드로 만들고, 팀에 공유할 수 있는 오픈소스 BI 도구. Tableau의 오픈소스 버전 느낌."**

## 7-2. 구조 이해
```
Database (Postgres)   →  Dataset  →  Chart  →  Dashboard
  (실제 테이블·뷰)       (논리적 테이블)  (시각화 1개)  (차트 묶음)
```
- **Dataset**은 "Superset 안에서 쓸 가상 테이블". 계산 컬럼·메트릭을 추가 가능.
- **Chart**는 Dataset에서 하나의 시각화.
- **Dashboard**는 차트를 배치한 페이지.

## 7-3. SQL Lab
Superset 안에서 **애드혹 SQL**을 바로 쓸 수 있는 창. 쿼리 짜고 → "Create Chart" 누르면 바로 Dataset/Chart 로 전환.

## 7-4. 꼭 알아야 할 3가지

### ① 캐시
같은 쿼리를 또 받으면 DB로 안 가고 캐시에서 응답. 캐시를 너무 안 쓰면 DB 부하, 너무 오래 쓰면 stale 데이터.

### ② 필터 (Native Filters)
대시보드 최상단 드롭다운(날짜, 지역 등). 이걸로 모든 차트를 한꺼번에 필터링.

### ③ Row-Level Security
"이 사용자는 TW 데이터만" 같은 규칙. 실무에선 중요.

## 7-5. 초보 함정
- Superset의 metadata DB(=자기 설정 저장용)와 실제 분석용 DB는 **다른 것**. 처음 셋업 때 이 둘을 헷갈리면 안 됨.
- Dashboard export/import는 YAML로. 버전 관리 가능(AdInsight Agent도 이걸로).
- arm64 Mac에서 초기 부팅 느림 주의.

## 7-6. 1분 요약
- Database → Dataset → Chart → Dashboard 계층
- SQL Lab은 애드혹 분석용
- Tableau와 개념은 유사, 오픈소스·확장성↑
- JD에 "Superset" 명시 + 오픈소스 기여 우대라 이 도구를 주로 쓸 것

---

# 8. LangChain + Text2SQL + pgvector 입문

## 8-1. Text2SQL이 뭐?
**"자연어 질문 → SQL 쿼리 → 결과 반환"** 의 전 과정. 사용자는 "지난주 대만에서 ROAS 가장 높은 뷰티 캠페인 Top 5?" 만 말하고, 시스템이 알아서 SQL을 짜 돌려 답을 준다.

## 8-2. LangChain이 뭐?
LLM을 앱에 쓰기 쉽게 해주는 프레임워크. **"LLM 호출 + 프롬프트 템플릿 + 외부 도구(DB, 검색, API) 연결"** 을 표준화된 컴포넌트로 제공.

> 꼭 LangChain일 필요는 없음. 하지만 SQL Agent 같은 패턴의 표준 구현체가 많아서 **포트폴리오·면접용**으로 좋음.

## 8-3. 왜 그냥 GPT한테 던지면 안 되나?

1. **스키마를 모르니** 엉뚱한 컬럼을 씀 (halucination)
2. **DELETE/DROP** 같은 위험한 SQL을 만들 수 있음
3. 테이블이 수백 개면 프롬프트가 너무 길어짐
4. **평가가 안 됨** — 맞았는지 틀렸는지 기록·개선이 어려움

Text2SQL 시스템의 본질은 이 4가지를 **엔지니어링으로 풀기**.

## 8-4. Schema-Aware Retrieval (핵심)
**"질문과 관련 있는 테이블·컬럼만 프롬프트에 넣기"** 위한 검색. 단계:

1. dbt yaml의 description·synonyms·example_questions 을 문서로 만들고
2. **임베딩 모델**로 벡터로 변환
3. **Vector DB**(pgvector)에 저장
4. 질문이 오면, 질문도 임베딩 → 벡터 유사도 검색 → top-k 반환
5. top-k만 프롬프트에 넣어 LLM에 전달

## 8-5. 임베딩과 Vector DB 기본

- **임베딩**: 텍스트 → 숫자 벡터(예: 1024차원). "의미가 비슷하면 벡터가 가깝다".
- **Vector DB**: 이 벡터들을 빠르게 "가까운 거 찾기"가 가능하게 저장하는 DB.
- **pgvector**: Postgres 확장으로 벡터 컬럼 + ANN 인덱스(ivfflat, hnsw)를 지원. 별도 벡터 DB를 안 쓰고 Postgres 한 스택으로 끝낼 수 있음.

## 8-6. Agent의 필수 구성
```
질문 → [Retriever] → [SQL Generator(LLM)] → [Validator] → [Executor] → 결과
              ↑                                    ↑
          pgvector                              sqlglot (AST parse)
```

**Validator**가 왜 중요?
- `SELECT` 만 허용 (DROP/DELETE 차단)
- `LIMIT` 자동 삽입
- `EXPLAIN` 먼저 돌려 "이 쿼리가 얼마나 걸릴지" 확인
- 구문 오류 사전 탐지

## 8-7. 평가 (Evaluation)
**"프롬프트를 바꿨는데 더 좋아진 거야?"** 에 답하기 위해 고정된 평가셋이 필요.

- **Execution Accuracy**: 실행 결과가 정답과 같은 비율
- **Exact Match**: SQL 문자열이 정답과 똑같은 비율 (참고용, 관대하게 봐야 함)
- **Latency p50/p95**: 응답 속도
- **Cost per query**: 토큰 비용

## 8-8. 1분 요약
- Text2SQL = 자연어 → SQL → 결과
- 그냥 LLM에 던지면 안 됨. Retriever + Validator + Executor 가 필수
- pgvector로 schema embedding 저장 → top-k retrieval
- 평가셋이 없으면 개선이 없다

---

# 9. 동시성/트래픽 면접 개념

## 9-1. 왜 이게 중요한가
LINE Pay 면접 후기에서 **"트래픽 처리"와 "동시성"** 을 중점적으로 물어봤다고 했어요. 초보자도 최소한의 용어와 사고틀은 잡고 가야 합니다.

## 9-2. 꼭 아는 단어 10개

| 용어 | 뜻 | 상황 |
|---|---|---|
| **Latency** | 한 요청의 응답 시간 | "빠르다/느리다" |
| **Throughput** | 단위시간당 처리량 | "초당 몇 건?" |
| **p50 / p95 / p99** | 50·95·99 퍼센타일 응답시간 | "대부분 빠르지만 꼬리 응답도 챙겨야" |
| **Concurrent** | 동시에 "진행 중"인 요청 수 | "지금 몇 명이 쓰고 있나" |
| **QPS** | Queries Per Second | Throughput의 동의어 |
| **Connection pool** | DB 연결을 재사용하는 풀 | "새 연결은 비싸니 미리 만들어둠" |
| **Back-pressure** | 넘치면 받지 않고 대기시키기 | "큐가 터지지 않게" |
| **Rate limit** | 초당 요청 제한 | "LLM API 1분 60건 제한" |
| **Timeout** | 일정 시간 넘으면 끊음 | "무한 대기 방지" |
| **Retry with backoff** | 실패하면 간격 늘려가며 재시도 | "exponential backoff" |

## 9-3. 동시성의 3가지 층위 (AdInsight Agent 기준)

1. **파이프라인**: Airflow 동시 DAG run, dbt incremental MERGE → idempotency로 푼다.
2. **DB**: 대시보드 SELECT와 ETL MERGE 충돌 → statement_timeout, 커넥션 풀, 락.
3. **서빙/Agent**: 여러 사용자가 같은 질문 → singleflight(한 번만 실행 후 결과 공유), 캐시, rate limit.

## 9-4. "트래픽 10배가 오면?" 답변 프레임
1. **지금 병목이 어딘가?** (DB? LLM API? 네트워크?)
2. **수평 확장 가능한가?** (stateless면 쉬움, stateful이면 어려움)
3. **캐시를 넣을 수 있나?** (읽기 많으면 대부분 해결)
4. **비동기화 가능한가?** (사용자를 기다리게 하지 말고 큐잉)
5. **Back-pressure를 거는가?** (무한히 받으면 터짐. 한계선을 둔다)

## 9-5. 1분 요약
- 용어 10개 + 층위 3개 + 답변 프레임 5단계 = 기본 체력
- "측정 안 하면 최적화 없다" — p95/p99 말할 수 있어야
- Idempotency, back-pressure, timeout, retry with backoff — 이 4개는 매직 워드

---

# 10. 용어 사전 (알파벳순 / 가나다 혼용)

| 용어 | 한 줄 설명 |
|---|---|
| **ANN (Approximate Nearest Neighbor)** | 근사 최근접 이웃 검색. 벡터 DB의 핵심 |
| **ADR (Architecture Decision Record)** | "이 결정을 왜 했는지" 기록하는 짧은 문서 |
| **ANTLR / sqlglot** | SQL 파서. Validator에서 씀 |
| **Backfill** | 과거 구간 재처리 |
| **Catchup** | Airflow가 과거 실행을 따라잡기 |
| **CDC (Change Data Capture)** | 원본 DB의 변경만 잡아 오는 기법 |
| **CI/CD** | 자동 빌드·테스트·배포 |
| **Conformed Dimension** | 여러 fact가 공유하는 차원 (date, region…) |
| **CTE (WITH)** | 쿼리를 단계로 나누는 구문 |
| **DAG** | Airflow·dbt의 태스크/모델 의존성 그래프 |
| **dbt** | SQL 변환 프레임워크. "테스트·문서 되는 SQL" |
| **Dim / Fact** | Kimball 모델링의 두 축 |
| **ELT / ETL** | 변환 타이밍 차이. ELT는 "일단 넣고 거기서 변환" |
| **Embedding** | 텍스트 → 벡터 변환 |
| **EXPLAIN** | 쿼리 실행 계획 보기 |
| **Grain** | fact 테이블 한 줄의 의미 |
| **Idempotency (멱등성)** | 몇 번 돌려도 같은 결과 |
| **Incremental** | dbt에서 "새로 들어온 것만" 처리 |
| **Ingestion** | 수집 단계 |
| **Kimball** | 차원 모델링의 대가. star schema 창시 |
| **Lineage** | 테이블·컬럼의 출처 추적 |
| **Materialization** | dbt 모델의 실체화 방식 (view/table/incremental/ephemeral) |
| **MERGE / UPSERT** | "있으면 update, 없으면 insert" |
| **OLAP / OLTP** | 분석용 / 트랜잭션용 |
| **p50 / p95 / p99** | 퍼센타일 응답시간 |
| **Parquet** | 컬럼 지향 파일 포맷. 대용량 분석 친화 |
| **pgvector** | Postgres의 벡터 확장 |
| **PII** | 개인식별정보 |
| **RAG (Retrieval-Augmented Generation)** | 검색한 걸 LLM에 넣어 답하게 하는 패턴 |
| **SCD** | 서서히 변하는 차원 (Type 1/2/3) |
| **Schema Drift** | 스키마가 슬그머니 바뀜 |
| **Singleflight** | 같은 요청 여러 개를 한 번만 실행 |
| **Snapshot (dbt)** | SCD Type 2 자동 생성 |
| **Source Freshness** | 원본이 최근에 업데이트됐는지 체크 |
| **Star Schema** | fact + dim을 별 모양으로 |
| **Staging / Marts** | 정제 단계 / 비즈 모델 단계 |
| **Text2SQL** | 자연어 → SQL |
| **Vector DB** | 임베딩을 저장·검색하는 DB |
| **Watermark** | "여기까지 처리했음" 표시 |
| **Window Function** | OVER() 절이 붙는 집계. ROW_NUMBER, LAG 등 |

* ARM64
* OLTP vs OLAPP
* Cron
* Index - B-Tree, BRIN, GIN, Hash
* ephemeral(?)
* 리네이지(?)

---

# 읽고 난 다음

이 문서를 한 번 쫙 훑었다면, **"단어들이 낯설지 않은 상태"** 가 되었을 거예요. 다음 단계는:

1. **실전 중급편**(`02_intermediate.md`)에서 각 주제의 **코드와 함정**을 보기
2. 코드를 직접 따라치면서 감 잡기
3. 막히는 개념만 **완전판**(`03_complete.md`)에서 깊이 파기
4. 그 다음에야 Claude Code에 부트스트랩 프롬프트를 넣고 AdInsight Agent Phase 1 시작

> "완벽하게 이해한 뒤 시작"은 함정이에요. **절반만 이해한 상태로 코드를 쓰면서 이해가 따라옵니다.** 문서 3개는 "막힐 때 돌아올 곳"으로 두세요.

행운을 빕니다 🚀
