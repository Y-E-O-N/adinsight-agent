# Stage 3 Mart Model — `mart_creator_sponsored_summary`

**Date**: 2026-06-08
**Model**: `marts.mart_creator_sponsored_summary`
**dbt file**: `dbt/models/marts/creator/mart_creator_sponsored_summary.sql`

## 1. 목적

`mart_creator_sponsored_summary`는 작성자별 광고/협찬 후보 활동을 BI와 포트폴리오 분석에서 바로 사용할 수 있게 정리한 creator mart다.

intermediate 모델이 재사용 가능한 계산 단위라면, mart 모델은 최종 사용자가 읽는 분석 테이블이다. 이 모델은 `int_ig_owner_activity`를 입력으로 받아 작성자별 게시물 수, 광고/협찬 후보 수, 좋아요 숨김 비율, engagement signal 여부를 한 행에 모은다.

이번 모델은 아래 질문에 답한다.

- 어떤 creator를 우선 검토해야 하는가?
- 작성자별 광고/협찬 후보 게시물 수는 몇 개인가?
- 좋아요 숨김 비율이 높은 creator는 누구인가?
- BI 대시보드나 포트폴리오 표에서 바로 보여줄 수 있는 creator 단위 결과는 무엇인가?

## 2. 핵심 SQL 패턴

### 2.1 mart 입력 모델

```sql
with owner_activity as (
    select * from {{ ref('int_ig_owner_activity') }}
)
```

`ref()`는 dbt 모델 간 의존성을 선언한다. 이 mart는 `int_ig_owner_activity`가 먼저 생성된 뒤 실행된다.

### 2.2 최종 분석 컬럼 선택

```sql
select
    owner_username,
    owner_full_name,
    posts,
    sponsored_candidate_posts,
    hidden_likes_posts,
    sponsored_candidate_rate,
    hidden_likes_rate,
    has_engagement_signal
from owner_activity
```

mart에서는 raw payload나 중간 계산에 필요한 보조 컬럼보다, BI에서 읽을 최종 분석 컬럼을 우선 남긴다.

### 2.3 creator review flag

```sql
(
    posts >= 2
    or sponsored_candidate_posts >= 1
) as included_in_creator_review
```

현재 기준은 학습용 1차 기준이다.

| condition | 의미 |
|---|---|
| `posts >= 2` | 반복 등장한 작성자 |
| `sponsored_candidate_posts >= 1` | 광고/협찬 후보 게시물이 1건 이상 있는 작성자 |

이 flag는 Superset 표나 포트폴리오 스크린샷에서 우선 검토 대상을 필터링하는 데 쓸 수 있다.

## 3. 현재 결과

Round 1 데이터 기준:

| metric | value |
|---|---:|
| creator rows | 46 |
| included creators | 24 |
| posts | 49 |
| sponsored candidate posts | 21 |

dbt 검증 결과:

| item | value |
|---|---:|
| models | 5 |
| data tests | 44 |
| mart tests | 5 |
| full test pass | 44 |
| warn | 0 |
| error | 0 |

Postgres relation:

| schema | table | type |
|---|---|---|
| `marts` | `mart_creator_sponsored_summary` | `BASE TABLE` |

## 4. AWS 대응 관계

현재 로컬 구현은 Postgres 컨테이너의 `marts` schema에 dbt table을 만드는 방식이다.

AWS managed 환경으로 대응하면 Redshift table 또는 Athena CTAS 결과 테이블에 가깝다. BI 도구는 이 mart를 직접 읽고, Airflow 또는 MWAA가 dbt run/test를 스케줄링한다. 운영 환경에서는 IAM 접근 제어, Glue Data Catalog 메타데이터, 쿼리 비용, refresh 주기, 실패 알림이 함께 필요하다.

## 5. Known Limitations

- Round 1 데이터가 49건으로 작아 creator ranking의 대표성이 낮다.
- 현재 `included_in_creator_review` 기준은 학습용 임시 기준이며, 데이터가 늘어나면 최소 게시물 수와 engagement 기준을 재조정해야 한다.
- `is_sponsored_candidate`는 caption 키워드 기반 후보값이므로 실제 광고 여부를 확정하지 않는다.
- mart는 현재 Instagram 단일 채널 기준이며, YouTube/TikTok 등 멀티 채널 creator 통합은 아직 포함하지 않는다.

## 6. 다음 학습 포인트

- Superset에서 이 mart를 dataset으로 등록하고 creator review table을 만든다.
- `included_in_creator_review = true` 기준으로 포트폴리오용 스크린샷을 캡처한다.
- 데이터가 늘어난 뒤 creator ranking 기준을 `posts`, `sponsored_candidate_rate`, `avg_likes_count_clean`, `avg_comments_count` 조합으로 개선한다.
