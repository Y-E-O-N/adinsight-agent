# Session 10 Concepts — Creator Mart + Superset Asset

## 1. dbt 레이어 역할

이번 세션의 핵심 구조는 아래 3단계다.

| layer | 역할 | 이번 모델 |
|---|---|---|
| staging | raw row를 분석 가능한 이름과 타입으로 정리 | `stg_ig_posts` |
| intermediate | 반복해서 쓸 계산 단위 | `int_ig_sponsored_candidates`, `int_ig_owner_activity` |
| marts | BI와 포트폴리오가 직접 읽는 최종 테이블 | `mart_creator_sponsored_summary` |

staging과 intermediate는 view로 두고, mart는 table로 만들었다. BI 도구는 mart를 직접 읽는다.

## 2. `schema.yml`은 문서이면서 계약이다

`schema.yml`은 컬럼 설명만 적는 파일이 아니다.

```yaml
- name: owner_username
  data_tests:
    - not_null
    - unique
```

위 설정은 "이 모델은 작성자 1명당 1행"이라는 grain 계약을 dbt test로 검증한다.

주의할 점:

- 모델명은 SQL 파일의 dbt 모델명과 정확히 같아야 한다.
- 컬럼명은 SELECT 결과 컬럼과 정확히 같아야 한다.
- YAML 들여쓰기는 구조이므로 2칸 차이로도 parser error가 난다.

## 3. PostgreSQL 조건부 집계

이번 모델에서 반복해서 쓴 패턴:

```sql
count(*) filter (where is_sponsored_candidate) as sponsored_candidate_posts
```

`COUNT(*) FILTER`는 전체 row 중 특정 조건을 만족하는 row만 센다. 여러 조건별 count를 한 번의 group by에서 만들 수 있어 작성자별 요약 모델에 적합하다.

비율은 아래처럼 계산했다.

```sql
round(
    count(*) filter (where is_sponsored_candidate)::numeric / nullif(count(*), 0),
    4
) as sponsored_candidate_rate
```

- `::numeric`: 정수 나눗셈 방지
- `nullif(count(*), 0)`: 0으로 나누기 방지
- `round(..., 4)`: 소수점 4자리 정리

## 4. Superset 연결에서 host는 `postgres`

Mac 브라우저에서는 Superset을 `localhost:8088`로 연다.

하지만 Superset이 Postgres에 접속할 때는 컨테이너 내부 네트워크 기준이다. 그래서 host는 아래처럼 입력한다.

```text
Host: postgres
Port: 5432
Database: adinsight
```

`postgres`는 인터넷 도메인이 아니라 Docker Compose service name이다. Compose 네트워크 안에서는 service name이 DNS 이름처럼 동작한다.

## 5. 검증 순서

이번 세션에서 `dbt run`과 `dbt test`를 병렬 실행했을 때 relation missing 오류가 한 번 발생했다.

원인:

- `dbt run`이 view를 drop/create하는 중이었다.
- 동시에 `dbt test`가 아직 재생성되지 않은 view를 읽으려 했다.

안전한 검증 명령:

```bash
docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"
```

## 6. 이번 세션의 포트폴리오 증거

| asset | path |
|---|---|
| Superset screenshot | `docs/images/phase3_creator_review_table.jpg` |
| Superset export | `dashboards/superset_exports/adinsight_creator_review_export.zip` |
| metric log | `metrics/run_results.jsonl` |
| portfolio draft | `docs/portfolio_draft.md` |

핵심 수치:

- dbt models: 5
- dbt tests: 44/44 pass
- creator rows: 46
- included creator review rows: 24
- sponsored candidate posts: 21
