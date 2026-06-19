with campaign_performance as (
    select * from {{ ref('int_campaign_payment_performance') }}
)

select
    campaign_id,
    campaign_name,
    region,
    category,
    objective,
    campaign_budget_krw,
    start_date,
    end_date,
    duration_days,

    attributed_posts,
    distinct_posts,
    distinct_creators,
    paid_partnership_posts,
    avg_observed_engagement_count,
    high_engagement_posts,
    viral_engagement_posts,

    payment_events,
    attributed_posts_with_payment,
    paying_creators,
    refunded_events,
    gross_payment_amount_krw,
    net_payment_amount_krw,
    avg_payment_amount_krw,
    first_payment_ts_utc,
    last_payment_ts_utc,

    roas,
    cost_per_payment_event_krw,
    payment_events_per_attributed_post,

    (net_payment_amount_krw > 0) as has_positive_net_payment,
    (roas >= 1.0) as is_roas_over_1x,
    (roas >= 2.0) as is_roas_over_2x,
    (
        attributed_posts >= 5
        or payment_events >= 1
    ) as included_in_campaign_roi_review,

    case
        when payment_events = 0 then 'no_payment'
        when net_payment_amount_krw < 0 then 'negative_net'
        when roas < 1.0 then 'under_1x'
        when roas < 2.0 then 'one_to_two_x'
        else 'two_x_plus'
    end as roas_performance_tier
from campaign_performance
