# Stage 3 Intermediate Model — `int_ig_owner_activity`

**Date**: 2026-06-06
**Model**: `intermediate.int_ig_owner_activity`
**dbt file**: `dbt/models/intermediate/int_ig_owner_activity.sql`

## 1. 목적

`int_ig_owner_activity`는 Instagram 작성자별 활동을 요약한다.

`stg_ig_posts`가 게시물 1건을 분석 가능한 row로 정리하고, `int_ig_sponsored_candidates`가 광고/협찬 후보 게시물만 분리한다면, 이 모델은 작성자 1명당 1행으로 집계해 creator mart의 기반을 만든다.

이번 모델은 아래 질문에 답한다.

- 어떤 작성자가 여러 게시물을 올렸는가?
- 작성자별 광고/협찬 후보 게시물 비율은 얼마인가?
- 좋아요 수가 숨겨진 게시물 비율은 얼마인가?
- 좋아요 또는 댓글 기반 engagement signal이 있는 작성자는 누구인가?

## 2. 핵심 SQL 패턴

### 2.1 작성자 단위 grain

```sql
group by owner_username
```

이 모델의 grain은 `owner_username`이다. 즉, 결과 row는 작성자 1명당 1개여야 한다.

그래서 `schema.yml`에서 `owner_username`에 `not_null`과 `unique` data test를 걸어 이 계약을 검증한다.

### 2.2 조건부 count

```sql
count(*) filter (where is_sponsored_candidate) as sponsored_candidate_posts
```

전체 게시물 중 광고/협찬 후보로 분류된 게시물만 센다.

같은 패턴으로 `likes_hidden`, `is_carousel`, `is_video`도 작성자별 count로 만든다.

### 2.3 작성자별 비율

```sql
round(
    count(*) filter (where is_sponsored_candidate)::numeric / nullif(count(*), 0),
    4
) as sponsored_candidate_rate
```

구성:

- `count(*) filter (...)`: 조건에 맞는 게시물 수
- `count(*)`: 작성자의 전체 게시물 수
- `::numeric`: 정수 나눗셈 방지
- `nullif(count(*), 0)`: 0으로 나누는 오류 방지
- `round(..., 4)`: 소수점 4자리로 정리

## 3. 현재 결과

Round 1 데이터 기준:

| metric | value |
|---|---:|
| owners | 46 |
| posts | 49 |
| sponsored_candidate_posts | 21 |
| avg_owner_sponsored_rate | 0.4565 |

전체 dbt data tests:

| item | value |
|---|---:|
| models | 4 |
| data tests | 39 |
| pass | 39 |
| warn | 0 |
| error | 0 |

## 4. AWS 대응 관계

현재 로컬 구현은 Postgres 컨테이너의 `intermediate` schema에 dbt view를 만드는 방식이다.

AWS managed 환경으로 대응하면 Redshift 또는 Athena 위에 dbt가 만든 curated intermediate view에 가깝다. 차이는 AWS에서는 IAM 권한, Glue Data Catalog, 컴퓨트 비용, 워크로드 격리, 운영 모니터링이 함께 필요하고, 현재 로컬 환경은 학습과 검증을 위한 단일 Postgres 컨테이너라는 점이다.

## 5. Known Limitations

- Round 1 데이터가 49건으로 작아 작성자별 비율은 대표성이 낮다.
- 대부분 작성자가 게시물 1건만 가지고 있어 `sponsored_candidate_rate`가 0 또는 1로 극단화되기 쉽다.
- `is_sponsored_candidate`는 caption 키워드 기반 후보값이므로 실제 광고 여부를 확정하지 않는다.

## 6. 다음 학습 포인트

- `int_ig_owner_activity`를 creator mart의 입력으로 승격할지 판단한다.
- 작성자별 집계와 게시물별 후보 모델을 함께 사용해 creator-level ranking을 만든다.
- 데이터가 늘어난 뒤 `posts >= N` 같은 최소 샘플 기준을 추가한다.
