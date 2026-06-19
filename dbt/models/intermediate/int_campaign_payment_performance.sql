with campaigns as (
    select * from {{ ref('stg_syn_campaigns') }}
),

attributions as (
    select * from {{ ref('stg_syn_post_campaign_attributions') }}
),

payment_events as (
    select * from {{ ref('stg_syn_payment_events') }}
),

attribution_summary as (
    select
        campaign_id,
        count(*) as attributed_posts,
        count(distinct post_id) as distinct_posts,
        count(distinct creator_username) as distinct_creators,
        sum(case when paid_partnership_observed then 1 else 0 end) as paid_partnership_posts,
        avg(observed_engagement_count) as avg_observed_engagement_count,
        sum(case when observed_engagement_tier in ('high', 'viral') then 1 else 0 end) as high_engagement_posts,
        sum(case when observed_engagement_tier = 'viral' then 1 else 0 end) as viral_engagement_posts
    from attributions
    group by 1
),

payment_summary as (
    select
        campaign_id,
        count(*) as payment_events,
        count(distinct post_campaign_attribution_id) as attributed_posts_with_payment,
        count(distinct creator_username) as paying_creators,
        sum(case when is_refunded then 1 else 0 end) as refunded_events,
        sum(payment_amount_krw) as gross_payment_amount_krw,
        sum(net_payment_amount_krw) as net_payment_amount_krw,
        avg(payment_amount_krw) as avg_payment_amount_krw,
        min(event_ts_utc) as first_payment_ts_utc,
        max(event_ts_utc) as last_payment_ts_utc
    from payment_events
    group by 1
)

select
    campaigns.campaign_id,
    campaigns.campaign_name,
    campaigns.region,
    campaigns.category,
    campaigns.objective,
    campaigns.campaign_budget_krw,
    campaigns.start_date,
    campaigns.end_date,
    campaigns.duration_days,

    coalesce(attribution_summary.attributed_posts, 0) as attributed_posts,
    coalesce(attribution_summary.distinct_posts, 0) as distinct_posts,
    coalesce(attribution_summary.distinct_creators, 0) as distinct_creators,
    coalesce(attribution_summary.paid_partnership_posts, 0) as paid_partnership_posts,
    coalesce(attribution_summary.avg_observed_engagement_count, 0) as avg_observed_engagement_count,
    coalesce(attribution_summary.high_engagement_posts, 0) as high_engagement_posts,
    coalesce(attribution_summary.viral_engagement_posts, 0) as viral_engagement_posts,

    coalesce(payment_summary.payment_events, 0) as payment_events,
    coalesce(payment_summary.attributed_posts_with_payment, 0) as attributed_posts_with_payment,
    coalesce(payment_summary.paying_creators, 0) as paying_creators,
    coalesce(payment_summary.refunded_events, 0) as refunded_events,
    coalesce(payment_summary.gross_payment_amount_krw, 0) as gross_payment_amount_krw,
    coalesce(payment_summary.net_payment_amount_krw, 0) as net_payment_amount_krw,
    coalesce(payment_summary.avg_payment_amount_krw, 0) as avg_payment_amount_krw,
    payment_summary.first_payment_ts_utc,
    payment_summary.last_payment_ts_utc,

    (
        coalesce(payment_summary.net_payment_amount_krw, 0)
        / nullif(campaigns.campaign_budget_krw, 0)
    ) as roas,
    (
        campaigns.campaign_budget_krw
        / nullif(coalesce(payment_summary.payment_events, 0), 0)
    ) as cost_per_payment_event_krw,
    (
        coalesce(payment_summary.payment_events, 0)
        / nullif(coalesce(attribution_summary.attributed_posts, 0), 0)
    ) as payment_events_per_attributed_post
from campaigns
left join attribution_summary
    on campaigns.campaign_id = attribution_summary.campaign_id
left join payment_summary
    on campaigns.campaign_id = payment_summary.campaign_id
