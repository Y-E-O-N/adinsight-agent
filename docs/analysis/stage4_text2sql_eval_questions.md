# Stage 4 — Text2SQL Eval Questions Draft

**Date**: 2026-06-11
**Phase**: Phase 4 — AI-Native Mart
**Primary model**: `ai_native.ai_creator_sponsored_summary`

## 1. Purpose

이 문서는 Phase 4의 첫 Text2SQL 평가 질문셋 초안이다.

목표는 LLM Agent의 최종 정확도를 지금 측정하는 것이 아니라, `ai_native` mart와 dbt `meta`가 자연어 질문을 SQL로 바꾸기에 충분한지 확인하는 것이다.

## 2. Evaluation Scope

| item | value |
|---|---|
| Target table | `ai_native.ai_creator_sponsored_summary` |
| Grain | creator 1명당 1행 |
| Required retrieval signal | `creator`, `influencer`, `작성자`, `크리에이터`, `협찬`, `광고`, `review` |
| Out of scope | raw caption inspection, post-level evidence, LLM answer generation quality |

첫 평가셋은 schema retrieval과 column selection을 본다.

- schema retrieval: 자연어 질문이 `ai_creator_sponsored_summary`를 고르는가
- column selection: 질문 의도에 맞는 컬럼을 고르는가
- SQL shape: filter, order by, limit, boolean condition을 안정적으로 만드는가

## 3. Draft Questions

| id | language | question | expected intent | required columns |
|---|---|---|---|---|
| `p4_q001` | en | Which creators should we review first for sponsored content? | review 대상 creator를 협찬 후보 수와 비율 기준으로 정렬 | `creator_username`, `sponsored_candidate_posts`, `sponsored_candidate_rate`, `included_in_creator_review` |
| `p4_q002` | en | Show creators with at least one sponsored candidate post. | 협찬 후보 게시물이 1개 이상인 creator 필터 | `creator_username`, `sponsored_candidate_posts` |
| `p4_q003` | en | Which influencers have a high sponsored candidate rate? | 협찬 후보 비율 상위 creator 정렬 | `creator_username`, `sponsored_candidate_rate`, `total_posts` |
| `p4_q004` | ko | 협찬 후보 게시물이 있는 크리에이터를 보여줘. | 한국어 `협찬`, `크리에이터` 표현으로 동일 테이블 검색 | `creator_username`, `sponsored_candidate_posts` |
| `p4_q005` | ko | 광고 의심 비율이 높은 작성자는 누구야? | 한국어 `광고 의심 비율`, `작성자` 표현으로 rate 컬럼 선택 | `creator_username`, `sponsored_candidate_rate` |
| `p4_q006` | ko | 우선 검토 대상 크리에이터만 보여줘. | boolean review flag 필터 | `creator_username`, `included_in_creator_review` |
| `p4_q007` | en | List creators where likes are often hidden. | likes hidden rate 기준 정렬 | `creator_username`, `hidden_likes_rate`, `hidden_likes_posts` |
| `p4_q008` | ko | 평균 댓글 수가 높은 인플루언서 Top 10을 보여줘. | 평균 댓글 기준 Top N 정렬 | `creator_username`, `avg_comments_count` |
| `p4_q009` | en | Which creators have engagement signals available? | engagement signal boolean 필터 | `creator_username`, `has_engagement_signal` |
| `p4_q010` | ko | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. | 복합 조건 필터 | `creator_username`, `total_posts`, `sponsored_candidate_posts` |

## 4. Expected SQL Patterns

대표 패턴은 아래와 같다.

```sql
select
    creator_username,
    sponsored_candidate_posts,
    sponsored_candidate_rate,
    included_in_creator_review
from ai_native.ai_creator_sponsored_summary
where included_in_creator_review = true
order by sponsored_candidate_posts desc, sponsored_candidate_rate desc
limit 20;
```

```sql
select
    creator_username,
    sponsored_candidate_rate
from ai_native.ai_creator_sponsored_summary
where sponsored_candidate_posts >= 1
order by sponsored_candidate_rate desc
limit 10;
```

```sql
select
    creator_username,
    total_posts,
    sponsored_candidate_posts
from ai_native.ai_creator_sponsored_summary
where total_posts >= 2
  and sponsored_candidate_posts = 0
order by sponsored_candidate_posts desc, total_posts desc;
```

## 5. Pass Criteria

초기 수동 평가 기준은 아래와 같다.

| criterion | pass condition |
|---|---|
| Table selection | `ai_native.ai_creator_sponsored_summary`를 선택한다. |
| Grain awareness | creator-level 질문에 post-level table을 만들거나 join하지 않는다. |
| Column selection | 질문의 핵심 지표와 관련된 컬럼을 포함한다. |
| Boolean handling | `included_in_creator_review`, `has_engagement_signal` 조건을 boolean으로 처리한다. |
| Ordering | `높은`, `top`, `first`, `우선` 표현에 `order by`를 사용한다. |
| Limit handling | Top N 질문에 `limit`를 사용한다. |

## 6. Current Row Counts

2026-06-11 현재 `ai_native.ai_creator_sponsored_summary` 기준 expected SQL 실행 결과는 아래와 같다.

| id | current row count |
|---|---:|
| `p4_q001` | 20 |
| `p4_q002` | 21 |
| `p4_q003` | 10 |
| `p4_q004` | 21 |
| `p4_q005` | 10 |
| `p4_q006` | 24 |
| `p4_q007` | 10 |
| `p4_q008` | 10 |
| `p4_q009` | 44 |
| `p4_q010` | 3 |

## 7. Next Step

다음 단계는 `agent/eval/text2sql_questions.yml`을 실제 evaluator가 읽을 수 있는 포맷으로 확정하고, 각 질문의 expected SQL을 실행해 결과 row count를 저장하는 것이다.

현재 Round 1 데이터 분포상 `total_posts >= 2`이면서 `sponsored_candidate_posts >= 1`인 creator는 0건이다. 그래서 복합 조건 질문은 결과가 있는 `total_posts >= 2 and sponsored_candidate_posts = 0` 케이스로 시작한다.
