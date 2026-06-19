# Session 07 — 학습 개념 정리 (2026-05-26)

Phase 2 Stage 1에서 배운 raw 적재, Airflow task 연결, 멱등성 검증 개념을 복습용으로 정리한다.

---

## 1. L0 Raw Layer

### 1.1 개념
- L0 raw layer는 외부 API 응답을 가능한 원형 그대로 저장하는 계층이다.
- 이번 프로젝트에서는 Postgres `raw` schema가 L0 역할을 한다.
- AWS로 치면 S3 raw bucket + Glue Data Catalog + Lake Formation에 가깝다.
- 핵심 규칙은 "raw에서 변환하지 않고, 모든 정제는 staging/dbt 이후로 미룬다"이다.

### 1.2 이번 설계
```text
raw.ig_posts
- Instagram 게시물 자체
- 자주 조회할 필드는 평면 컬럼
- 전체 원본 응답은 raw_payload JSONB

raw.ig_post_sources
- 게시물이 어떤 source_hashtag에서 발견됐는지 기록
- PRIMARY KEY (post_id, source_hashtag)
```

---

## 2. JSONB 원본 보존

### 2.1 왜 JSONB를 쓰나
- API 응답은 필드가 자주 바뀔 수 있다.
- 지금 당장 쓰는 필드만 테이블 컬럼으로 만들면 나중에 원본 재처리가 어렵다.
- `raw_payload JSONB`에 전체 응답을 넣으면, 나중에 staging 모델에서 새 필드를 다시 꺼낼 수 있다.

### 2.2 선택한 절충
| 구분 | 저장 방식 | 이유 |
|---|---|---|
| `id`, `caption`, `likes_count`, `posted_at` | 평면 컬럼 | 자주 조회하고 인덱스/필터에 필요 |
| `images`, `child_posts`, `music_info` | JSONB | 구조가 중첩되어 있고 raw 보존이 중요 |
| 전체 응답 | `raw_payload JSONB` | 재처리 가능성 보존 |

---

## 3. Upsert와 멱등성

### 3.1 Upsert
Upsert는 update + insert를 합친 말이다.

```sql
INSERT INTO raw.ig_posts (...)
VALUES (...)
ON CONFLICT (id) DO UPDATE SET ...
```

동작:
1. 같은 `id`가 없으면 insert
2. 같은 `id`가 있으면 update
3. row가 중복 증가하지 않음

### 3.2 멱등성
- 같은 작업을 여러 번 실행해도 결과가 깨지지 않는 성질이다.
- 이번 검증에서는 같은 DAG를 5번 실행했다.
- 첫 실행은 `inserted=20`, 이후 4회는 `inserted=0`, `updated=20`이었다.
- 최종 row count는 `raw.ig_posts=20`, `raw.ig_post_sources=20`으로 유지됐다.

---

## 4. Source Lineage

### 4.1 왜 별도 테이블인가
처음에는 `raw.ig_posts.source_hashtag` 컬럼 하나로 저장할 수 있다. 하지만 같은 게시물이 여러 seed에서 발견되면 마지막 값이 이전 값을 덮어쓴다.

```text
post A 발견 경로:
- #올리브영
- #뷰티
```

단일 컬럼이면 둘 중 하나만 남는다. 그래서 별도 테이블로 분리했다.

### 4.2 `ON CONFLICT DO NOTHING`
```sql
INSERT INTO raw.ig_post_sources (post_id, source_hashtag)
VALUES (%s, %s)
ON CONFLICT (post_id, source_hashtag) DO NOTHING
RETURNING 1;
```

- 새 source link면 insert
- 이미 있으면 아무것도 하지 않음
- `RETURNING 1`이 있으면 새로 insert된 경우만 `fetchone()`으로 확인 가능

---

## 5. psycopg

### 5.1 역할
`psycopg`는 Python에서 PostgreSQL에 연결하고 SQL을 실행하는 드라이버다.

```python
with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()
```

### 5.2 이번 디버깅
- 로컬 `uv` 환경에는 `psycopg`가 있었지만 Airflow 이미지에는 없었다.
- `infra/airflow/requirements.txt`에 `psycopg[binary]`를 추가하고 Airflow 이미지를 재빌드했다.
- requirements 변경은 컨테이너 재시작만으로 반영되지 않고 `docker compose build`가 필요하다.

---

## 6. Airflow XCom

### 6.1 개념
XCom은 Airflow task끼리 작은 값을 주고받는 메커니즘이다.

```python
items = collect_one_hashtag()
load_posts(items)
```

겉으로는 Python 함수 호출처럼 보이지만 실제로는:
1. `collect_one_hashtag` task가 실행됨
2. 반환값이 Airflow metadata DB의 XCom에 저장됨
3. `load_posts` task가 실행될 때 그 값을 꺼내 인자로 받음

### 6.2 주의점
- XCom은 작은 값 전달용이다.
- 20건 smoke payload는 가능하다.
- Stage 2 본수집 2,000건 payload는 XCom으로 넘기기보다 task 내부 collect-and-load 또는 임시 landing 방식을 쓰는 편이 낫다.

---

## 7. Airflow 디버깅 패턴

### 7.1 Paused DAG
- `DAGS_ARE_PAUSED_AT_CREATION=true`라 신규 DAG는 paused 상태로 생성된다.
- `trigger`는 run을 만들지만 paused면 scheduler가 처리하지 않는다.
- 해결:
```bash
docker compose exec airflow-webserver airflow dags unpause ig_collect_smoke
```

### 7.2 `upstream_failed`
- 앞 task가 실패해서 뒤 task가 실행되지 못한 상태다.
- 이번에는 `collect_one_hashtag`가 실패했기 때문에 `load_posts`는 `upstream_failed`가 됐다.

### 7.3 Task 로그 위치
```text
logs/dag_id=ig_collect_smoke/run_id=.../task_id=.../attempt=1.log
```

traceback은 scheduler/worker 일반 로그보다 task 전용 로그에서 보는 것이 정확하다.

### 7.4 외부 API 인증 실패
이번 실패 원인:
```text
ApifyApiError: User was not found or authentication token is not valid
```

코드 버그가 아니라 토큰 인증 문제였다. 해결은 Apify token 교체와 컨테이너 재생성이었다.

---

## 8. 이번 세션 핵심 흐름

```text
Airflow DAG trigger
-> collect_one_hashtag
-> Apify에서 #다이소화장품 20건 수집
-> XCom으로 items 전달
-> load_posts
-> psycopg로 raw.ig_posts upsert
-> raw.ig_post_sources source lineage insert
-> DAG 5회 재실행
-> row count 20/20 유지
```

면접용 한 문장:

> 외부 API 응답을 JSONB로 원본 보존하고, 게시물 엔티티와 수집 경로 lineage를 분리한 뒤, Airflow DAG 5회 재실행으로 raw loader의 idempotency를 검증했습니다.
