with campaigns as (
    select * from {{ source('raw', 'syn_campaigns') }}
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

    (campaign_budget_krw >= 1000000) as is_budget_over_1m_krw,
    (campaign_budget_krw >= 5000000) as is_budget_over_5m_krw,
    (current_date between start_date and end_date) as is_active_on_current_date,

    synthetic_source,
    raw_payload,
    created_at,
    updated_at
from campaigns
