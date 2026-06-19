with campaign_roi as (
    select * from {{ ref('mart_campaign_roi_summary') }}
)

select
    campaign_id,
    campaign_name,
    region as campaign_region,
    category as product_category,
    objective as campaign_objective,
    campaign_budget_krw,
    start_date as campaign_start_date,
    end_date as campaign_end_date,
    duration_days as campaign_duration_days,

    attributed_posts as total_attributed_posts,
    distinct_posts as unique_attributed_posts,
    distinct_creators as unique_creators,
    paid_partnership_posts,
    avg_observed_engagement_count,
    high_engagement_posts,
    viral_engagement_posts,

    payment_events as total_payment_events,
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
    has_positive_net_payment,
    is_roas_over_1x,
    is_roas_over_2x,
    included_in_campaign_roi_review,
    roas_performance_tier
from campaign_roi
