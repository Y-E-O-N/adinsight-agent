with payment_events as (
    select * from {{ source('raw', 'syn_payment_events') }}
)

select
    payment_event_id,
    post_campaign_attribution_id,
    post_id,
    campaign_id,
    creator_username,
    event_ts as event_ts_utc,
    cast(event_ts as date) as event_date,

    region,
    category,
    objective,
    currency,
    payment_amount_local,
    fx_rate_to_krw,
    payment_amount_krw,
    is_refunded,
    (
        case
            when is_refunded then -1 * payment_amount_krw
            else payment_amount_krw
        end
    ) as net_payment_amount_krw,

    observed_engagement_count,
    observed_engagement_tier,
    campaign_budget_krw,
    paid_partnership_observed,
    expected_payment_count,

    conversion_model,
    synthetic_source,
    raw_payload,
    created_at,
    updated_at
from payment_events
