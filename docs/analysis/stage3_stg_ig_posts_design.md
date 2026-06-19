# Stage 3 Staging Model — `stg_ig_posts`

**Date**: 2026-06-05
**Model**: `staging.stg_ig_posts`
**dbt file**: `dbt/models/staging/stg_ig_posts.sql`

## 1. 목적

`stg_ig_posts`는 raw Instagram 게시물을 분석하기 좋은 1-post-per-row 모델로 정리한다.

핵심 원칙:

- raw 값은 보존한다.
- 분석에서 오해하기 쉬운 값은 flag와 clean 컬럼으로 분리한다.
- source lineage는 게시물 단위 배열과 count로 붙인다.
- 광고/협찬 여부는 확정값이 아니라 후보 flag로 둔다.

## 2. raw에서 staging으로 바뀐 것

| staging column | raw source | 의미 |
|---|---|---|
| `post_id` | `raw.ig_posts.id` | 게시물 ID를 명확한 이름으로 변경 |
| `posted_at_utc` | `raw.ig_posts.posted_at` | UTC 게시 시각 |
| `posted_date` | `posted_at` | 일 단위 분석용 날짜 |
| `caption_is_empty` | `caption` | caption 누락/공백 여부 |
| `likes_count_raw` | `likes_count` | Apify 원본 좋아요 수 |
| `likes_hidden` | `likes_count = -1` | 좋아요 수 숨김 여부 |
| `likes_count_clean` | `likes_count` | 평균/합계용 좋아요 수. 숨김이면 `NULL` |
| `is_carousel` | `post_type`, `product_type` | carousel 게시물 여부 |
| `is_video` | `post_type`, `product_type` | video/reels 게시물 여부 |
| `is_sponsored_candidate` | `caption` regex | 광고/협찬 키워드 후보 |
| `source_hashtags` | `raw.ig_post_sources` | 게시물이 발견된 seed 목록 |
| `source_hashtag_count` | `raw.ig_post_sources` | 게시물이 발견된 seed 수 |

## 3. 중요한 SQL 패턴

### 3.1 sentinel value 정리

```sql
p.likes_count as likes_count_raw,
(p.likes_count = -1) as likes_hidden,
case
    when p.likes_count = -1 then null
    else p.likes_count
end as likes_count_clean
```

의미:

- `-1`은 실제 좋아요 수가 아니다.
- raw 값은 `likes_count_raw`로 남긴다.
- 숨김 여부는 `likes_hidden`으로 분리한다.
- 분석용 숫자는 `likes_count_clean`으로 만든다.

### 3.2 후보 flag 이름 짓기

```sql
(
    coalesce(p.caption, '') ~* '(광고|협찬|제품제공|제품지원|AD|sponsored|gift)'
) as is_sponsored_candidate
```

의미:

- caption에 광고/협찬 관련 키워드가 있으면 `true`.
- 키워드 기반 규칙은 오탐 가능성이 있으므로 `is_sponsored`가 아니라 `is_sponsored_candidate`라고 부른다.

### 3.3 source lineage 합치기

```sql
array_remove(array_agg(s.source_hashtag order by s.source_hashtag), null) as source_hashtags,
count(distinct s.source_hashtag) as source_hashtag_count
```

의미:

- 한 게시물이 어떤 seed hashtag에서 발견됐는지 배열로 보존한다.
- 여러 seed에서 같은 게시물이 발견될 수 있으므로 count도 따로 둔다.

## 4. 검증 결과

실행:

```bash
docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt --select stg_ig_posts"
docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt test --profiles-dir /opt/dbt --select stg_ig_posts source:raw"
```

결과:

| check | result |
|---|---:|
| dbt model run | pass |
| dbt data tests | 15 pass |
| `staging.stg_ig_posts` row count | 49 |
| `likes_hidden` posts | 16 |
| `is_sponsored_candidate` posts | 21 |
| `caption_is_empty` posts | 2 |
| missing source rows | 0 |

source별 staging 결과:

| source_hashtags | posts | hidden_likes | sponsored_candidates |
|---|---:|---:|---:|
| `{다이소화장품}` | 30 | 12 | 17 |
| `{뷰티}` | 18 | 4 | 4 |
| `{올리브영}` | 1 | 0 | 0 |

## 5. 다음 학습 포인트

다음에는 `stg_ig_posts`를 기반으로 intermediate 모델을 설계한다.

후보:

- `int_ig_post_source_quality`: seed별 수집 품질 요약
- `int_ig_sponsored_candidates`: 광고/협찬 후보 게시물만 분리
- `int_ig_owner_activity`: 작성자별 게시물 수, 숨김 좋아요 비율, 광고 후보 비율

학습 목표:

- staging은 1:1 정제
- intermediate는 분석 목적별 재사용 가능한 계산
- marts는 비즈니스 질문에 바로 답하는 테이블
