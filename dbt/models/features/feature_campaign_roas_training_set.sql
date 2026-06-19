with campaign_roi as (
    select * from {{ ref('mart_campaign_roi_summary') }}
)

select
    campaign_id,

    -- Categorical features
    region,
    category,
    objective,

    -- Numeric campaign setup features
    campaign_budget_krw,
    duration_days,

    -- Numeric observed content/engagement features
    attributed_posts,
    distinct_posts,
    distinct_creators,
    paid_partnership_posts,
    avg_observed_engagement_count,
    high_engagement_posts,
    viral_engagement_posts,
    (
        paid_partnership_posts::numeric
        / nullif(attributed_posts, 0)
    ) as paid_partnership_post_rate,
    (
        high_engagement_posts::numeric
        / nullif(attributed_posts, 0)
    ) as high_engagement_post_rate,
    (
        viral_engagement_posts::numeric
        / nullif(attributed_posts, 0)
    ) as viral_engagement_post_rate,
    (
        distinct_creators::numeric
        / nullif(attributed_posts, 0)
    ) as creator_diversity_rate,

    -- Labels and post-campaign outcomes
    payment_events as label_payment_events,
    net_payment_amount_krw as label_net_payment_amount_krw,
    roas as label_roas,
    roas_performance_tier as label_roas_performance_tier,
    is_roas_over_1x as label_is_roas_over_1x,
    has_positive_net_payment as label_has_positive_net_payment
from campaign_roi
where included_in_campaign_roi_review
