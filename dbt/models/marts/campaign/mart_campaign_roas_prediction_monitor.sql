with predictions as (
    select * from {{ source('feature_outputs', 'campaign_roas_baseline_predictions') }}
),

campaign_roi as (
    select * from {{ ref('mart_campaign_roi_summary') }}
)

select
    predictions.scoring_snapshot_date,
    predictions.model_name,
    predictions.campaign_id,
    campaign_roi.campaign_name,
    campaign_roi.region,
    campaign_roi.category,
    campaign_roi.objective,
    campaign_roi.campaign_budget_krw,

    predictions.predicted_roas,
    campaign_roi.roas as actual_roas,
    (
        campaign_roi.roas - predictions.predicted_roas
    ) as roas_prediction_error,
    abs(
        campaign_roi.roas - predictions.predicted_roas
    ) as absolute_roas_prediction_error,

    campaign_roi.net_payment_amount_krw,
    campaign_roi.payment_events,
    campaign_roi.roas_performance_tier as actual_roas_performance_tier,
    predictions.prediction_reason,
    predictions.training_rows_used,
    predictions.prediction_generated_at_utc
from predictions
left join campaign_roi
    on predictions.campaign_id = campaign_roi.campaign_id
