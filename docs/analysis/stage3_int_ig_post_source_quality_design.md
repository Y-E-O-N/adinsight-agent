# Stage 3 Intermediate Model — `int_ig_post_source_quality`

**Date**: 2026-06-05
**Model**: `intermediate.int_ig_post_source_quality`
**dbt file**: `dbt/models/intermediate/int_ig_post_source_quality.sql`

## 1. 목적

`int_ig_post_source_quality`는 seed hashtag별 수집 품질을 요약한다.

staging 모델이 "게시물 1건을 분석하기 좋게 정리"하는 단계라면, intermediate 모델은 "반복해서 쓸 계산 단위"를 만든다.

이번 모델은 아래 질문에 답한다.

- 어떤 seed가 충분한 게시물을 반환했는가?
- 좋아요 숨김 비율이 높은 seed는 무엇인가?
- 광고/협찬 후보 비율이 높은 seed는 무엇인가?
- 후속 분석이나 추가 수집에서 어떤 seed를 우선 볼 것인가?

## 2. 핵심 SQL 패턴

### 2.1 배열을 row로 펼치기

```sql
unnest(source_hashtags) as source_hashtag
```

`stg_ig_posts.source_hashtags`는 배열이다. 한 게시물이 여러 source에서 발견될 수 있으므로, seed별 집계를 하려면 배열을 row로 펼친다.

예:

```text
post_id | source_hashtags
A       | {뷰티, 다이소화장품}
```

`unnest` 후:

```text
post_id | source_hashtag
A       | 뷰티
A       | 다이소화장품
```

### 2.2 조건부 count

```sql
count(*) filter (where likes_hidden) as hidden_likes_posts
```

전체 row 중 `likes_hidden = true`인 row만 센다.

### 2.3 비율 계산

```sql
round(
    count(*) filter (where likes_hidden)::numeric / nullif(count(*), 0),
    4
) as hidden_likes_rate
```

구성:

- `count(*) filter (...)`: 조건에 맞는 row 수
- `count(*)`: 전체 row 수
- `::numeric`: 정수 나눗셈을 피하기 위한 타입 변환
- `nullif(count(*), 0)`: 0으로 나누는 오류 방지
- `round(..., 4)`: 소수점 4자리까지 정리

## 3. 판단 컬럼

| column | rule | 의미 |
|---|---|---|
| `has_minimum_sample` | `posts >= 20` | 최소 샘플 수를 만족하는 seed |
| `useful_for_sponsored_analysis` | `posts >= 20` and `sponsored_candidate_rate >= 0.3` | 광고/협찬 후보 분석에 쓸 만한 seed |

현재 기준은 학습용 1차 기준이다. 데이터가 늘어나면 `posts >= 100`처럼 기준을 올릴 수 있다.

## 4. 다음 학습 포인트

이 모델을 통해 배울 내용:

- staging과 intermediate의 역할 차이
- `unnest()`로 배열을 분석 단위 row로 펼치는 방법
- `COUNT(*) FILTER`로 조건부 집계를 만드는 방법
- count를 비율로 바꿀 때 `::numeric`, `nullif`, `round`를 쓰는 이유
