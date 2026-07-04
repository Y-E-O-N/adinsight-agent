# Stage 6 Text2SQL Demo Evidence

## Purpose

`POST /query` deterministic Text2SQL v1을 Superset campaign ROAS monitor 데모와 함께 보여주기 위한 실측 증거를 남긴다.

## Runtime

- Captured at: `2026-06-29T18:56:37+0900`
- API server: `uvicorn api.main:app` on `127.0.0.1:8000`
- Postgres: local Docker Compose service on `5432`
- Superset screenshot source: `docs/images/05_campaign_roas_prediction_monitor.png`

## Health Check

```json
{"status":"ok","service":"adinsight-api"}
```

## English Query

Question:

```text
Which campaigns have the highest ROAS?
```

Result summary:

| Field | Value |
|---|---|
| `question_id` | `p5_q001` |
| `expected_model` | `ai_native.ai_campaign_roi_summary` |
| `row_count` | `5` |
| top campaign | `camp_000029` |
| top campaign name | `beauty_kr_conversion_000029` |
| top ROAS | `0.5969125239376458` |
| latency | `44.922ms` |

SQL executed:

```sql
select
    campaign_id,
    campaign_name,
    roas,
    net_payment_amount_krw
from ai_native.ai_campaign_roi_summary
order by roas desc, net_payment_amount_krw desc
limit 5
```

## Korean Query

Question:

```text
최신 ROAS 예측 모델의 MAE와 bias를 요약해줘.
```

Result summary:

| Field | Value |
|---|---|
| `question_id` | `p5_q008` |
| `expected_model` | `marts.mart_campaign_roas_prediction_monitor` |
| `row_count` | `1` |
| model | `objective_mean_roas_baseline_v1` |
| prediction rows | `25` |
| MAE | `0.07988873820803322` |
| bias | `-1.095444e-16` |
| latency | `41.072ms` |

SQL executed:

```sql
select
    model_name,
    count(*) as prediction_rows,
    avg(absolute_roas_prediction_error) as mae,
    avg(roas_prediction_error) as bias
from marts.mart_campaign_roas_prediction_monitor
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
group by model_name
order by model_name asc
```

## Artifact

- Demo GIF: `docs/images/06_text2sql_demo.gif`
- Generator script: `dashboards/scripts/create_text2sql_demo_gif.sh`

## Known Limitation

This is still deterministic Text2SQL v1. It matches curated questions from `agent/eval/text2sql_questions.yml` and executes validated SELECT SQL. It is not free-form LLM SQL generation yet.
