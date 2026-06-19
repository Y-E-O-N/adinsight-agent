with attributions as (
    select * from {{ source('raw', 'syn_post_campaign_attributions') }}
)

select
    post_campaign_attribution_id,
    post_id,
    creator_username,
    campaign_id,
    post_date,
    source_hashtag,
    category,

    likes_count_clean,
    likes_hidden,
    comments_count,
    observed_engagement_count,
    observed_engagement_tier,
    paid_partnership_observed,

    (
        observed_engagement_tier in ('high', 'viral')
    ) as is_high_engagement_observed,
    (
        observed_engagement_tier = 'viral'
    ) as is_viral_engagement_observed,

    metric_policy,
    synthetic_source,
    raw_payload,
    created_at,
    updated_at
from attributions
