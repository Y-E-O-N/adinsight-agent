# Text2SQL Positive Criteria Rulebook

**Date**: 2026-07-09
**Phase**: Phase 6 — Text2SQL v2 provider tuning
**Purpose**: LLM Text2SQL generation 전에 반드시 참고할 positive evaluation 기준서.

이 문서는 `agent/eval/text2sql_questions.yml`의 positive 질문 24개가 어떤 비즈니스 의미와 SQL 조건을 가져야 하는지 한 곳에 모은 rule book이다.

## How to Use

- LLM SQL 생성 전 이 문서의 기준을 우선 적용한다.
- 실제 SQL의 source of truth는 dbt 모델과 `agent/eval/text2sql_questions.yml`이다.
- 여기의 기준은 real business KPI 확정안이 아니라 AdInsight portfolio benchmark 기준이다.
- ROAS/payment 데이터는 synthetic benchmark이므로 실제 광고 성과 주장에 사용하지 않는다.

## Source of Truth

| Area | Source |
|---|---|
| Positive eval questions | `agent/eval/text2sql_questions.yml` |
| Creator sponsored rules | `dbt/models/staging/stg_ig_posts.sql`, `dbt/models/intermediate/int_ig_owner_activity.sql`, `dbt/models/marts/creator/mart_creator_sponsored_summary.sql` |
| Campaign ROI rules | `dbt/models/intermediate/int_campaign_payment_performance.sql`, `dbt/models/marts/campaign/mart_campaign_roi_summary.sql` |
| Prediction monitor rules | `dbt/models/marts/campaign/mart_campaign_roas_prediction_monitor.sql` |
| Synthetic generation policy | `data_generation/generators/generation_profile.py` |

## Global SQL Rules

| Rule | Required Behavior |
|---|---|
| Allowed tables | Use only tables in the schema context. |
| Creator questions | Prefer `ai_native.ai_creator_sponsored_summary`. |
| Campaign ROI questions | Prefer `ai_native.ai_campaign_roi_summary`. |
| Prediction error / MAE / bias questions | Prefer `marts.mart_campaign_roas_prediction_monitor`. |
| Latest snapshot | Always filter `scoring_snapshot_date = (select max(scoring_snapshot_date) from marts.mart_campaign_roas_prediction_monitor)`. |
| List queries | Use deterministic `order by` and explicit `limit`. |
| Aggregates | Use clear aliases such as `campaign_count`, `avg_roas`, `mae`, `bias`. |
| Expected output columns | If a question mapping or intent defines expected output columns, include every expected column explicitly in `select`, even if the same column is used in `where`, `group by`, or `order by`. |
| Extra output columns | Product answers may include useful extra columns, but benchmark strict comparison only requires the expected column subset. Extra columns must not change the required row order or substitute for expected aliases. |
| Ambiguous words | Resolve `high` / `often` by the Top N or threshold explicitly stated in the question. |

## Missing-Condition and Metric Availability Rules

| Situation | Rule |
|---|---|
| Ranking question without period | For creator/campaign summary questions, default to the full collected dataset and disclose that default in the answer. |
| Prediction monitor question without period | Use latest snapshot: `scoring_snapshot_date = max(scoring_snapshot_date)`. |
| Ranking question without Top N | Default to Top 10 and disclose that default. |
| Views / impressions / clicks requested | These metrics are not available in the allowed Text2SQL schema. Do not fabricate them. Refuse exact SQL and suggest likes/comments engagement or supported ROI/payment metrics. |
| Metric substitution | Do not silently substitute. Use substitute metrics only when the user asks for them or accepts them. |
| Period requested but selected allowed table has no date column | Do not invent a period filter. Return `not_answerable` or ask for a supported model/metric. |
| Natural-language answer after default use | Mention the metric definition, default period, ranking limit, and any substitution. |

## User Question Criteria

이 섹션은 사용자가 실제로 의문을 제기한 항목을 답변형 기준으로 고정한 것이다. LLM이 같은 표현을 만나면 아래 정의를 우선 적용한다.

| No. | Topic | Definition |
|---:|---|---|
| 1 | `we review first` 조건 | `included_in_creator_review = true`인 creator만 본다. 정렬은 `sponsored_candidate_posts desc, sponsored_candidate_rate desc`, 결과는 Top 20이다. `included_in_creator_review` 자체는 `posts >= 2 or sponsored_candidate_posts >= 1`이다. |
| 2 | `sponsored candidate post` 조건 | caption에 `(광고|협찬|제품제공|제품지원|AD|sponsored|gift)` 중 하나가 포함되면 `is_sponsored_candidate = true`이다. 확정 광고가 아니라 후보 판정이다. |
| 3 | `sponsored candidate rate` 조건 | creator별 `sponsored_candidate_posts / total_posts`이다. 소수 4자리로 round한다. |
| 4 | 광고 의심 콘텐츠 및 광고 의심 비율 조건 | 광고 의심 콘텐츠는 sponsored candidate와 같은 기준이다. 광고 의심 비율은 `sponsored_candidate_rate`이고, 질문에서는 Top 10으로 고정한다. |
| 5 | 우선 검토 대상 조건 | creator 기준은 `posts >= 2 or sponsored_candidate_posts >= 1`이다. 질문에서는 그중 상위 20명을 `sponsored_candidate_posts desc` 중심으로 정렬한다. |
| 6 | `likes are often hidden`의 `often` | 고정 임계값은 없다. 현재 평가셋에서는 모호성을 없애기 위해 `hidden_likes_rate desc, hidden_likes_posts desc` 기준 Top 10으로 정의한다. |
| 7 | 평균 댓글 수 산정 방식 | creator별 `avg(comments_count)`이다. hidden likes와 무관하게 comments count 평균만 본다. |
| 8 | `engagement signals available` 의미 | creator의 평균 likes가 null이 아니거나 평균 댓글 수가 0보다 크면 true이다. post-level에서는 likes가 존재하거나 댓글 수가 0보다 크면 engagement signal이 있다고 본다. |
| 9 | 협찬 후보가 없는 계정 기준 | `total_posts >= 2 and sponsored_candidate_posts = 0`이다. |
| 10 | ROAS 산정 방식 | campaign별 `net_payment_amount_krw / campaign_budget_krw`이다. 분모 0 방지를 위해 `nullif(campaign_budget_krw, 0)`를 쓴다. |
| 11 | net payment amount by campaign objective 기준 | campaign objective별로 `count(*)`, `avg(roas)`, `avg(net_payment_amount_krw)`를 계산한다. net payment는 campaign에 속한 payment event의 `net_payment_amount_krw` 합계이고, 환불은 음수로 반영된다. |
| 12 | 전환 목적 캠페인 기준 | `campaign_objective = 'conversion'`이다. 현재 objective 값은 synthetic campaign generator에서 `conversion`, `traffic`, `awareness` 중 샘플링된다. |
| 13 | 순결제액 여부, ROI 검토 대상 기준 | 순결제액 있음은 `net_payment_amount_krw > 0`이다. ROI 검토 대상 campaign은 `attributed_posts >= 5 or payment_events >= 1`이다. 질문은 두 조건을 모두 만족하는 campaign을 본다. |
| 14 | ROAS prediction error 판단 기준 | `roas_prediction_error = actual_roas - predicted_roas`이다. 양수면 실제 ROAS가 예측보다 높고, 음수면 실제가 예측보다 낮다. 큰 오차 순위는 `abs(actual_roas - predicted_roas)`를 쓴다. |
| 15 | 최신 예측의 기간 범위 | 기간 범위가 아니라 `scoring_snapshot_date = max(scoring_snapshot_date)`인 가장 최근 snapshot 날짜 1개이다. |
| 16 | average actual ROAS 기간 범위 / latest prediction snapshot 시점 | `avg(actual_roas)`와 `avg(predicted_roas)`는 최신 snapshot 날짜 1개 안에서 objective별 평균을 낸다. 별도 campaign start/end 기간 필터는 없다. |
| 17 | 최신 ROAS 예측 모델, 기간 범위, MAE, bias | Text2SQL monitor 질문에서 최신 모델은 최신 snapshot에 들어있는 `model_name`별 집계이다. daily monitor는 `objective_mean_roas_baseline_v1` 기반이고, FastAPI serving artifact의 best model은 `linear_regression_numpy_v1`이므로 둘을 구분한다. MAE는 `avg(abs(actual_roas - predicted_roas))`, bias는 monitor SQL 기준 `avg(actual_roas - predicted_roas)`이다. |
| 18 | campaign 수, ROAS performance tier, objective 선정 방식 | campaign 수는 현재 group/filter의 `count(*)`이다. ROAS performance tier는 `no_payment`, `negative_net`, `under_1x`, `one_to_two_x`, `two_x_plus`이다. objective는 synthetic generator에서 `conversion`, `traffic`, `awareness` 중 확률 샘플링된다. |
| 19 | 지역 나누는 기준 | 현재 region은 synthetic campaign의 `KR`, `JP` 두 값이다. 생성 확률은 `KR 0.7`, `JP 0.3`이고 payment currency는 `KR -> KRW`, `JP -> JPY`로 매핑된다. |
| 20 | `latest` 기준 | `latest`는 현재 실행 날짜가 아니라 monitor table 안의 `max(scoring_snapshot_date)`이다. |
| 21 | MAE 계산 기준 | monitor 질문에서는 최신 snapshot에서 `avg(absolute_roas_prediction_error)`이다. 모델 비교 스크립트에서는 leave-one-out 예측 결과 기준으로 `mean(abs(actual - predicted))`를 계산한다. |
| 22 | campaign ROI tier, absolute error, `0.05` 기준 | campaign ROI tier는 ROAS performance tier이다. absolute error는 과대예측/과소예측 방향과 무관하게 얼마나 크게 틀렸는지 보기 위해 쓴다. `0.05`는 positive eval의 threshold filter 테스트용 고정 기준이며, production SLA가 아니다. 운영 기준은 나중에 error 분포의 p75/p90 또는 alert 정책으로 재설정한다. |

## Creator Sponsored Review Rules

| Concept | Rule |
|---|---|
| Sponsored candidate post | A post is a sponsored candidate when caption matches `(광고|협찬|제품제공|제품지원|AD|sponsored|gift)`. This is only a candidate flag, not final ad proof. |
| Sponsored keyword group | `제품제공|제품지원|gift` -> `product_provided`; `광고|협찬|AD|sponsored` -> `ad_disclosure`; otherwise `other_keyword`. |
| Sponsored candidate posts | Creator-level count of posts where `is_sponsored_candidate = true`. |
| Sponsored candidate rate | `sponsored_candidate_posts / total_posts`, rounded to 4 decimal places. |
| Advertising suspicious content | Same benchmark meaning as sponsored candidate content. |
| Advertising suspicious rate | Same benchmark metric as `sponsored_candidate_rate`. |
| Creator review target | `posts >= 2 or sponsored_candidate_posts >= 1`. |
| Hidden likes post | `likes_count_raw = -1`; clean likes count becomes `null`. |
| Hidden likes rate | `hidden_likes_posts / total_posts`, rounded to 4 decimal places. |
| Likes are often hidden | No fixed business threshold. In positive eval, rank by `hidden_likes_rate desc, hidden_likes_posts desc` and limit 10. |
| Average comments | `avg(comments_count)` by creator. |
| Engagement signal | Creator has engagement signal when `avg(likes_count_clean) is not null or avg(comments_count) > 0`. |
| No sponsored candidate account | `total_posts >= 2 and sponsored_candidate_posts = 0`. |

## Campaign ROI Rules

| Concept | Rule |
|---|---|
| Campaign grain | One row per `campaign_id`. |
| ROAS | `net_payment_amount_krw / campaign_budget_krw`. |
| Gross payment amount | Sum of `payment_amount_krw` by campaign. |
| Net payment amount | Sum of `net_payment_amount_krw` by campaign. Refund events are negative in net payment. |
| Has positive net payment | `net_payment_amount_krw > 0`. |
| ROI review target | `attributed_posts >= 5 or payment_events >= 1`. |
| Conversion campaign | `campaign_objective = 'conversion'`. |
| Campaign objective values | `conversion`, `traffic`, `awareness`. Current synthetic probabilities are `0.60`, `0.25`, `0.15`. |
| Campaign region values | `KR`, `JP`. Current synthetic probabilities are `0.70`, `0.30`. |
| Region currency | `KR -> KRW`, `JP -> JPY` with JPY converted to KRW in payment outputs. |
| Campaign count | `count(*)` for the current group or filter. |
| ROAS performance tier | `payment_events = 0` -> `no_payment`; `net_payment_amount_krw < 0` -> `negative_net`; `roas < 1.0` -> `under_1x`; `roas < 2.0` -> `one_to_two_x`; otherwise `two_x_plus`. |

## Prediction Monitor Rules

| Concept | Rule |
|---|---|
| Latest | Latest means `max(scoring_snapshot_date)` in `marts.mart_campaign_roas_prediction_monitor`, not current wall-clock date. |
| Latest prediction period | A single latest scoring snapshot date. There is no campaign start/end date filter unless the question explicitly asks for one. |
| Actual ROAS | `campaign_roi.roas` joined into the monitor mart. |
| Predicted ROAS | `predictions.predicted_roas` from `features.campaign_roas_baseline_predictions`. |
| ROAS prediction error | `actual_roas - predicted_roas`. Positive means actual ROAS was higher than predicted. |
| Absolute ROAS prediction error | `abs(actual_roas - predicted_roas)`. Use this for largest-error rankings because direction does not matter for magnitude. |
| MAE | `avg(absolute_roas_prediction_error)`. |
| Bias | In monitor SQL, use `avg(roas_prediction_error)`. Positive bias means actual is above predicted on average. |
| Model-level summary | Group latest snapshot rows by `model_name`, then compute row count, MAE, and bias. |
| Objective-level prediction summary | Group latest snapshot rows by `objective`. |
| ROI-tier prediction summary | Join monitor to `ai_native.ai_campaign_roi_summary` on `campaign_id`, group by `roas_performance_tier`, compute count, MAE, and bias. |
| Error threshold 0.05 | Benchmark threshold for positive eval question `p5_q013`; not a production SLA. |

## Extended Metric Catalog

이 섹션은 positive 질문에 직접 등장하지 않더라도 현재 코드에서 정의 가능한 식, 개념, 조건, 산정 방식, 선정 방법을 모두 모은다.

### Instagram Post Staging

| Concept | Definition |
|---|---|
| `posted_date` | `posted_at`을 UTC 기준 date로 변환한다. |
| `caption_is_empty` | caption이 null이거나 trim 후 빈 문자열이면 true이다. |
| `caption_hashtag_count` | caption 안의 `#[영문/숫자/한글/_]` 패턴 개수이다. |
| `mention_count` | caption 안의 `@username` 패턴 개수이다. |
| `likes_count_raw` | Apify 원본 likes count이다. `-1`은 likes hidden sentinel value이다. |
| `likes_hidden` | `likes_count_raw = -1`이면 true이다. |
| `likes_count_clean` | likes hidden이면 null, 아니면 원본 likes count이다. |
| `is_carousel` | `post_type = 'Sidecar'` 또는 `product_type = 'carousel_container'`이면 true이다. |
| `is_video` | `post_type = 'Video'` 또는 `product_type = 'clips'`이면 true이다. |
| `source_hashtags` | 해당 post가 발견된 source hashtag 배열이다. |
| `source_hashtag_count` | distinct source hashtag 수이다. |

### Source Hashtag Quality

| Concept | Definition |
|---|---|
| `posts` | source hashtag별 post row 수이다. |
| `distinct_posts` | source hashtag별 distinct post 수이다. |
| `distinct_owners` | source hashtag별 distinct creator 수이다. |
| `empty_caption_posts` | `caption_is_empty = true`인 post 수이다. |
| `hidden_likes_posts` | `likes_hidden = true`인 post 수이다. |
| `sponsored_candidate_posts` | `is_sponsored_candidate = true`인 post 수이다. |
| `empty_caption_rate` | `empty_caption_posts / posts`, 소수 4자리 round이다. |
| `hidden_likes_rate` | `hidden_likes_posts / posts`, 소수 4자리 round이다. |
| `sponsored_candidate_rate` | `sponsored_candidate_posts / posts`, 소수 4자리 round이다. |
| `avg_likes_count_clean` | hidden likes를 제외한 평균 likes이다. |
| `avg_comments_count` | 평균 comments count이다. |
| `has_minimum_sample` | `posts >= 20`이다. |
| `useful_for_sponsored_analysis` | `posts >= 20 and sponsored_candidate_rate >= 0.3`이다. |

### Post-Campaign Attribution

| Concept | Definition |
|---|---|
| category inference | source hashtag mapping으로 category를 추정한다. mapping에 없으면 `beauty`를 기본값으로 둔다. |
| attribution likes clean | raw likes가 `-1`이면 0으로 보정한다. |
| attribution comments count | null이면 0, 음수 방지 후 정수로 보정한다. |
| `observed_engagement_count` | `likes_count_clean + comments_count`이다. |
| `observed_engagement_tier` | Apify profile의 engagement_count percentile 기준 `low`, `medium`, `high`, `viral`로 분류한다. |
| `is_high_engagement_observed` | tier가 `high` 또는 `viral`이면 true이다. |
| `is_viral_engagement_observed` | tier가 `viral`이면 true이다. |
| campaign selection | 같은 category campaign 중 random choice한다. 같은 category가 없으면 전체 campaign 중 choice한다. |
| `metric_policy` | `observed_likes_comments_only_v1`; views, impressions, clicks는 현재 사용하지 않는다. |

### Synthetic Campaign Generation

| Concept | Definition |
|---|---|
| `region` | `KR`, `JP` 중 샘플링한다. 확률은 `0.70`, `0.30`이다. |
| `category` | `beauty`, `fashion`, `food` 중 샘플링한다. 확률은 `0.50`, `0.30`, `0.20`이다. |
| `objective` | `conversion`, `traffic`, `awareness` 중 샘플링한다. 확률은 `0.60`, `0.25`, `0.15`이다. |
| `campaign_budget_krw` | lognormal 샘플을 사용하되 최소 `100,000 KRW`이다. |
| `duration_days` | `7`, `14`, `30` 중 샘플링한다. 확률은 `0.40`, `0.40`, `0.20`이다. |
| `campaign_name` | `{category}_{region.lower()}_{objective}_{index}` 형태이다. |
| `is_budget_over_1m_krw` | `campaign_budget_krw >= 1,000,000`이다. |
| `is_budget_over_5m_krw` | `campaign_budget_krw >= 5,000,000`이다. |
| `is_active_on_current_date` | `current_date between start_date and end_date`이다. |

### Synthetic Payment Generation

| Concept | Definition |
|---|---|
| `expected_payment_count` | Poisson 분포의 lambda로 사용한다. |
| lambda formula | `(tier_base_rate + log1p(observed_engagement_count) * 0.035) * budget_multiplier * category_multiplier * objective_multiplier * partnership_multiplier`. |
| tier base rate | `low=0.03`, `medium=0.12`, `high=0.45`, `viral=1.50`. |
| budget multiplier | `sqrt(campaign_budget_krw / 1,000,000)`를 `0.35`~`3.00` 사이로 clamp한다. |
| category multiplier | `beauty=1.8`, `fashion=1.3`, `food=1.1`. |
| objective multiplier | `conversion=1.25`, `traffic=0.85`, `awareness=0.45`. |
| partnership multiplier | paid partnership observed면 `1.15`, 아니면 `1.0`. |
| `payment_count` | `Poisson(expected_payment_count)` 샘플이다. |
| event time | post 시각 이후 0~7일 사이에서 초 단위 random offset을 둔다. |
| `payment_amount_krw` | lognormal 샘플, mean `9.2`, sigma `0.7`이다. |
| `payment_amount_local` | `payment_amount_krw / fx_rate_to_krw`이다. |
| `is_refunded` | random 값이 `0.03`보다 작으면 true이다. |
| `net_payment_amount_krw` | refund면 `-payment_amount_krw`, 아니면 `payment_amount_krw`이다. |
| deterministic RNG | `SEED`와 `post_campaign_attribution_id` hash로 attribution 단위 deterministic random generator를 만든다. |

### Campaign Payment Performance

| Concept | Definition |
|---|---|
| `attributed_posts` | campaign에 귀속된 attribution row 수이다. |
| `distinct_posts` | campaign별 distinct post 수이다. |
| `distinct_creators` | campaign별 distinct creator 수이다. |
| `paid_partnership_posts` | paid partnership observed post 수이다. |
| `avg_observed_engagement_count` | attribution의 observed engagement 평균이다. |
| `high_engagement_posts` | observed engagement tier가 `high` 또는 `viral`인 attribution 수이다. |
| `viral_engagement_posts` | observed engagement tier가 `viral`인 attribution 수이다. |
| `payment_events` | campaign별 payment event 수이다. |
| `attributed_posts_with_payment` | payment가 발생한 distinct attribution 수이다. |
| `paying_creators` | payment가 발생한 distinct creator 수이다. |
| `refunded_events` | refund event 수이다. |
| `gross_payment_amount_krw` | campaign별 gross payment 합계이다. |
| `net_payment_amount_krw` | campaign별 net payment 합계이다. |
| `avg_payment_amount_krw` | campaign별 gross payment 평균이다. |
| `first_payment_ts_utc` | campaign의 최초 payment timestamp이다. |
| `last_payment_ts_utc` | campaign의 최종 payment timestamp이다. |
| `cost_per_payment_event_krw` | `campaign_budget_krw / payment_events`이다. |
| `payment_events_per_attributed_post` | `payment_events / attributed_posts`이다. |

### Feature Layer and Model Evaluation

| Concept | Definition |
|---|---|
| categorical features | `region`, `category`, `objective`. |
| numeric features | budget, duration, attribution counts, creator counts, partnership/high/viral counts, engagement average, and rate features. |
| `paid_partnership_post_rate` | `paid_partnership_posts / attributed_posts`. |
| `high_engagement_post_rate` | `high_engagement_posts / attributed_posts`. |
| `viral_engagement_post_rate` | `viral_engagement_posts / attributed_posts`. |
| `creator_diversity_rate` | `distinct_creators / attributed_posts`. |
| training labels | `label_payment_events`, `label_net_payment_amount_krw`, `label_roas`, `label_roas_performance_tier`, `label_is_roas_over_1x`, `label_has_positive_net_payment`. |
| scoring set | label 컬럼을 제외하고 `current_date`를 `scoring_snapshot_date`로 둔다. |
| baseline prediction | 같은 objective의 평균 ROAS를 사용한다. objective 평균이 없으면 global mean을 사용한다. |
| prediction table key | `(scoring_snapshot_date, campaign_id, model_name)`. |
| model comparison strategy | leave-one-out validation. |
| candidate models | `global_mean_baseline_v1`, `objective_mean_roas_baseline_v1`, `linear_regression_numpy_v1`, `ridge_regression_numpy_v1`, `knn_regression_numpy_v1`. |
| best model selection | `(mae, rmse)`가 가장 낮은 모델을 best로 선택한다. |
| linear model artifact | full training rows로 linear regression을 다시 fit하고 `agent/model_artifacts/campaign_roas_linear_v1.json`에 저장한다. |
| model eval bias | model comparison script에서는 `avg(predicted - actual)`이다. monitor SQL의 bias와 부호가 반대이므로 문맥을 명시해야 한다. |

## Positive Question Mapping

| ID | User Wording | Required Interpretation |
|---|---|---|
| `p4_q001` | Which creators should we review first for sponsored content? | Filter `included_in_creator_review = true`; order by `sponsored_candidate_posts desc, sponsored_candidate_rate desc`; limit 20. |
| `p4_q002` | Show the top 20 creators with at least one sponsored candidate post. | Filter `sponsored_candidate_posts >= 1`; order by `sponsored_candidate_posts desc, creator_username asc`; limit 20. |
| `p4_q003` | Which influencers have the top 10 sponsored candidate rates? | Order by `sponsored_candidate_rate desc, total_posts desc`; limit 10. |
| `p4_q004` | 협찬 후보 게시물이 있는 크리에이터 상위 20명을 보여줘. | Same as `p4_q002` with Korean wording. |
| `p4_q005` | 광고 의심 비율이 높은 작성자 Top 10은 누구야? | Use `sponsored_candidate_rate`; order by `sponsored_candidate_rate desc, total_posts desc`; limit 10. |
| `p4_q006` | 우선 검토 대상 크리에이터 상위 20명만 보여줘. | Filter `included_in_creator_review = true`; select `creator_username`, `sponsored_candidate_posts`, `sponsored_candidate_rate`, `included_in_creator_review`; order by `sponsored_candidate_posts desc, sponsored_candidate_rate desc`; limit 20. |
| `p4_q007` | List the top 10 creators where likes are often hidden. | Use Top 10 by `hidden_likes_rate desc, hidden_likes_posts desc`. |
| `p4_q008` | 평균 댓글 수가 높은 인플루언서 Top 10을 보여줘. | Order by `avg_comments_count desc`; limit 10. |
| `p4_q009` | Show the first 20 creators that have engagement signals available. | Filter `has_engagement_signal = true`; order by `creator_username asc`; limit 20. |
| `p4_q010` | 게시물이 2개 이상인데 협찬 후보가 없는 계정을 찾아줘. | Filter `total_posts >= 2 and sponsored_candidate_posts = 0`; order by `total_posts desc, creator_username asc`. |
| `p5_q001` | Which campaigns have the highest ROAS? | Use campaign ROI table; order by `roas desc, net_payment_amount_krw desc`; limit 5. |
| `p5_q002` | Show average ROAS and net payment amount by campaign objective. | Group by `campaign_objective`; compute `count(*)`, `avg(roas)`, `avg(net_payment_amount_krw)`. |
| `p5_q003` | 전환 목적 캠페인 중 ROAS가 높은 캠페인 Top 10을 보여줘. | Filter `campaign_objective = 'conversion'`; order by `roas desc, total_payment_events desc`; limit 10. |
| `p5_q004` | 순결제액이 있는 ROI 검토 대상 캠페인을 보여줘. | Filter `has_positive_net_payment = true and included_in_campaign_roi_review = true`; order by `roas desc, campaign_id asc`. |
| `p5_q005` | Which campaigns have the largest ROAS prediction errors in the latest snapshot? | Latest snapshot filter; order by `absolute_roas_prediction_error desc, campaign_id asc`; limit 5. |
| `p5_q006` | 최신 예측에서 실제 ROAS가 예측보다 높았던 캠페인을 찾아줘. | Latest snapshot filter plus `roas_prediction_error > 0`; order by `roas_prediction_error desc, campaign_id asc`. |
| `p5_q007` | Compare average actual ROAS and predicted ROAS by objective in the latest prediction snapshot. | Latest snapshot filter; group by `objective`; compute average actual, predicted, and error. |
| `p5_q008` | 최신 ROAS 예측 모델의 MAE와 bias를 요약해줘. | Latest snapshot filter; group by `model_name`; compute `count(*)`, MAE, and bias. |
| `p5_q009` | Compare campaign count and average ROAS by objective and ROAS performance tier. | Group campaign ROI by `campaign_objective, roas_performance_tier`; select `count(*) as campaign_count`, `avg(roas) as avg_roas`; order by `avg_roas desc, campaign_objective asc, roas_performance_tier asc`; no LIMIT. |
| `p5_q010` | 지역별 ROI 검토 대상 캠페인 수와 평균 ROAS를 보여줘. | Filter `included_in_campaign_roi_review = true`; group by `campaign_region`; select `count(*) as review_campaign_count`, `avg(roas) as avg_roas`; order by `avg_roas desc, campaign_region asc`; no LIMIT. |
| `p5_q011` | Show the latest prediction rows with campaign ROI tier and prediction error, limited to 10 campaigns. | Join monitor to campaign ROI on `campaign_id`; latest snapshot filter; order by absolute error desc; limit 10. |
| `p5_q012` | 최신 예측 snapshot에서 objective별 MAE가 큰 순서로 보여줘. | Latest snapshot filter; group by `objective`; compute MAE; order by MAE desc. |
| `p5_q013` | Which latest prediction rows have absolute ROAS error at least 0.05, with campaign ROI tier? | Join monitor to campaign ROI; latest snapshot filter; filter `absolute_roas_prediction_error >= 0.05`; order by error desc. |
| `p5_q014` | 최신 snapshot에서 campaign ROI tier별 예측 오차를 요약해줘. | Join monitor to campaign ROI; latest snapshot filter; group by ROI tier; compute count, MAE, and bias. |

## Known Limitations

- Sponsored candidate detection is keyword-based and does not prove actual paid sponsorship.
- `often` and `high` are benchmark ranking terms unless the question provides an explicit threshold.
- `0.05` absolute ROAS error is an evaluation threshold, not a real production alert threshold.
- Campaign region, objective, payment, and ROAS values come from synthetic generation policy.
- Model comparison uses a small synthetic labeled set; production model-quality claims require larger real labels.
