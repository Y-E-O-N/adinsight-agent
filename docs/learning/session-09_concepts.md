# Session 09 — 학습 개념 정리 (2026-06-05)

Phase 3 dbt staging/intermediate를 시작하면서 배운 개념을 정리한다.

## 1. raw와 staging

raw:

```text
외부 API가 준 값을 최대한 그대로 보존한다.
```

staging:

```text
분석하기 좋은 컬럼 이름, clean 값, boolean flag를 만든다.
```

예:

```sql
p.likes_count as likes_count_raw,
(p.likes_count = -1) as likes_hidden,
case
    when p.likes_count = -1 then null
    else p.likes_count
end as likes_count_clean
```

의미:

- `likes_count_raw`: Apify 원본 값
- `likes_hidden`: 좋아요 수 숨김 여부
- `likes_count_clean`: 평균/합계 계산에 쓸 수 있는 좋아요 수

## 2. 왜 `is_sponsored_candidate`인가

```sql
coalesce(p.caption, '') ~* '(광고|협찬|제품제공|제품지원|AD|sponsored|gift)'
```

이 규칙은 caption 안의 키워드만 본다.

따라서 광고 확정이 아니라 광고 후보로 봐야 한다.

```text
is_sponsored        -- 너무 단정적
is_sponsored_candidate -- 더 안전한 이름
```

## 3. dbt source

`_sources.yml`은 raw 테이블을 dbt에 알려주는 파일이다.

```yaml
sources:
  - name: raw
    schema: raw
    tables:
      - name: ig_posts
```

장점:

- raw 테이블도 lineage에 포함된다.
- source table에도 `not_null`, `unique`, `relationships` 같은 data test를 걸 수 있다.
- 모델 SQL에서 `{{ source('raw', 'ig_posts') }}`로 참조한다.

## 4. dbt model

dbt 모델은 기본적으로 SQL `SELECT` 파일이다.

예:

```text
dbt/models/staging/stg_ig_posts.sql
```

dbt run을 하면 warehouse에 view/table이 생긴다.

```text
staging.stg_ig_posts
```

이번 실행 결과:

```text
dbt run --select stg_ig_posts: pass
```

## 5. dbt data tests

`schema.yml`에 컬럼별 테스트를 적는다.

```yaml
columns:
  - name: post_id
    data_tests:
      - not_null
      - unique
```

의미:

- `not_null`: 값이 비어 있으면 안 된다.
- `unique`: 중복되면 안 된다.
- `relationships`: FK처럼 다른 테이블에 대응 row가 있어야 한다.

이번 결과:

```text
전체 dbt test: 24/24 pass
```

## 6. staging과 intermediate 차이

staging:

```text
row-level 정제
게시물 1건을 분석하기 좋게 만든다.
```

intermediate:

```text
반복해서 쓸 계산 단위
seed별 품질 요약, 작성자별 활동 요약 같은 재사용 모델을 만든다.
```

이번 intermediate:

```text
intermediate.int_ig_post_source_quality
```

목적:

```text
source hashtag별 수집 품질을 비교한다.
```

## 7. `unnest()`

`stg_ig_posts.source_hashtags`는 배열이다.

```text
{다이소화장품}
{뷰티}
```

seed별 집계를 하려면 배열을 row로 펼쳐야 한다.

```sql
unnest(source_hashtags) as source_hashtag
```

이후:

```sql
group by source_hashtag
```

로 seed별 집계를 만들 수 있다.

## 8. `COUNT(*) FILTER`

조건부 count 패턴이다.

```sql
count(*) filter (where likes_hidden) as hidden_likes_posts
```

뜻:

```text
전체 row 중 likes_hidden=true인 row만 세라.
```

비율 계산:

```sql
round(
    count(*) filter (where likes_hidden)::numeric / nullif(count(*), 0),
    4
) as hidden_likes_rate
```

핵심:

- `::numeric`: 소수 나눗셈을 위해 숫자 타입 변환
- `nullif(count(*), 0)`: 0으로 나누기 방지
- `round(..., 4)`: 소수점 4자리

## 9. 현재 해석

```text
#다이소화장품
posts=30
sponsored_candidate_rate=0.5667
useful_for_sponsored_analysis=true
```

현재 데이터에서는 `#다이소화장품`만 광고/협찬 후보 분석에 쓸 만하다.

```text
#뷰티
posts=18
샘플 수 부족
```

```text
#올리브영
posts=1
분석 seed로 부적합
```

## 10. 다음 학습

다음 모델 후보:

- `int_ig_sponsored_candidates`: 광고/협찬 후보 게시물만 분리
- `int_ig_owner_activity`: 작성자별 활동/품질 요약

추천:

```text
int_ig_sponsored_candidates부터 진행
```

이유:

현재 `#다이소화장품`에서 sponsored 후보 비율이 높게 나왔기 때문에, 후보 게시물만 따로 보고 caption/owner/source를 해석하기 좋다.
