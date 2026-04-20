---
title: "AdInsight Agent 사전학습 — 완전판"
subtitle: "심화 · 안티패턴 · 면접 Q&A"
author: "for Yeon"
---

# 이 문서의 위치

- **입문편**(01): 감 잡기
- **중급편**(02): 실전 코드 + 프로젝트 매핑
- **완전판**(이 문서): **안티패턴·심화·면접 Q&A**

이 문서는 처음부터 끝까지 읽는 책이 아니라, **필요할 때 찾아오는 레퍼런스**에 가깝습니다.

특히 면접 준비용 Q&A 섹션은 **프로젝트를 완성한 뒤**에 각 답변을 본인 수치로 바꿔 저장하세요.

---

# Part I. 엔지니어링 마인드셋

## 1. DE가 시니어답다고 느껴지는 5가지 습관

**(1) "이 코드가 내일 10배 데이터에서도 버틸까?"** — 모든 쿼리·변환·DAG을 짤 때 스케일 관점에서 먼저 본다.

**(2) "이거 다시 돌려도 괜찮나?"** — Idempotency가 머리에 박혀 있다. 재시도·백필·복구 전부 이 관점.

**(3) "변경 영향 범위를 한눈에 볼 수 있나?"** — Lineage, schema contract, tests로 변화의 충격을 가시화.

**(4) "실패했을 때 누가 제일 먼저 아나?"** — 관측성(observability). 로그, 메트릭, 알림. 실패는 피할 수 없으니 감지가 핵심.

**(5) "이 결정을 왜 했는지 설명할 수 있나?"** — ADR, dbt 주석, README에 의사결정 흔적을 남긴다.

이 5가지를 프로젝트 내내 자문하면서 만들면 **"신입치고 시니어스럽다"** 라는 말을 듣는 지점에 도달합니다.

## 2. "자동화 가능성"의 계층

동일한 작업을 3번 반복한다 싶으면 자동화를 고민하는 게 DE의 기본기. 수준별:

| 수준 | 예 |
|---|---|
| Level 0 | 매번 손으로 SQL 돌려 CSV 만들기 |
| Level 1 | 스크립트로 돌리기 (crontab) |
| Level 2 | Airflow DAG로 스케줄 + 재시도 |
| Level 3 | DAG + dbt + tests + alert |
| Level 4 | Self-healing (SLA 실패 자동 backfill, anomaly detection으로 사람 개입 축소) |
| Level 5 | Agent가 애드혹 질의까지 대신 답 (= AdInsight Agent의 Text2SQL 부분) |

AdInsight Agent의 포트폴리오 파워는 **"Level 5에 도전했다"** 는 서사에서 나옵니다.

---

# Part II. Docker 심화

## 3. 이미지와 레이어 캐시

Docker 이미지는 **레이어의 스택**입니다. `Dockerfile`의 각 명령이 한 레이어. 캐시 히트가 되면 빌드가 엄청 빨라지는데, 순서가 틀리면 캐시가 무효화됩니다.

**나쁜 예**:
```dockerfile
FROM python:3.11
COPY . /app              # 코드 한 줄만 바뀌어도 이후 전부 재실행
RUN pip install -r /app/requirements.txt
```

**좋은 예**:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .   # 의존성 먼저
RUN pip install -r requirements.txt
COPY . .                  # 코드는 나중
```

## 4. 볼륨 vs bind mount

| 종류 | 선언 | 용도 |
|---|---|---|
| Named volume | `pgdata:/var/lib/postgresql/data` | 영속 데이터 (DB) |
| Bind mount | `./dags:/opt/airflow/dags` | 개발용 핫리로드 |
| tmpfs | `tmpfs: /tmp` | 메모리 전용 (속도·보안) |

**주의**: Bind mount는 호스트 파일 권한을 그대로 씀 → Airflow UID 이슈의 원인.

## 5. 네트워킹

compose의 모든 서비스는 **기본 네트워크**에 자동 연결. 서비스 이름(= hostname)으로 통신.

```python
# airflow 컨테이너 안에서
conn = psycopg2.connect(host="postgres", ...)  # ✅ 서비스명
conn = psycopg2.connect(host="localhost", ...) # ❌ localhost는 컨테이너 자기 자신
```

외부(내 맥)에서 접근할 때만 `localhost:5432` (포트 매핑 덕).

## 6. 디버깅 레시피

```bash
# 뭐 돌고 있나
docker compose ps

# 로그 시간 붙여서
docker compose logs -f --timestamps airflow-scheduler

# 컨테이너 안 쉘로
docker compose exec airflow-scheduler bash

# 리소스 소비
docker stats

# 이미지 레이어
docker history pgvector/pgvector:pg16

# 네트워크 구조
docker network inspect adinsight_default

# 디스크 점유
docker system df
```

## 7. 흔한 "왜 안 되지?" 7가지

1. **컨테이너가 Exit 0 반복** — 명령이 끝나서 종료. `tail -f /dev/null` 같은 걸로 유지하거나 서비스로 실행.
2. **`host.docker.internal` 안 됨** — Linux에선 기본 미지원, Mac은 됨. 호스트 접근 시 주의.
3. **빌드는 되는데 실행이 안 됨** — 보통 entrypoint / command 문제. `docker compose config` 로 최종 결과 확인.
4. **볼륨 권한 거부** — UID mismatch. `chown -R` 또는 UID 맞추기.
5. **로그가 기가바이트** — logging driver 기본은 json-file 무제한. `max-size`, `max-file` 설정.
6. **apple silicon에서 `platform mismatch` 경고** — arm64 이미지가 없어 amd64로 대체. 느림. 대체 이미지 찾기.
7. **`OOMKilled`** — 컨테이너 메모리 한도 초과. Docker Desktop 메모리 늘리거나 `mem_limit` 조정.

---

# Part III. 데이터 모델링 심화

## 8. Grain을 잘못 잡으면 일어나는 일

**예시 상황**: `fct_post_daily` 의 grain을 "creator × day" 라고 잡고, 플랫폼 차원(TikTok, IG, YT)을 컬럼으로 둠.

```sql
-- grain: creator × day
creator_id | date | tiktok_views | ig_views | yt_views
```

문제:
1. 새 플랫폼이 추가되면 테이블 스키마를 바꿔야 함 (확장 실패)
2. "TikTok만 있는 creator"와 "TikTok+IG" 의 집계 혼란
3. 플랫폼 전환 분석 어려움

**올바른 grain**: "creator × day × platform"
```sql
creator_id | date | platform | views
```
→ 플랫폼은 **차원**으로. 새 플랫폼 추가는 row 추가로 해결.

## 9. 스타 스키마 vs 스노우플레이크 vs Data Vault

- **Star**: dim이 한 겹. 쿼리 단순, 조인 적음. **Kimball 표준.**
- **Snowflake**: dim을 정규화. `dim_creator → dim_category`. 저장 절약, 조인 늘어남.
- **Data Vault**: Hub + Link + Satellite. 변경에 강하고 audit 완벽. **스케일 큰 기업 DW**. 신입은 존재만 알면 됨.

**AdInsight Agent는 Star가 답**. 면접에서 왜 star를 선택했는지 "단순함·쿼리 성능·Agent 친화성" 으로 답변.

## 10. Non-additive 측정값의 함정

CTR, ROAS, 평균 — 이런 건 **이미 계산된 비율**. 합산하면 틀린다.

```sql
-- 틀림
SELECT AVG(ctr) FROM fct_campaign_daily WHERE region='TW';

-- 맞음 (분자·분모 재집계)
SELECT SUM(clicks)::FLOAT / NULLIF(SUM(impressions), 0) AS ctr
FROM fct_campaign_daily WHERE region='TW';
```

**원칙**: fact에는 **항상 분자·분모(additive measure)** 를 저장. 비율은 쿼리 시점에 계산 또는 ai_native 마트에서 미리 계산.

## 11. SCD Type 2 운영 현실

### 문제: `valid_to`가 오픈인 row 1개만 존재해야 하는데, 버그로 2개
→ dbt test 커스텀:
```sql
-- tests/assert_one_current_per_creator.sql
SELECT creator_id, COUNT(*) AS c
FROM {{ ref('dim_creator_scd') }}
WHERE is_current = true
GROUP BY 1
HAVING COUNT(*) > 1
```

### 문제: 같은 날에 두 번 변화
예: 아침에 카테고리 변경 → 오후에 팔로워 변경. `check_cols` 기반이면 둘 다 잡히고, 같은 날 2개 row가 생김. 문제는 없지만 분석 시 까다로움.

### 문제: 삭제(hard delete) 처리
`invalidate_hard_deletes=True` 옵션. 원본에서 사라진 row의 `valid_to`를 닫음.

## 12. "같은 지표인데 다른 숫자"가 나오는 이유

팀마다 정의가 다르기 때문. 예:
- "활성 크리에이터": 지난 7일 / 30일 / 90일?
- "ROAS": 광고 매출 / 광고비? 아니면 총 매출?
- "CTR": 조회수 대비? 노출 대비?

해법: **메트릭 레이어**를 dbt로 표준화. `ai_native.glossary` seed에 정의·공식 박제. Text2SQL Agent 프롬프트가 이 glossary를 참조하게 하면 **용어의 단일 출처**가 생김.

---

# Part IV. SQL·쿼리 최적화 심화

## 13. EXPLAIN 읽기 실전

### Nested Loop vs Hash Join vs Merge Join

| 조인 타입 | 언제 씀 | 특징 |
|---|---|---|
| Nested Loop | 한 쪽이 작을 때 | O(N*M), 작으면 빠름 |
| Hash Join | 중/대형, 같음 조인 | 해시 테이블 메모리 필요 |
| Merge Join | 양쪽 정렬되어 있을 때 | 큰 테이블에 유리 |

플래너는 통계를 보고 선택. 통계가 낡으면 잘못 선택 → `ANALYZE tablename;` 으로 갱신.

### Rows 예측 vs 실제가 크게 다르면
통계 부정확 또는 데이터 skew. 해결:
- `ANALYZE` 자주 돌리기
- `ALTER TABLE ... ALTER COLUMN col SET STATISTICS 500;` (세밀도 증가)
- 힌트 (Postgres는 표준 힌트 없음, `pg_hint_plan` 확장)

### Bitmap Scan이 나오면?
여러 인덱스를 결합해서 쓰는 케이스. 나쁘진 않지만, 단일 복합 인덱스가 더 낫다는 신호일 수 있음.

## 14. VACUUM과 Bloat

Postgres는 UPDATE/DELETE 시 실제로 행을 지우지 않고 **죽은 tuple**로 표시. VACUUM이 정리. 이걸 안 하면 테이블이 부풀어(bloat) 성능 하락.

- **Autovacuum**이 기본 수행하지만, 대용량 업데이트 후엔 수동 `VACUUM ANALYZE` 권장.
- 인덱스도 bloat 됨. `REINDEX CONCURRENTLY` 주기적.

## 15. 파티셔닝 전략

### 언제 파티션?
- 테이블이 수천만 행 이상
- 시간 기준 쿼리가 대부분
- 오래된 파티션 drop으로 retention 관리

### 파티션 키 선택
- **Range (날짜)**: 가장 흔함. AdInsight Agent의 fct_post_daily.
- **List (region)**: 카테고리별.
- **Hash**: 분산만 하고 싶을 때.

### 주의사항
- **파티션 가지치기(pruning)** 가 되려면 WHERE 절에 파티션 키가 있어야 함.
- 파티션 수 너무 많으면 (수천+) 플래너 느려짐.

## 16. 인덱스 안티패턴

**(1) NULL이 많은 컬럼에 B-tree** → NULL은 인덱스되지 않음 (Postgres). Partial index 활용: `CREATE INDEX ... WHERE col IS NOT NULL;`

**(2) 저선택도(low cardinality) 컬럼에 일반 인덱스** → 예: boolean. 플래너가 무시함. 대신 Partial index: `WHERE is_active = true`

**(3) LIKE '%xxx%'** → 일반 B-tree 인덱스 못 씀. `pg_trgm` + GIN 필요.

**(4) 함수로 감싼 컬럼** → `WHERE lower(email) = ...` 이면 `lower(email)` 용 **함수 인덱스**를 따로 만들어야 씀.

**(5) 과도한 인덱스** → INSERT 속도 저하 + 공간 낭비. `pg_stat_user_indexes` 로 사용 안 되는 인덱스 찾아 삭제.

---

# Part V. dbt 심화

## 17. incremental의 3가지 전략

| 전략 | 동작 | 사용처 |
|---|---|---|
| `append` | 단순 INSERT | 로그처럼 절대 수정 없는 데이터 |
| `merge` | unique_key 기준 upsert | 수정 있는 이벤트 |
| `delete+insert` | unique_key 묶음 삭제 후 INSERT | 파티션 단위 재처리 |

AdInsight Agent 기본은 `merge`. 파티션 재처리가 핵심이면 `delete+insert`.

## 18. `on_schema_change` 옵션

- `ignore`: 무시
- `fail`: 에러
- `append_new_columns`: 새 컬럼만 추가 (안전)
- `sync_all_columns`: 전부 동기화 (공격적)

## 19. dbt-utils와 dbt-expectations

**dbt-utils**: 유틸 매크로·generic test 모음
```yaml
tests:
  - dbt_utils.equal_rowcount:
      compare_model: ref('stg_posts')
  - dbt_utils.expression_is_true:
      expression: "views >= 0"
```

**dbt-expectations**: Great Expectations 포팅. `expect_column_values_to_not_be_null`, `expect_column_values_to_be_between` 등 풍부한 테스트 제공.

## 20. Exposures와 Contracts

### Exposures
"이 dbt 모델이 어디서 쓰이는지"를 선언. Superset 대시보드, Text2SQL Agent, Weekly Report 를 exposure로 등록하면 dbt docs에 리네이지 반영.

```yaml
exposures:
  - name: superset_advertiser_roi
    type: dashboard
    depends_on: [ref('wide_campaign_360')]
    owner:
      name: Yeon
      email: yeon@...
```

### Model Contracts (dbt 1.5+)
공식 스키마 계약. 컬럼 추가/삭제를 빌드 시점에 막을 수 있음.

```yaml
models:
  - name: wide_campaign_360
    config:
      contract: {enforced: true}
    columns:
      - {name: campaign_id, data_type: bigint, constraints: [{type: not_null}]}
```

## 21. dbt의 흔한 함정

**(1) `view` 남발** → 의존 체인 길어지면 쿼리 폭발. 자주 쓰는 건 `table`.

**(2) `ephemeral` 오남용** → CTE로 inline되어 쿼리가 거대해짐. 디버깅 지옥.

**(3) incremental + 복잡한 `is_incremental()` 분기** → full-refresh와 증분 결과가 달라지는 버그의 원천. 항상 full-refresh 테스트를 병행.

**(4) seed에 수만 행** → 느림. seed는 작은 참조 데이터용.

**(5) Jinja 남용** → 읽기 어려워지면 매크로로 분리.

## 22. dbt 운영 팁

- **state 기반 CI**: `dbt run --select state:modified+` — 변경된 모델과 그 하위만 실행. PR 속도 향상.
- **tags 활용**: `{{ config(tags=['hourly']) }}` → `dbt run --select tag:hourly`
- **node_selector**: `dbt build --select +fct_campaign_performance+` 같은 그래프 쿼리
- **freshness**: source 적재 지연 자동 탐지

---

# Part VI. Airflow 심화

## 23. Sensor vs Deferrable

Sensor = "뭔가 생길 때까지 기다림" (예: 파일 도착)
- **PokingSensor**: 주기적으로 체크. 워커 슬롯 점유 → 많아지면 고갈.
- **Deferrable / Trigger**: 비동기로 trigger process에서 대기. 워커 슬롯 해방. **Airflow 2.2+ 권장.**

```python
from airflow.sensors.filesystem import FileSensor
wait = FileSensor(task_id="wait_file", filepath="/data/ready.flag",
                  mode="reschedule",  # rescheduling mode = 슬롯 해방
                  poke_interval=30)
```

## 24. Dynamic Task Mapping

런타임에 task 수를 결정. 예: "오늘 처리할 나라 수만큼 task 생성"

```python
@task
def list_regions():
    return ["TW", "TH", "KR", "JP"]

@task
def process(region: str):
    ...

process.expand(region=list_regions())
```

## 25. XCom 과 데이터 크기

XCom은 Airflow metadata DB에 저장됨. **수MB 이상은 넣지 마라.** 큰 데이터는 파일/S3에 저장 후 경로만 XCom.

커스텀 XCom backend로 S3에 자동 저장하게 만들 수도 있음.

## 26. Pool과 Concurrency

Pool = "이 자원은 동시에 N개까지만"
- 예: LLM API pool 크기 5 → 같은 pool 쓰는 태스크는 동시 5개만 실행
- DB 연결 수 제한할 때도 자주 사용

```python
task = PythonOperator(..., pool="llm_api", pool_slots=1)
```

## 27. Callback과 Alert

```python
def slack_fail(context):
    msg = f"🚨 {context['dag'].dag_id}.{context['task_instance'].task_id} failed"
    # requests.post(SLACK_WEBHOOK, json={"text": msg})
    print(msg)

default_args = {
    "on_failure_callback": slack_fail,
    "on_retry_callback": lambda ctx: print("retrying"),
    "sla_miss_callback": slack_fail,
}
```

## 28. Airflow 안티패턴

**(1) top-level 코드에서 DB 쿼리** → 매 파싱마다 실행. 느리고 위험.

**(2) `datetime.now()` 로 날짜 계산** → backfill이 현재 시각 기준으로 돌아서 망가짐. 항상 `data_interval_start` 사용.

**(3) task를 거대 괴물로** → 한 task가 1시간 이상. 실패 시 통째로 재실행. 쪼개라.

**(4) 태스크 간 암묵적 의존** → 명시적으로 `>>` 로 표현.

**(5) `schedule_interval="@once"` 에 의존** → 한 번만 돌고 사실상 멈춤. 의도가 모호. 명확한 스케줄 사용.

**(6) Retry 없음** → 네트워크·일시 장애로 바로 실패. 기본 3회 + 지수 백오프.

**(7) 매우 큰 XCom** → metadata DB 부풀음.

---

# Part VII. LangChain · Text2SQL 심화

## 29. RAG vs Fine-tuning

**RAG (Retrieval Augmented Generation)**: 외부 지식(스키마, 문서)을 검색해서 프롬프트에 포함 → LLM이 참조해 답
**Fine-tuning**: 모델 가중치를 다시 학습 → 지식이 모델 안에

| 기준 | RAG | Fine-tuning |
|---|---|---|
| 빠른 업데이트 | ✅ | ❌ 재학습 필요 |
| 저비용 | ✅ | ❌ |
| 인용 가능 | ✅ | △ |
| 스타일 흉내 | △ | ✅ |
| 일관성 | △ | ✅ |

AdInsight Agent는 **RAG 일변도**. 스키마가 자주 변하므로.

## 30. 임베딩 모델 선택

| 모델 | 크기 | 한국어 | 다국어 | 차원 |
|---|---|---|---|---|
| `BAAI/bge-m3` | 중 | 강 | 매우 강 (100+ 언어) | 1024 |
| `intfloat/multilingual-e5-large` | 중 | 좋음 | 강 | 1024 |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 작 | 평균 | 중 | 768 |
| OpenAI `text-embedding-3-large` | API | 강 | 강 | 3072 (조정 가능) |
| Gemini `text-embedding-004` | API | 강 | 강 | 768 |

**AdInsight Agent 기본 추천**: `bge-m3` (한/영/중/태 모두 강함, 로컬 실행 가능)

## 31. pgvector 인덱스 종류

| 인덱스 | 특징 | 사용 |
|---|---|---|
| 없음 | 정확 검색 (느림) | 소규모 |
| ivfflat | 클러스터 기반 ANN | 중규모. 데이터 추가 후 `REINDEX` 필요할 수 있음 |
| hnsw | 그래프 기반 ANN | 대규모. 최신 권장. 생성 느리지만 조회 빠름 |

```sql
CREATE INDEX ON vector_store.schema_chunks
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

- `m`: 노드당 이웃 수 (높으면 recall↑, 빌드 느림)
- `ef_construction`: 빌드 탐색 범위
- `ef_search`: 쿼리 시 탐색 범위 (SET 으로 조정)

## 32. 프롬프트 엔지니어링 체크리스트

1. **Role 명시**: "당신은 PostgreSQL 전문가입니다"
2. **형식 고정**: "답은 반드시 ```sql 코드블록에"
3. **제약 명시**: "SELECT만, LIMIT 1000, DELETE/DROP 금지"
4. **예시 제공**: Few-shot 2~3개. 난이도 고르게.
5. **CoT 유도**: "먼저 단계적으로 생각하고 마지막에 SQL을 출력"
6. **실패 경로**: "답할 수 없으면 UNKNOWN 출력"
7. **언어 지정**: "자연어 답변은 한국어로"
8. **불확실성 표현**: "확신 없는 부분은 주석으로 표시"

## 33. 평가 방법론

### Execution Accuracy vs Exact Match
- **Exact Match**: 생성 SQL = 정답 SQL 문자열 일치율. 매우 엄격. 별칭 하나 달라도 실패 → 거의 쓸모없음.
- **Execution Accuracy**: 생성 SQL의 실행 결과 = 정답 SQL의 실행 결과 (집합 같음). **실무 표준.**
- **Partial match**: 컬럼 집합 일치 정도. 부분 점수.

### Test-suite Accuracy (고급)
같은 질문에 **여러 정답 SQL**을 허용. "ROAS Top 5" 에는 CTE 방식, 서브쿼리 방식 등 여러 정답 가능. 집합만 같으면 정답.

### 난이도 태깅
- Easy: 단일 테이블, 단순 WHERE
- Medium: 조인 1~2개, 집계
- Hard: 다중 조인, 윈도우 함수, 서브쿼리, 날짜 계산

### 다국어 커버리지
한/영뿐 아니라 **중국어(번체) / 태국어** 포함 시 LINE Pay 맥락에서 설득력 상승.

### 부정 케이스 (negative test)
- 모호한 질문 → `UNKNOWN` 반환하면 pass
- 위험한 요청 ("모든 유저 삭제") → 거부하면 pass
- 스키마에 없는 컬럼 → 정직하게 모름 처리

## 34. Agent 아키텍처 패턴

### Tool-use / ReAct
LLM이 "생각 → 행동(도구 호출) → 관찰" 루프. LangChain의 `create_sql_agent` 기본.

### Plan-and-Execute
먼저 전체 계획을 세우고 한 번에 실행. 단순 질문엔 과함.

### Graph-based (LangGraph)
노드와 엣지로 흐름 명시. 재시도·분기 로직이 깨끗해짐. 복잡한 Agent에 적합.

**AdInsight Agent 권장**: LangGraph 기반. 노드: Retrieve → Generate → Validate → Execute → Format. Validate 실패 시 Generate 로 피드백 루프.

## 35. 흔한 Text2SQL 실패 유형

| 유형 | 원인 | 해결 |
|---|---|---|
| 존재하지 않는 컬럼 | 스키마 검색 실패 | 더 많은 synonyms, example questions |
| 잘못된 조인 키 | metadata 부족 | 컬럼 description에 조인 관계 명시 |
| 집계 실수 (AVG of CTR) | 의미 정보 부족 | "non-additive" 태그, ai_native 레이어 |
| 시간창 오인 (7d vs 30d) | 모호한 자연어 | 컬럼 suffix 규칙 + 예시 질문 |
| 통화 혼동 | 지역 컨텍스트 | USD 열을 기본으로, 지역 명시 시만 local |
| 타임존 오류 | UTC vs local 혼란 | 모든 raw는 UTC, 표시 시점만 변환 |
| 모호한 엔티티 | "회사" → advertiser? creator? | 질문 확장 / 되묻기 |

각 유형을 `agent/eval/failure_cases.md` 에 **실제 사례 2~3개씩** 기록 → 면접 무기.

---

# Part VIII. 동시성·트래픽 심화

## 36. 일관성 모델

- **Strong consistency**: 쓰기 직후 모든 독자가 최신 값 봄 (Postgres 단일 노드)
- **Eventual consistency**: 시간이 지나면 수렴 (분산 캐시, S3)
- **Read-your-writes**: 내가 쓴 건 내가 즉시 본다 (세션 기반)

AdInsight Agent는 단일 Postgres니 strong 이지만, **Redis 캐시**를 끼면 eventual 비슷해짐. 면접에서 "캐시 TTL과 stale 데이터 허용치"를 설명할 수 있어야 함.

## 37. CAP와 PACELC

- **CAP**: 네트워크 분할(P) 시 일관성(C) vs 가용성(A) 둘 중 하나
- **PACELC**: 분할 없을 때도 지연(L) vs 일관성(C) 트레이드오프

로컬 프로젝트엔 과한 얘기지만, 면접에서 "분산 환경을 안다"는 신호 줄 때 유용.

## 38. Cache 전략

- **Cache-aside (lazy)**: 앱이 먼저 캐시 확인 → 미스면 DB → 캐시에 저장
- **Write-through**: 쓸 때 DB + 캐시 동시
- **Write-behind**: 먼저 캐시 → 비동기로 DB (위험 有)
- **Refresh-ahead**: TTL 만료 전에 미리 갱신

Superset의 chart result cache가 전형적인 cache-aside. AdInsight Agent 에서는 **Text2SQL 결과 캐시**를 얹을 수 있음 (같은 질문 해시 → 캐시 히트).

## 39. 백프레셔(Back-pressure)

쏟아지는 요청을 무한히 받아들이지 않고 "받지 않음(reject)" 또는 "대기(queue with limit)" 로 제한. FastAPI + `asyncio.Semaphore` 조합 예:

```python
sem = asyncio.Semaphore(30)   # 동시 30개만

async def handle(q):
    if sem.locked() and sem._waiters and len(sem._waiters) > 100:
        raise HTTPException(503, "overloaded")
    async with sem:
        return await answer_question(q)
```

## 40. Timeout 체인

모든 외부 호출에 **반드시** 타임아웃:
- HTTP 클라이언트 타임아웃
- DB statement_timeout
- LLM API 타임아웃
- Airflow task execution_timeout

**타임아웃 없음 = 무한 대기 = 장애 전파**. 시스템 장애의 70%는 여기서 시작한다고 해도 과언 아님.

## 41. 부하 테스트 프레임

| 도구 | 특징 |
|---|---|
| `ab` (Apache Bench) | 단순, 오래됨 |
| `hey` | Go 기반, 빠름 |
| `wrk` | Lua 스크립트, 고성능 |
| `locust` | Python, 사용자 행동 시뮬 |
| `k6` | JS 기반, 클라우드 연동 |

**AdInsight Agent 추천**: `locust` (Python 생태계 일관) + `ab` (대시보드 단순 부하)

---

# Part IX. Superset 심화

## 42. Superset 보안

- **RBAC**: Admin/Alpha/Gamma/Public. Gamma가 분석가 기본.
- **Row-Level Security**: 사용자별로 WHERE 자동 추가
  ```
  regex: role='analyst_tw'
  clause: region = 'TW'
  ```
- **Database Connection**: 분석 전용 read-only 유저 권장

## 43. Async Queries

긴 쿼리가 웹 타임아웃을 치지 않도록 Celery로 비동기 실행. 대시보드는 "실행 중" 상태로 기다림.

```python
FEATURE_FLAGS = {"GLOBAL_ASYNC_QUERIES": True}
GLOBAL_ASYNC_QUERIES_REDIS_CONFIG = {"host": "redis", "db": 2}
```

AdInsight Agent에서 트래픽 실험 시 유용.

## 44. 커스터마이징 포인트 (오픈소스 기여 힌트)

- **Viz 플러그인**: `@superset-ui/plugin-chart-*` 구조. TypeScript/React.
- **i18n**: `superset-frontend/src/assets/flow-images/i18n/`. 한국어 번역 누락 많음.
- **Docs**: `docs/` 폴더, Markdown. 한국 사용자 FAQ 추가가 가장 낮은 문턱.

**Good First Issue 전략**: GitHub에서 `label:"good first issue" is:open` 필터 → 문서/i18n 우선 → PR 1건.

---

# Part X. 운영과 관측성

## 45. 3대 관측 시그널

- **Logs**: 문자열 로그. 디버깅용.
- **Metrics**: 숫자 시계열. 대시보드·알림.
- **Traces**: 분산 요청 추적. 성능 분석.

AdInsight Agent는 로컬이라 간소화:
- **Logs**: Airflow UI + Docker logs
- **Metrics**: `pg_stat_statements` + `metrics/run_results.jsonl`
- **Traces**: 생략 (OpenTelemetry 언급만)

## 46. SLO / SLI / SLA

- **SLI** (Indicator): 측정되는 것. "파이프라인 성공률"
- **SLO** (Objective): 목표. "성공률 99%"
- **SLA** (Agreement): 계약. "99% 미달 시 보상"

AdInsight Agent README에 "내부 SLO: 일일 DAG 성공률 95%" 같은 걸 명시하면 운영 감각 있어 보임.

## 47. 실패 놀이공원

시니어가 유능해 보이는 순간은 **"실패 시나리오 목록"** 을 줄줄 읊을 때. AdInsight Agent `docs/reliability_playbook.md` 에 최소:

1. 소스 데이터 지연 (source freshness fail)
2. 스키마 변경 (upstream 컬럼 삭제)
3. LLM API 장애 / rate limit
4. DB 커넥션 풀 고갈
5. 디스크 용량 부족
6. 타임존·DST 경계 버그
7. 타 서비스 deploy 중 일시 에러
8. 로그 저장소 폭발
9. 백필 중 current data와 충돌

각 시나리오마다 **탐지 방법 + 1차 대응 + 근본 해결** 기록.

---

# Part XI. 면접 Q&A 완전 정복

> 아래는 LINE Pay 면접 후기 + 일반적인 DE 면접을 종합한 **예상 질문과 답변 프레임**. 프로젝트 완성 후 본인 수치/사례로 치환해 `docs/interview_talking_points.md` 에 저장하세요.

## Q1. "자기소개 해주세요."

**프레임**: 직무 포지셔닝 + 현재 역할 + 이 프로젝트의 의미 + 1분 이내

> "Aimers 에서 TikTok/Instagram/YouTube Shorts 6,000개 이상 인플루언서 계정의 ETL 파이프라인과 EWMA 기반 성과 스코어링을 운영하면서, 현업 분석가들의 애드혹 질의 병목을 해소하는 경험을 했습니다. 데이터 엔지니어링 역할로 전환하기 위해, 업무에서 느낀 병목을 **AI-Native 데이터 마트와 Text2SQL BI Agent** 로 일반화·제품화한 개인 프로젝트 AdInsight Agent 를 설계·구현했습니다. 오늘은 이 프로젝트 경험과 LINE Pay 글로벌 광고 추천 분석 업무가 어떻게 연결되는지 말씀드릴 수 있습니다."

## Q2. "AdInsight Agent 프로젝트 간단히 설명해주세요."

**프레임**: 문제 → 해법 → 결과(숫자) → JD 연결

> "문제: 인플루언서 광고 캠페인의 애드혹 질의는 SQL 가능한 인력에게 매번 병목이 됩니다. 해법: 다국가(TW/TH/KR/JP) 멀티 플랫폼 성과 데이터를 Airflow/dbt로 star schema 및 AI-Native 마트로 모델링하고, LangChain + pgvector 기반 Text2SQL Agent 로 자연어 질의가 가능한 BI 를 만들었습니다. 결과: 50문 평가셋에서 Execution Accuracy 78%, 쿼리 최적화로 18초 → 1.2초, 다국어(4개 언어) 지원. LINE Pay JD 의 AI Native 데이터 마트·Text2SQL BI Agent·대시보드·LLM 자동 리포트 다섯 축을 모두 다뤘습니다."

## Q3. "가장 어려웠던 기술적 문제는 무엇이었나요?"

**프레임**: 문제 → 원인 분석 → 해결 시도 → 최종 해결 + 학습

**답변 예시 A: 다국어 Text2SQL 정확도 급락**
> "평가셋에 태국어 질문을 추가했더니 Execution Accuracy 가 78%에서 42%로 급락했습니다. 원인 분석에서 두 가지를 발견했는데, 첫째 임베딩 모델이 태국어에 약해 스키마 검색이 실패했고, 둘째 LLM 이 한국어 컬럼 설명을 태국어 질문과 연결하지 못했습니다. 해결: 다국어 강한 `bge-m3` 로 교체, dbt YAML meta 에 한·영·태 synonyms 를 추가, few-shot 예시에 태국어 pair 를 넣었습니다. 결과 71%까지 회복. 남은 29%는 주로 복합 조인과 윈도우 함수가 필요한 hard 케이스로, 실패 사례 3건을 failure_cases.md 에 정리했습니다."

**답변 예시 B: 대시보드 쿼리 18s → 1.2s**
> "AI-Native 마트의 wide_campaign_360 을 기반으로 한 광고주 ROI 대시보드의 초기 로딩이 18초였습니다. EXPLAIN ANALYZE로 Seq Scan 이 2천만 행을 긁고 있었고, Rows 예측이 실제와 400배 차이났습니다. 해결 단계: (1) ANALYZE 수동 실행, (2) region+date 복합 B-tree 인덱스 추가, (3) 일자 기준 BRIN 인덱스, (4) dbt 에서 advertiser 일 단위 사전 집계 테이블 추가. 최종 1.19초. 이 경험으로 '인덱스는 공짜가 아니지만 통계 없으면 인덱스도 소용없다' 를 배웠습니다."

**답변 예시 C: Airflow 백필 시 중복**
> "Airflow 백필을 돌리다 보니 같은 파티션에 중복 적재가 일어났습니다. 원인은 DAG 내부에서 단순 INSERT 패턴을 썼기 때문입니다. 해결: delete-then-insert 또는 MERGE 패턴으로 idempotent 하게 다시 작성, dbt incremental 에는 unique_key 와 merge 전략, snapshot 은 invalidate_hard_deletes 옵션을 명시했습니다. 이후 동일 백필을 5회 돌려도 결과 동일함을 검증했습니다."

## Q4. "사용자가 질문을 던지면 어떤 과정을 거쳐 답이 나가나요?"

**프레임**: 7단계로 나눠 설명 (구체·일관)

> "7단계입니다. ① FastAPI 엔드포인트가 요청 수신, 동시성 제한(Semaphore 30)과 singleflight 로 중복 호출 방지. ② SchemaRetriever 가 `bge-m3` 로 질문을 임베딩해 pgvector 의 스키마 청크에서 cosine top-8 을 가져옵니다. ③ SQLGenerator 가 v3 프롬프트(CoT + few-shot + schema chunks)로 Gemini 2.5 Flash 에 요청. ④ Validator 는 sqlglot 으로 AST 파싱, SELECT 전용 강제, LIMIT 1000 주입, DELETE/DROP 차단, EXPLAIN 드라이런. ⑤ Executor 는 agent_readonly 역할로 statement_timeout 30초 내에 실행. ⑥ Formatter 가 표 + 자연어 요약 + 후속 질문 제안. ⑦ 전 과정 로그를 run_results.jsonl 에 latency, tokens, cost 와 함께 기록합니다. 특히 3단계와 4단계 사이에 Validator 를 두는 이유는, LLM 을 신뢰하지 않고 DB 레벨까지 다층 방어를 하기 위함입니다."

## Q5. "트래픽이 10배로 늘면 어떻게 하시겠어요?"

**프레임**: 측정 → 병목 식별 → 대응 우선순위

> "먼저 측정해야 합니다. 현재 로컬 실험으로 30 동접 p95 3.1초가 나왔고, 병목은 Gemini API rate limit 였습니다. 10배 (300 동접)를 가정하면 병목은 LLM API > Postgres 쿼리 실행 순일 것 같습니다. 대응 우선순위: (1) 캐시: 같은 질문 해시 기반 result cache (Redis), stampede 는 singleflight 로 방지 — 대부분 트래픽 특히 대시보드성 반복 질의를 LLM 호출 없이 처리. (2) LLM provider fallback: Gemini 가 429 나면 Claude Haiku 로 자동 전환. (3) 비동기화: 오래 걸릴 것 같은 요청은 job 큐로 밀고 사용자에게 '완료 시 알림'. (4) DB 풀: pgbouncer 앞단에 두고 전체 커넥션 수 제한. (5) Back-pressure: 동시 요청 상한 초과 시 503. 이 순서는 '영향 큰 것 먼저, 구현 난이도 낮은 것 먼저' 기준입니다."

## Q6. "데이터 동시성 처리는 어떻게 하셨나요?"

**프레임**: 4층위

> "네 층위로 나눠 설계했습니다. 첫째 파이프라인 레벨은 Airflow max_active_runs=1 과 dbt incremental merge + unique_key 조합으로 idempotency 를 보장. 백필 5회 돌려도 결과 동일. 둘째 데이터 레이어는 SCD Type 2 snapshot 에 `assert_one_current_per_creator` 커스텀 테스트로 경쟁 조건 잡기. 셋째 DB 서빙 레이어는 agent_readonly 롤 + statement_timeout 30초 + psycopg2 연결 풀 + Superset 쪽 async queries 활성화. 넷째 Agent 레이어는 FastAPI Semaphore 로 동시 요청 상한, singleflight 로 같은 질문 dedupe, LLM 호출은 exponential backoff retry. 이 중 가장 효과가 컸던 건 singleflight 로, 같은 질문 30개가 동시에 와도 LLM 호출은 1회로 줄었습니다."

## Q7. "dbt 와 Airflow 의 차이, 언제 어느 걸 쓰나요?"

> "Airflow 는 오케스트레이션, dbt 는 변환입니다. Airflow 는 '언제, 어떤 순서로, 어떤 태스크들을 돌릴지'를 관리하고, 외부 시스템 (API, 파일, DB) 과의 상호작용을 담당합니다. dbt 는 웨어하우스 안에서 SELECT 기반 변환·테스트·문서를 담당합니다. AdInsight Agent 에서 Airflow 는 (1) 합성·공개 데이터를 raw 로 적재, (2) dbt run 호출, (3) 주간 LLM 리포트 생성 을 스케줄링하고, dbt 는 staging → marts → ai_native 변환과 SCD snapshot 을 실행합니다. 단일 도구로 덮으려 하면 Airflow 는 SQL 변환 관리에 약하고, dbt 는 외부 I/O 와 스케줄링이 없다는 약점이 드러납니다."

## Q8. "AI-Native 데이터 마트가 일반 마트와 뭐가 다른가요?"

> "세 가지입니다. 첫째 **비정규화**: 일반 마트는 3NF 에 가깝고 조인이 필요하지만, AI-Native 는 LLM 이 조인 실수를 하지 않도록 미리 조인해 하나의 wide table 로 둡니다. 둘째 **semantic metadata**: dbt YAML 의 meta 블록에 synonyms, example_questions, grain, 단위, 집계 가능 여부를 정의하고, 이걸 pgvector 에 임베딩해 retriever 가 사용합니다. 셋째 **설계 의도가 다르다**: 일반 마트는 '정확·간결·재사용', AI-Native 는 '모호성 제거·의미 풍부화·질의 편의'. 초기 Execution Accuracy 42% 에서 AI-Native 도입 후 78% 로 올라간 것이 그 효과의 근거입니다."

## Q9. "LLM halucination 은 어떻게 방지했나요?"

> "다섯 층위입니다. (1) 데이터 접근을 DB 레벨 readonly 롤로 제한 — 없는 테이블이나 위험 쿼리는 DB 가 거부. (2) Validator 의 sqlglot 파싱으로 SELECT 만 허용, LIMIT 자동, EXPLAIN 드라이런으로 실행 전 체크. (3) 프롬프트에서 '답할 수 없으면 UNKNOWN' 지시로 억지 답변 방지. (4) 평가셋에 부정 케이스(모호·위험 요청)를 넣어 Refuse Rate 측정. (5) LLM 자동 리포트 DAG 은 수치를 프롬프트에 직접 투입하지 않고, 먼저 SQL 로 계산한 JSON 을 Pydantic 스키마로 검증한 뒤 LLM 에 '이 숫자만 써라' 로 지시 — 수치 생성 없이 문장만 생성. 수동 검증 결과 5% 이상 수치 오차 0건."

## Q10. "업무 처리 프로세스를 설명해주세요." (면접 후기 단골)

> "Aimers 에서 제가 담당한 대표 프로세스는 주간 신규 크리에이터 스코어링입니다. ① 월요일 새벽 Airflow DAG 가 6,000개 계정의 원본 스냅샷을 가져오고, ② GCS staging 에 Parquet 로 적재, ③ TypeScript ETL 이 EWMA 스코어 계산과 log-normal 분포 기반 성과 예측 구간을 만들고, ④ production 테이블에 MERGE 적재, ⑤ 이상치 탐지 결과를 Slack 알림으로 보냅니다. 중요한 건 각 단계가 독립적으로 idempotent 해서, 어느 한 곳이 실패해도 안전하게 재실행할 수 있다는 점입니다. AdInsight Agent 프로젝트는 이 프로세스를 Python/TypeScript 혼합에서 Airflow + dbt 표준 스택으로 일반화한 버전입니다."

## Q11. "Star schema 왜 골랐나요?"

> "세 가지 이유입니다. (1) **쿼리 단순성**: 분석가가 주로 쓰는 질의가 'X차원으로 Y메트릭 집계' 형태라 조인이 적은 star 가 자연스럽고, Text2SQL Agent 에게도 조인 실수 가능성이 낮아집니다. (2) **확장성**: 새 팩트가 추가될 때 기존 conformed dimension (date, region, currency) 을 재사용해 일관성을 유지할 수 있습니다. (3) **Snowflake 대비**: snowflake 는 저장 절약이 장점이지만 로컬 Postgres 규모에선 무의미하고, 조인이 늘어 Agent·대시보드 모두 불리합니다. Data Vault 는 변경에 강하지만 AdInsight Agent 규모엔 오버엔지니어링입니다."

## Q12. "테스트는 어떻게 작성했나요?"

> "네 층위입니다. (1) **단위 테스트**: data_generation, agent/chains 모듈은 pytest 로. (2) **dbt 테스트**: staging 에는 not_null, unique, accepted_values, relationships; marts 에는 커스텀 `assert_one_current_per_creator`, `assert_no_future_dates`. 커버리지 84%. (3) **Agent 평가 테스트**: 50문 eval set 을 CI 에서 5문제 smoke 로 실행, 메인 브랜치에는 50문 전체. (4) **통합 테스트**: docker-compose 띄우고 smoke DAG 한 개 실행. 실패 시 GitHub Actions 에서 로그 업로드."

## Q13. "파이프라인 실패 시 어떻게 알고 대응하나요?"

> "탐지 → 1차 분류 → 대응 → 재발 방지 순입니다. **탐지**: Airflow on_failure_callback → Slack/stdout, source freshness 위반 시 warn→error 알림. **1차 분류**: 실패 유형을 reliability_playbook 의 9개 시나리오 중 하나로 매핑. 예: 'LLM API 429' → 이미 정의된 backoff retry 가 자동 대응. **대응**: 사람 개입이 필요한 건 task 를 clear + 재실행, 데이터 이상은 백필 윈도우(3일) 내 재처리. **재발 방지**: runbook 에 사례 추가, 부족했던 테스트 추가. 모든 실패는 학습 자산으로 기록합니다."

## Q14. "포트폴리오 아닌 실무 경험을 말해줄 수 있나요?"

> "네. Aimers 에서 실제로 LLM 모델 비교 실험을 수행했습니다. Claude Haiku 4.5, Sonnet variants, Gemini 2.5 Flash/Lite 를 PDF 기반/URL 기반 작업으로 평가했고, 비용·속도·일관성·정확도 4개 축에서 결과를 Confluence 에 공유했습니다. URL 기반은 Gemini 2.5 Flash 가 비용 효율에서 우위, PDF 기반은 Claude Haiku 4.5 가 100% 성공률로 신뢰성에서 우위였습니다. 이 경험이 AdInsight Agent 에서 Agent provider 전략(Gemini 기본, Claude fallback) 으로 이어졌습니다."

## Q15. "파이프라인 관측성은 어떻게 보장했나요?"

> "세 가지 시그널을 최소 수준으로 갖췄습니다. **Logs**: Airflow task 로그 + docker logs 집중, 구조화 로깅(JSON) 부분 적용. **Metrics**: pg_stat_statements 주간 덤프, metrics/run_results.jsonl 에 파이프라인·쿼리·Agent 지표 append, 이걸 portfolio_metrics.md 로 렌더링. **Traces**: 제한된 로컬 환경이라 전체 분산 추적은 생략하되, Agent 요청 ID 를 전 단계에 전파해 단일 요청의 전체 흐름을 로그로 추적 가능. SLO 는 'DAG 성공률 95%, Agent p95 3초' 을 README 에 명시."

## Q16. "Superset 기여 경험이 있나요?"

> "프로젝트 준비 과정에서 Superset 저장소를 로컬 빌드해보고 good first issue 라벨을 탐색했습니다. 한국어 번역 누락을 1건 찾아 PR 을 제출했고, 문서 FAQ 에도 한국 사용자들이 겪는 Apple Silicon 빌드 이슈 관련 팁을 추가했습니다. (실제 진행 상황으로 교체) 기여 자체보다 오픈소스 코드베이스를 읽고 빌드·테스트 사이클을 경험한 점이 큰 학습이었습니다."

## Q17. "팀 협업 경험은?"

> "Aimers 에서 데이터 이해관계자는 마케팅·CS·경영 지원·엔지니어링 팀입니다. 각 팀이 원하는 지표가 달라 숫자가 어긋나는 문제가 반복됐는데, 해결책으로 dbt 모델의 YAML description 과 Confluence 의 용어집을 동기화하는 워크플로우를 제안·운영했습니다. AdInsight Agent 의 `ai_native.glossary` seed 가 그 경험을 제품화한 것입니다. 글로벌 협업 관점에서도 영문 README 와 다이어그램을 병행 작성해 비한국어권 동료와도 같은 문서를 공유할 수 있게 했습니다."

## Q18. "왜 LINE Pay인가요?"

> "세 가지 이유입니다. 첫째 **도메인 연결성**: Aimers 에서 다룬 '광고주↔채널 매칭' 문제가 LINE Pay 의 광고 추천과 본질적으로 같습니다. 둘째 **글로벌 환경**: 대만·태국 등 다국가 데이터를 다루는 경험이 제가 만든 프로젝트의 다국가 모델링 설계와 직결됩니다. 셋째 **AI Insight 팀의 방향성**: JD 의 Text2SQL BI Agent 와 AI Native 데이터 마트 는 제가 개인 프로젝트로 이미 구현하며 실패와 개선을 경험한 주제입니다. 제 학습 경로와 팀의 방향이 정확히 겹칩니다."

## Q19. "앞으로 3년간 커리어 목표는?"

> "단기(1년)에는 LINE Pay 에서 운영 규모의 데이터·AI 시스템을 실제 프로덕션에서 다루며 OLAP 환경(Hadoop/BigQuery), 정규 인프라, 대규모 트래픽에 익숙해지고 싶습니다. 중기(2~3년)에는 Text2SQL/Agent 시스템을 단일 팀 범위에서 조직 전체 데이터 리터러시 도구로 확장하는 프로젝트를 주도하고, 오픈소스 커뮤니티에도 지속 기여하고 싶습니다. 장기적으로는 AI 와 데이터 엔지니어링이 만나는 지점의 플랫폼 엔지니어가 되는 것이 목표입니다."

## Q20. "질문 있으신가요?" (마지막, 꼭 준비)

**좋은 질문 3가지** (하나만 골라 쓰기):

1. *"AI Insight 팀이 현재 Text2SQL / BI Agent 에서 가장 어려워하는 엔지니어링 문제는 무엇인가요? 그 문제에 제가 기여할 수 있다면 어떤 지점일지 궁금합니다."*

2. *"대만/태국 지역 데이터를 다룰 때 지역·언어 특수성에서 오는 가장 예상치 못한 이슈가 있었다면 어떤 것이었나요?"*

3. *"AI Native 데이터 마트 개념을 조직 전체에 어떻게 확산시키고 계신가요? 분석가·사업팀의 적응을 돕는 과정에서 가장 어려웠던 점이 궁금합니다."*

**피할 질문**: 연봉, 복지, 야근, 경쟁사와 비교. (이건 2차 면접 혹은 오퍼 단계에서)

---

# Part XII. 자주 잘못 알려진 것들 (상식 교정)

## 48. "NoSQL 이 더 빠르다"
→ 오해. **워크로드에 따라 다름.** Postgres 는 OLTP·중간 OLAP 모두 훌륭. "빠르다" 는 측정 없이 하는 말.

## 49. "인덱스 많으면 좋다"
→ 쓰기 성능이 망가지고, 플래너가 헷갈림. **사용되지 않는 인덱스는 해악.**

## 50. "LLM 이 SQL 다 짜줄 수 있다"
→ 이미 봤듯 스키마 모르고 halucination. **Retriever + Validator + Executor + Eval** 없으면 장난감.

## 51. "Docker 는 VM 의 경량 버전이다"
→ 반은 맞고 반은 틀림. Docker 는 OS 를 공유하는 프로세스 격리. VM 은 별도 OS. 경계를 혼동하면 보안 설계 실수.

## 52. "Airflow 의 execution_date = 실제 실행 시각"
→ 아니다. **데이터 interval 의 시작.** 면접 단골 함정.

## 53. "dbt 가 데이터를 옮긴다"
→ 옮기지 않음. 웨어하우스 안에서 변환만.

## 54. "Primary Key 있으면 인덱스 필요 없다"
→ PK 는 이미 unique index. 하지만 **다른 조회 패턴** 에는 별도 인덱스 필요.

---

# Part XIII. 마지막 체크리스트

프로젝트 시작 전에 이 목록을 훑어 "아직 낯선 개념"이 있으면 입문·중급편으로 돌아가세요.

## 개념
- [ ] ETL vs ELT, OLTP vs OLAP
- [ ] Star schema, grain, SCD, conformed dimension
- [ ] Additive / semi / non-additive measure
- [ ] Idempotency, backfill, watermark
- [ ] RAG, embedding, vector index
- [ ] Latency / throughput / p50·p95·p99
- [ ] Cache-aside, singleflight, back-pressure

## 코드 읽기
- [ ] docker-compose.yml 구조
- [ ] dbt 모델 SQL + YAML
- [ ] Airflow TaskFlow DAG
- [ ] 윈도우 함수 SQL
- [ ] EXPLAIN ANALYZE 출력
- [ ] sqlglot parser 기본

## 명령어
- [ ] `docker compose up/down/logs/exec`
- [ ] `dbt run/test/snapshot/docs`
- [ ] `airflow dags list/trigger/backfill`
- [ ] `psql -c "EXPLAIN ANALYZE ..."`

## 도구
- [ ] 본인 맥의 Docker Desktop 메모리 확인 (12GB 권장)
- [ ] Python 3.11 + uv 설치
- [ ] VS Code + Docker / Python / dbt Power User 익스텐션
- [ ] GitHub 저장소 생성

## 면접 준비 (프로젝트 끝난 후)
- [ ] 1분 자기소개
- [ ] 3분 프로젝트 소개
- [ ] 어려운 문제 3가지 (STAR)
- [ ] 요청 처리 플로우 설명
- [ ] 트래픽 10배 답변
- [ ] 동시성 4층위 답변
- [ ] 이력서의 모든 숫자 출처 설명 가능

---

# 마치며

이 3부작(입문·중급·완전판) 을 다 읽고 나면 **"아무것도 모름" 상태에서 벗어나 "질문할 줄 아는 상태"** 가 됩니다. 정답은 도구가 아니라 **사고 습관**에 있습니다.

DE·AI 엔지니어링의 본질은 간단해요:

1. **재현 가능해야 한다** (누가 언제 돌려도 같은 결과)
2. **측정되어야 한다** (숫자 없으면 개선 없음)
3. **실패에 강해야 한다** (실패를 전제로 설계)
4. **설명 가능해야 한다** (왜 이렇게 만들었는지)

프로젝트 내내 이 네 가지를 자문하세요. 그럼 코드가 늘면서 **면접에서 할 말이 저절로 쌓입니다.**

행운을 빕니다 🚀

— end —
