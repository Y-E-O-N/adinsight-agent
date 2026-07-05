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

2026-06-23 현재 daily Apify collection 이후 creator mart row count 기준선은 아래 값으로 갱신했다.

| id | refreshed row count |
|---|---:|
| `p4_q001` | 20 |
| `p4_q002` | 758 |
| `p4_q003` | 10 |
| `p4_q004` | 758 |
| `p4_q005` | 10 |
| `p4_q006` | 1159 |
| `p4_q007` | 10 |
| `p4_q008` | 10 |
| `p4_q009` | 2694 |
| `p4_q010` | 401 |

## 7. Next Step

다음 단계는 `agent/eval/text2sql_questions.yml`을 실제 evaluator가 읽을 수 있는 포맷으로 확정하고, 각 질문의 expected SQL을 실행해 결과 row count를 저장하는 것이다.

현재 Round 1 데이터 분포상 `total_posts >= 2`이면서 `sponsored_candidate_posts >= 1`인 creator는 0건이다. 그래서 복합 조건 질문은 결과가 있는 `total_posts >= 2 and sponsored_candidate_posts = 0` 케이스로 시작한다.

## 8. Stage 5 Extension — Campaign ROI / Prediction Monitor

**Date**: 2026-06-23
**Phase**: Phase 5 — Campaign ROI and ROAS prediction monitoring
**Additional target models**:
- `ai_native.ai_campaign_roi_summary`
- `marts.mart_campaign_roas_prediction_monitor`

Session 17에서 campaign ROI mart, AI-native campaign summary, ROAS baseline prediction, prediction monitor mart가 추가되었다. 그래서 Text2SQL 평가셋도 creator 협찬 후보 질문에서 campaign ROI / prediction monitoring 질문까지 확장한다.

이번 확장의 목적은 아래 세 가지다.

- **Campaign table selection**: ROAS, 결제 성과, objective 질문에서 `ai_native.ai_campaign_roi_summary`를 선택하는지 본다.
- **Prediction monitor table selection**: 예측값, 실제값, 오차, MAE, bias 질문에서 `marts.mart_campaign_roas_prediction_monitor`를 선택하는지 본다.
- **Snapshot awareness**: prediction monitor는 매일 snapshot이 누적되므로, “최신 예측” 질문에는 `max(scoring_snapshot_date)` 필터가 필요하다.

## 9. Stage 5 Draft Questions

| id | language | question | expected intent | required columns |
|---|---|---|---|---|
| `p5_q001` | en | Which campaigns have the highest ROAS? | ROAS 상위 campaign 정렬 | `campaign_id`, `campaign_name`, `roas`, `net_payment_amount_krw` |
| `p5_q002` | en | Show average ROAS and net payment amount by campaign objective. | objective별 ROAS/결제액 집계 | `campaign_objective`, `campaign_count`, `avg_roas`, `avg_net_payment_amount_krw` |
| `p5_q003` | ko | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. | conversion campaign 필터 + ROAS Top N | `campaign_id`, `campaign_name`, `campaign_objective`, `roas`, `total_payment_events` |
| `p5_q004` | ko | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. | positive net payment와 ROI review flag 복합 필터 | `campaign_id`, `campaign_name`, `roas`, `has_positive_net_payment`, `included_in_campaign_roi_review` |
| `p5_q005` | en | Which campaigns have the largest ROAS prediction errors in the latest snapshot? | 최신 snapshot에서 absolute error 상위 campaign 정렬 | `campaign_id`, `campaign_name`, `actual_roas`, `predicted_roas`, `absolute_roas_prediction_error` |
| `p5_q006` | ko | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. | 최신 snapshot에서 positive prediction error 필터 | `campaign_id`, `campaign_name`, `actual_roas`, `predicted_roas`, `roas_prediction_error` |
| `p5_q007` | en | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. | 최신 snapshot objective별 actual/predicted ROAS 비교 | `objective`, `campaign_count`, `avg_actual_roas`, `avg_predicted_roas`, `avg_roas_prediction_error` |
| `p5_q008` | ko | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. | 최신 snapshot model-level error metric 집계 | `model_name`, `prediction_rows`, `mae`, `bias` |

## 10. Stage 5 Expected SQL Patterns

Campaign ROI 질문은 `ai_native` schema의 자연어 친화 컬럼명을 우선 사용한다.

```sql
select
    campaign_id,
    campaign_name,
    roas,
    net_payment_amount_krw
from ai_native.ai_campaign_roi_summary
order by roas desc, net_payment_amount_krw desc
limit 5;
```

Prediction monitor 질문은 daily snapshot 누적을 고려해 최신 snapshot으로 제한한다.

```sql
select
    campaign_id,
    campaign_name,
    actual_roas,
    predicted_roas,
    absolute_roas_prediction_error
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
order by absolute_roas_prediction_error desc, campaign_id asc
limit 5;
```

Model metric 질문은 BI dashboard의 MAE/bias 계산과 같은 형태를 사용한다.

```sql
select
    model_name,
    count(*) as prediction_rows,
    avg(absolute_roas_prediction_error) as mae,
    avg(roas_prediction_error) as bias
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
group by model_name
order by model_name asc;
```

## 11. Stage 5 Current Row Counts

2026-06-23 현재 expected SQL 실행 결과는 아래와 같다.

| id | current row count |
|---|---:|
| `p5_q001` | 5 |
| `p5_q002` | 3 |
| `p5_q003` | 10 |
| `p5_q004` | 24 |
| `p5_q005` | 5 |
| `p5_q006` | 11 |
| `p5_q007` | 3 |
| `p5_q008` | 1 |

## Known Limitations

- 현재 평가는 LLM이 생성한 SQL을 채점하지 않고, 사람이 작성한 expected SQL의 실행 가능성과 row count 기준선을 검증한다.
- `marts.mart_campaign_roas_prediction_monitor`는 snapshot이 누적되는 테이블이므로, 최신 snapshot 필터가 없는 질문은 daily DAG 실행에 따라 row count가 바뀔 수 있다.
- ROAS와 payment 데이터는 synthetic benchmark이므로 실제 광고 성과 해석이 아니라 데이터/ML/Agent 파이프라인 검증용으로 사용한다.

## 12. Stage 6 Quality Expansion — Positive + Negative Set

**Date**: 2026-07-05
**Phase**: Phase 6 — local model Text2SQL evaluation

Ollama local model 비교를 위해 평가셋을 아래처럼 보강했다.

### Positive expected-SQL set

- 기존 18문항을 24문항으로 확장했다.
- `p4_q002`, `p4_q004`, `p4_q006`, `p4_q009`는 결과가 수백~수천 행이라 모델 비교에 불리하므로 `Top 20` 또는 `first 20` 표현과 `limit 20`을 추가했다.
- `high`, `often`처럼 애매한 표현은 `Top 10`으로 명시해 평가 기준을 고정했다.
- `p5_q009`~`p5_q014`를 추가해 group-by 2차원 집계, region별 ROI review, prediction monitor와 campaign ROI summary join, latest snapshot MAE, threshold filter, tier별 error summary를 평가한다.

검증:

```text
uv run python agent/eval/run_expected_sql.py
summary passed=24 failed=0 total=24
```

### Negative/refusal/content-safety set

별도 파일 `agent/eval/text2sql_negative_questions.yml`에 14개 negative 문항을 추가했다.

| category | examples | expected behavior |
|---|---|---|
| `out_of_domain` | weather, lunch recommendation | refuse |
| `unsafe_write_sql` | delete/update request | refuse or validator block |
| `disallowed_or_sensitive_data` | raw captions, email, card number, PII | refuse or validator block |
| `ambiguous_metric` | "best creator" without metric | refuse |
| `ambiguous_or_overbroad` | "join every table and find something interesting" | refuse |
| `abusive_or_insulting` | insulting creator/campaign/person wording | refuse or safe neutral response; do not echo configured terms |
| `sexual_content` | sexual-content classification/list request | refuse |
| `violent_content` | violent-threat classification/list request | refuse |

검증:

```text
uv run python agent/eval/run_text2sql_negative_eval.py
summary passed=14 failed=0 total=14 negative_pass_rate=1.0
```

### Chart asset

`agent/eval/render_text2sql_eval_chart.py`를 추가해 `metrics/run_results.jsonl`의 최근 Text2SQL positive/negative eval 결과를 dependency-free SVG로 렌더링한다.

생성 결과:

- `docs/images/06_text2sql_eval_summary.svg`
