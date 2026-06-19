# Session 17 — Campaign ROAS Prediction Monitoring (2026-06-19)

**Phase**: Phase 4/5 — AI-native campaign ROI + ROAS prediction monitoring
**Duration**: ~2h
**Operator**: Yeon (with Codex)

## Goals
- Session 16의 campaign ROI mart를 AI/Text2SQL/ML feature layer로 확장한다.
- Campaign ROAS prediction baseline을 만들고 Superset에서 모니터링 가능한 형태로 연결한다.
- 매일 데이터가 들어올 때 feature, prediction, monitor mart가 다시 계산되는 Airflow 운영 흐름을 만든다.
- 지금까지의 진행 상태와 LINE JD 기준 다음 도구 선택 방향을 문서화한다.

## Done
- [x] `ai_native.ai_campaign_roi_summary`를 추가했다.
  - grain: `campaign_id`
  - 목적: campaign/payment mart를 자연어 질의와 agent schema retrieval에 더 친화적인 컬럼명과 metadata로 노출
- [x] ML feature layer를 추가했다.
  - `features.feature_campaign_roas_training_set`
  - `features.feature_campaign_roas_scoring_set`
  - label column은 `label_roas`, `label_roas_performance_tier`로 분리해 feature leakage를 피했다.
- [x] baseline evaluator를 추가했다.
  - script: `agent/eval/run_campaign_roas_baseline.py`
  - global mean vs objective mean baseline 비교
- [x] daily scoring script를 추가했다.
  - script: `agent/eval/run_campaign_roas_scoring.py`
  - output: `features.campaign_roas_baseline_predictions`
  - idempotent delete+insert by `scoring_snapshot_date`, `model_name`
- [x] prediction monitor mart를 추가했다.
  - `marts.mart_campaign_roas_prediction_monitor`
  - predicted ROAS, actual ROAS, signed error, absolute error를 campaign grain으로 비교
- [x] Superset prediction dashboard를 생성했다.
  - dashboard: `AdInsight Campaign ROAS Prediction Monitor`
  - chart: `Campaign ROAS Prediction Monitor Table`
  - export: `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip`
  - screenshot: `docs/images/05_campaign_roas_prediction_monitor.png`
- [x] Airflow daily prediction DAG를 추가했다.
  - DAG: `campaign_roas_prediction_daily`
  - 순서: feature dbt run → scoring script → monitor mart dbt run → dbt test → metrics 기록
  - manual run success: `manual__phase5_prediction_validation_20260619`
- [x] Superset screenshot 파일명을 포트폴리오 규칙에 맞게 변경했다.
  - from: `docs/images/스크린샷 2026-06-19 오후 5.58.32.png`
  - to: `docs/images/05_campaign_roas_prediction_monitor.png`
- [x] JD 기반 cloud/tooling strategy 문서를 추가했다.
  - `docs/analysis/stage5_jd_cloud_tooling_strategy.md`
- [x] 검증된 checkpoint를 커밋했다.
  - `9ef5ad1 Add campaign ROAS prediction monitoring flow`
  - `c03eb5e Add campaign ROAS prediction daily DAG`

## Decisions
- **첫 ROAS 예측 모델은 baseline으로 시작한다**: 데이터가 25 labeled campaign rows 수준이므로 복잡한 모델보다 objective별 평균 ROAS baseline이 더 정직한 비교 기준이다.
- **label과 feature를 이름부터 분리한다**: `label_*` prefix를 붙여 모델 입력과 예측 대상이 섞이지 않게 했다.
- **prediction output은 dbt model이 아니라 script output table로 둔다**: scoring은 Python 모델 실행 결과이므로 `features.campaign_roas_baseline_predictions`를 source로 선언하고, dbt mart에서 이를 소비한다.
- **운영 갱신은 Airflow DAG로 표현한다**: 매일 feature 재계산, prediction 재생성, monitor mart/test/metrics까지 한 DAG에서 순서 보장한다.
- **현재 JD 방향에서는 AWS managed service를 바로 붙이기보다 로컬 구현과 AWS 대응표를 먼저 명확히 한다**: 포트폴리오에서는 “도구 이름”보다 “어떤 운영 문제를 어떤 서비스로 풀 수 있는가”가 더 중요하다.

## Files changed
- `dbt/models/ai_native/ai_campaign_roi_summary.sql` — campaign ROI semantic mart
- `dbt/models/ai_native/schema.yml` — ai_native campaign metadata/tests
- `dbt/models/features/feature_campaign_roas_training_set.sql` — ROAS training feature table
- `dbt/models/features/feature_campaign_roas_scoring_set.sql` — ROAS daily scoring feature table
- `dbt/models/features/schema.yml` — feature models + prediction output source tests
- `agent/eval/run_campaign_roas_baseline.py` — baseline evaluation script
- `agent/eval/run_campaign_roas_scoring.py` — daily scoring script
- `dbt/models/marts/campaign/mart_campaign_roas_prediction_monitor.sql` — prediction vs actual monitor mart
- `dbt/models/marts/campaign/schema.yml` — monitor mart tests
- `dashboards/scripts/create_campaign_roas_prediction_dashboard.py` — Superset dashboard rebuild script
- `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip` — Superset export artifact
- `docs/images/05_campaign_roas_prediction_monitor.png` — Superset monitor screenshot
- `docs/analysis/stage5_campaign_roas_prediction_dashboard.md` — dashboard design note
- `dags/dag_campaign_roas_prediction_daily.py` — Airflow daily prediction refresh DAG
- `docker-compose.yml` — Airflow worker에 `agent/` mount 추가
- `metrics/run_results.jsonl` — Phase 5 DAG validation metrics append
- `docs/portfolio_draft.md` — Phase 4/5/6 progress and assets 갱신
- `docs/analysis/stage5_jd_cloud_tooling_strategy.md` — LINE JD 기반 cloud/tooling strategy

## Concepts taught (학습 강화)
- **Baseline model** — 복잡한 ML 전에 global/objective mean 같은 단순 예측 기준선을 만들어야 이후 모델 개선을 정직하게 비교할 수 있다.
- **Feature leakage** — 정답에 해당하는 ROAS tier를 feature로 넣으면 모델이 답을 보고 학습하는 문제가 생긴다.
- **Scoring set vs training set** — training set은 label을 포함하고, scoring set은 매일 예측할 입력 feature만 포함한다.
- **Prediction monitor** — 예측값과 실제값을 나란히 두고 error, absolute error, bias를 보는 운영 mart다.
- **Airflow orchestration** — feature 생성, Python scoring, dbt mart/test, metrics 기록을 순서 있는 task graph로 묶어 daily refresh를 보장한다.
- **AWS 대응 사고법** — 로컬 Airflow/Postgres/dbt/Superset이 각각 MWAA/Glue or ECS, Redshift or RDS, dbt Cloud or CodeBuild, QuickSight에 어떻게 대응되는지 설명했다.

## Portfolio assets added
- Superset screenshot:
  - `docs/images/05_campaign_roas_prediction_monitor.png`
- Superset export:
  - `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip`
- Dashboard design note:
  - `docs/analysis/stage5_campaign_roas_prediction_dashboard.md`
- JD/cloud strategy note:
  - `docs/analysis/stage5_jd_cloud_tooling_strategy.md`
- Metrics:
  - `metrics/run_results.jsonl`에 `phase=p5`, `step=campaign_roas_prediction_daily` append
- Git commits:
  - `9ef5ad1 Add campaign ROAS prediction monitoring flow`
  - `c03eb5e Add campaign ROAS prediction daily DAG`

## Open questions
- Baseline 다음 모델을 `scikit-learn` regression으로 갈지, JD 키워드에 맞춰 LightGBM 계열로 갈지 결정한다.
- Text2SQL 평가셋을 campaign ROI / prediction monitor까지 확장할지 결정한다.
- AWS 실습을 실제 클라우드 배포까지 할지, 비용을 줄이기 위해 architecture mapping + IaC skeleton까지만 할지 결정한다.
- 모델 서빙 API를 FastAPI로 먼저 만들지, batch scoring DAG 안정화를 먼저 강화할지 결정한다.

## Metrics
- Baseline evaluation:
  - rows: `25`
  - global mean MAE: `0.0935`
  - objective mean MAE: `0.0892`
  - objective mean RMSE: `0.1349`
- Scoring output:
  - table: `features.campaign_roas_baseline_predictions`
  - rows: `25`
  - model: `objective_mean_roas_baseline_v1`
  - predicted ROAS min/avg/max: `0.0246 / 0.1279 / 0.1482`
- Prediction monitor:
  - table: `marts.mart_campaign_roas_prediction_monitor`
  - rows: `25`
  - MAE: `0.0799`
  - bias: `0.0000`
- dbt:
  - full `dbt run`: `15/15 PASS`
  - full `dbt test`: `248/248 PASS`
  - `dbt docs generate`: success
- Airflow:
  - DAG: `campaign_roas_prediction_daily`
  - manual run: `manual__phase5_prediction_validation_20260619`
  - run state: `success`
  - task states: `5/5 success`
- Superset:
  - dashboard count: `2`
  - chart count: `2`
  - export ZIP: `18 KB`

## Next session — start here
1. 현재 기준점 확인:
   ```bash
   git status --short
   git log --oneline -5
   docker compose ps
   ```
2. Airflow prediction DAG 확인:
   ```bash
   docker compose exec airflow-worker airflow dags list-runs -d campaign_roas_prediction_daily --no-backfill -o table
   ```
3. JD 기반 다음 우선순위는 아래 순서가 적절하다.
   - A. Text2SQL 평가셋을 campaign ROI/prediction monitor까지 확장
   - B. `scikit-learn` 또는 LightGBM style ROAS regression model v1 추가
   - C. FastAPI `/predict` endpoint로 model serving API skeleton 추가
   - D. AWS 대응 아키텍처 문서 또는 Terraform/CDK skeleton 작성
4. 참고 문서:
   - `docs/analysis/stage5_jd_cloud_tooling_strategy.md`
   - `docs/analysis/stage5_campaign_roas_prediction_dashboard.md`
   - `docs/portfolio_draft.md`
