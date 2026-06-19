# Stage 3 Intermediate Model — `int_ig_sponsored_candidates`

**Date**: 2026-06-06
**Model**: `intermediate.int_ig_sponsored_candidates`
**dbt file**: `dbt/models/intermediate/int_ig_sponsored_candidates.sql`

## 1. 목적

`int_ig_sponsored_candidates`는 caption 키워드 기준 광고/협찬 후보 게시물만 분리한다.

`stg_ig_posts`가 raw Instagram 게시물을 분석 가능한 row로 정리한다면, 이 모델은 그중 광고/협찬 분석에 쓸 후보 row만 남긴다. 후속 mart에서는 이 모델을 입력으로 사용해 협찬 유형별 성과, 작성자별 협찬 후보 활동, seed별 광고 후보 분포를 계산할 수 있다.

이번 모델은 아래 질문에 답한다.

- 광고/협찬 후보 게시물은 몇 건인가?
- 후보 게시물은 어떤 키워드 그룹으로 나뉘는가?
- 후보 게시물 중 좋아요 또는 댓글 기반 engagement signal이 있는 게시물은 몇 건인가?
- 후속 creator mart에 넘길 수 있는 게시물 단위 후보 데이터는 무엇인가?

## 2. 핵심 SQL 패턴

### 2.1 후보 row만 필터링

```sql
where is_sponsored_candidate
```

`is_sponsored_candidate`는 staging 모델에서 만든 boolean flag다.

이 값은 실제 광고 여부를 확정하는 라벨이 아니라, caption 키워드 기반 후보값이다. 그래서 모델명도 `sponsored` 확정 모델이 아니라 `sponsored_candidates`로 둔다.

### 2.2 engagement count

```sql
coalesce(likes_count_clean, 0) + coalesce(comments_count, 0) as engagement_count
```

좋아요 수가 숨겨진 게시물은 `likes_count_clean`이 `null`이다. `coalesce(..., 0)`을 사용해 `null + comments_count`가 전체 `null`로 번지는 것을 막는다.

이 값은 정교한 engagement rate가 아니라, 후보 게시물 비교를 위한 단순 count다.

### 2.3 engagement signal 여부

```sql
(
    likes_count_clean is not NULL
    or coalesce(comments_count, 0) > 0
) as has_engagement_signal
```

좋아요 수가 보이거나 댓글 수가 1개 이상이면 분석 가능한 engagement signal이 있다고 본다.

### 2.4 키워드 그룹 분류

```sql
case
    when coalesce(caption, '') ~* '(제품제공|제품지원|gift)' then 'product_provided'
    when coalesce(caption, '') ~* '(광고|협찬|AD|sponsored)' then 'ad_disclosure'
    else 'other_keyword'
end as sponsored_keyword_group
```

`~*`는 PostgreSQL의 대소문자 무시 정규식 매칭 연산자다.

현재 그룹은 두 갈래다.

| group | 의미 |
|---|---|
| `product_provided` | 제품 제공, 제품 지원, gift 계열 후보 |
| `ad_disclosure` | 광고, 협찬, AD, sponsored 계열 후보 |

`other_keyword`는 staging의 후보 규칙이 더 넓어질 때를 대비해 허용값에 포함했다.

## 3. 현재 결과

Round 1 데이터 기준:

| metric | value |
|---|---:|
| sponsored candidate posts | 21 |
| posts with engagement signal | 19 |
| avg engagement count | 64.29 |

키워드 그룹별 결과:

| sponsored_keyword_group | posts | with_engagement_signal | avg_engagement_count |
|---|---:|---:|---:|
| `product_provided` | 13 | 13 | 77.62 |
| `ad_disclosure` | 8 | 6 | 42.63 |

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

AWS managed 환경으로 대응하면 Redshift 또는 Athena 위에 dbt가 만든 curated intermediate view에 가깝다. Glue Data Catalog가 테이블 메타데이터를 관리하고, IAM이 접근 권한을 제어하며, Airflow 또는 MWAA가 dbt 실행을 오케스트레이션할 수 있다.

현재 로컬 환경은 단일 Postgres 컨테이너라 비용과 권한 경계가 단순하지만, AWS 환경에서는 쿼리 비용, 역할별 접근 제어, lineage/catalog 운영이 별도 설계 대상이다.

## 5. Known Limitations

- 후보 판단은 caption 키워드 기반이라 오탐과 미탐이 모두 가능하다.
- Round 1 데이터가 49건이고 후보는 21건이라 비율과 평균 engagement는 대표성이 낮다.
- 좋아요 숨김 게시물은 `engagement_count`에서 좋아요를 0으로 계산하므로 실제 반응보다 낮게 보일 수 있다.
- 현재는 한국어/영어 일부 키워드만 사용하며, 해시태그·이미지·댓글 기반 광고 판단은 포함하지 않는다.

## 6. 다음 학습 포인트

- `int_ig_sponsored_candidates`와 `int_ig_owner_activity`를 조합해 creator-level ranking mart를 설계한다.
- 광고 후보 규칙을 dbt seed나 macro로 분리할지 판단한다.
- 데이터가 늘어난 뒤 keyword group별 precision을 수동 샘플링으로 검증한다.
