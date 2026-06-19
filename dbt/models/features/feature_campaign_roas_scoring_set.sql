with campaign_roi as (
    select * from {{ ref('mart_campaign_roi_summary') }}
)

select
    current_date as scoring_snapshot_date,
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
    ) as creator_diversity_rate
from campaign_roi
where included_in_campaign_roi_review
