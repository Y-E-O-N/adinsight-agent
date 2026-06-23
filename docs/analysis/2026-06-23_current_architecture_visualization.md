# AdInsight Current Architecture Visualization

**Date**: 2026-06-23
**Scope**: Phase 2B through Phase 6 checkpoint
**Purpose**: README / portfolio draft용 현재 구현 흐름 시각화

## 1. End-to-End Flow

```mermaid
flowchart TD
    A[Apify Instagram collection<br/>ig_collect_daily / ig_collect_backfill] --> B[raw layer<br/>raw.ig_posts<br/>raw.ig_post_sources]
    B --> C[staging dbt models<br/>stg_ig_posts<br/>stg_syn_campaigns<br/>stg_syn_payment_events]
    C --> D[intermediate dbt models<br/>creator quality<br/>campaign payment performance]
    D --> E[creator mart<br/>marts.mart_creator_sponsored_summary]
    D --> F[campaign ROI mart<br/>marts.mart_campaign_roi_summary]

    E --> G[ai_native creator summary<br/>ai_native.ai_creator_sponsored_summary]
    F --> H[ai_native campaign ROI summary<br/>ai_native.ai_campaign_roi_summary]
    F --> I[ROAS feature layer<br/>features.feature_campaign_roas_training_set<br/>features.feature_campaign_roas_scoring_set]

    I --> J[baseline scoring<br/>objective_mean_roas_baseline_v1]
    I --> K[model comparison runner<br/>linear / ridge / KNN / baselines]

    J --> L[prediction monitor mart<br/>marts.mart_campaign_roas_prediction_monitor]
    L --> M[Superset dashboard<br/>AdInsight Campaign ROAS Prediction Monitor]

    G --> N[Text2SQL expected-SQL eval set]
    H --> N
    L --> N
    N --> O[expected SQL evaluator<br/>18 / 18 PASS]

    K --> P[model benchmark metric<br/>best: linear_regression_numpy_v1<br/>MAE 0.0474 vs baseline 0.0892]
```

## 2. Recent Checkpoint Timeline

```mermaid
timeline
    title AdInsight recent implementation checkpoints
    2026-06-19 : Synthetic payment events
               : raw.syn_campaigns 30
               : raw.syn_payment_events 498
    2026-06-19 : Campaign ROI mart
               : marts.mart_campaign_roi_summary 30 rows
               : dbt test 124 / 124 PASS
    2026-06-19 : ROAS prediction monitoring
               : objective mean baseline MAE 0.0892
               : monitor MAE 0.0799
               : Airflow DAG success
    2026-06-23 : Text2SQL eval expansion
               : questions 10 -> 18
               : expected SQL 18 / 18 PASS
    2026-06-23 : ROAS model comparison
               : 5 candidate models
               : best linear regression
               : MAE 0.0474 vs baseline 0.0892
```

## 3. Portfolio Summary Table

| Layer | Current implementation | Evidence |
|---|---|---|
| Data ingestion | Apify daily/backfill DAGs | `ig_collect_daily`, `ig_collect_backfill`, `metrics/run_results.jsonl` |
| Warehouse modeling | raw → staging → intermediate → marts | `dbt/models/` |
| AI-native mart | creator and campaign semantic summaries | `dbt/models/ai_native/` |
| ROAS prediction | baseline scoring + model comparison runner | `agent/eval/run_campaign_roas_scoring.py`, `agent/eval/run_campaign_roas_model.py` |
| Monitoring | prediction monitor mart + Superset dashboard | `marts.mart_campaign_roas_prediction_monitor`, `docs/images/05_campaign_roas_prediction_monitor.png` |
| Text2SQL eval | 18 expected-SQL questions | `agent/eval/text2sql_questions.yml`, `18/18 PASS` |
| Portfolio metrics | JSONL append-only evidence | `metrics/run_results.jsonl` |

## 4. Key Numbers

| Metric | Value |
|---|---:|
| Text2SQL expected-SQL questions | 18 |
| Expected-SQL evaluator result | 18 / 18 PASS |
| ROAS model training rows | 25 |
| Objective mean baseline MAE | 0.0892 |
| Best ML v1 MAE | 0.0474 |
| Best ML v1 model | `linear_regression_numpy_v1` |
| Prediction monitor MAE | 0.0799 |
| Latest committed model checkpoint | `66e9c13 Add campaign ROAS model comparison` |

## Known Limitations

- Current model benchmark uses only 25 synthetic labeled campaign rows, so it is benchmark evidence, not production performance evidence.
- LightGBM, XGBoost, and CatBoost are intentionally deferred until more labeled campaign rows exist.
- Mermaid diagrams are source diagrams. Export to SVG/PNG separately before embedding in a polished README or PDF.

