# Stage 5 Campaign ROAS Prediction Dashboard

## Purpose

`marts.mart_campaign_roas_prediction_monitor`를 Superset에서 바로 보는 BI dashboard로 연결한다.

이 dashboard의 목적은 모델 성능을 과장하는 것이 아니라, daily scoring 결과가 실제 ROAS와 얼마나 차이 나는지 운영자가 빠르게 확인하는 것이다.

## Dataset

- Superset database: `AdInsight Warehouse`
- Superset dataset: `marts.mart_campaign_roas_prediction_monitor`
- dbt model: `dbt/models/marts/campaign/mart_campaign_roas_prediction_monitor.sql`

## Chart

### Campaign ROAS Prediction Monitor Table

표시 컬럼:

- `campaign_id`
- `campaign_name`
- `objective`
- `predicted_roas`
- `actual_roas`
- `absolute_roas_prediction_error`
- `prediction_reason`

정렬:

- `absolute_roas_prediction_error` descending

이 정렬은 prediction error가 큰 campaign을 먼저 보게 해준다. 운영 관점에서는 평균 성능보다 "어떤 campaign에서 크게 틀렸는가"가 더 중요하기 때문이다.

## Dashboard

- Superset dashboard: `AdInsight Campaign ROAS Prediction Monitor`
- Export artifact: `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip`
- Rebuild script: `dashboards/scripts/create_campaign_roas_prediction_dashboard.py`

## Current Metrics

2026-06-19 기준:

- Prediction rows: `25`
- MAE from monitoring mart: `0.0799`
- Bias from monitoring mart: `0.0000`
- Predicted ROAS range: `0.0246` to `0.1482`

## Local vs AWS Mapping

| Local implementation | AWS managed-service equivalent |
|---|---|
| Superset dashboard | Amazon QuickSight dashboard |
| Postgres mart table | Redshift / Aurora PostgreSQL BI mart |
| Python scoring script | SageMaker Processing / Batch Transform job |
| `features` schema | SageMaker Feature Store or Redshift feature mart |
| Superset export ZIP | IaC-managed BI asset or QuickSight asset bundle |

## Notes

- 현재 예측 모델은 `objective_mean_roas_baseline_v1`이며, objective별 평균 ROAS를 쓰는 baseline이다.
- synthetic payment 기반이므로 실제 광고 성과 예측 주장으로 쓰지 않는다.
- 이 dashboard는 "ML 성능 주장"보다 "scoring output이 BI/monitoring layer까지 연결되는 운영 구조"를 보여주는 포트폴리오 자산이다.
