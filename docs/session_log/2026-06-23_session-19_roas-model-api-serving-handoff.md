# Session 19 — ROAS Model and API Serving Handoff (2026-06-23)

**Phase**: Phase 6 — ROAS model comparison + FastAPI serving skeleton  
**Duration**: ~2h  
**Operator**: Yeon (with Codex)

## Goals
- Session 18 이후 작업을 이어서 ROAS ML model v1을 구현한다.
- 단일 모델이 아니라 여러 단순 모델을 같은 검증 방식으로 비교한다.
- 현재 구현 흐름을 새 세션과 포트폴리오에서 이해할 수 있게 시각화한다.
- FastAPI `/predict/campaign-roas` skeleton을 추가하고, request-time fitting 대신 model artifact loading 구조로 개선한다.
- 기능 코드 커밋과 push를 완료하고, 이 handoff 문서까지 추가해 새 세션이 `origin/main` 기준으로 이어갈 수 있게 만든다.

## Done
- [x] Session 18 Text2SQL eval 확장 checkpoint를 커밋했다.
  - commit: `f25e3c5 Expand Text2SQL eval for campaign ROI`
- [x] ROAS model comparison runner를 추가했다.
  - script: `agent/eval/run_campaign_roas_model.py`
  - candidates:
    - `global_mean_baseline_v1`
    - `objective_mean_roas_baseline_v1`
    - `linear_regression_numpy_v1`
    - `ridge_regression_numpy_v1`
    - `knn_regression_numpy_v1`
  - commit: `66e9c13 Add campaign ROAS model comparison`
- [x] 현재 구현 흐름을 Mermaid 문서로 시각화했다.
  - doc: `docs/analysis/2026-06-23_current_architecture_visualization.md`
  - commit: `35522c9 Document current architecture visualization`
- [x] FastAPI serving skeleton을 추가했다.
  - endpoints:
    - `GET /health`
    - `POST /predict/campaign-roas`
  - files:
    - `api/main.py`
    - `api/schemas.py`
    - `infra/api/Dockerfile`
    - `docker-compose.yml`
  - commit: `005a660 Add FastAPI campaign ROAS serving skeleton`
- [x] API가 요청마다 모델을 다시 fit하지 않도록 model artifact loading으로 개선했다.
  - artifact: `agent/model_artifacts/campaign_roas_linear_v1.json`
  - API response now includes `model_artifact_path`
  - commit: `371f24d Load ROAS model artifact in FastAPI`
- [x] 8 local functional commits를 `origin/main`에 push했다.
  - latest functional commit before handoff docs: `371f24d`

## Decisions
- **Boosting models는 보류한다**: LightGBM, XGBoost, CatBoost는 지금 붙일 수 있지만 labeled campaign row가 25개라 성능 수치가 신뢰하기 어렵다. 현재는 linear/ridge/KNN/baseline 비교로 충분하고, 데이터가 늘어난 뒤 boosting 계열을 같은 평가 harness에 추가한다.
- **Model v1은 NumPy 기반으로 유지한다**: scikit-learn 없이도 선형 회귀, ridge, KNN 비교를 구현해 dependency와 network risk를 줄였다.
- **API skeleton은 artifact-backed로 한 단계 개선한다**: 최초 skeleton은 요청 시점에 training table로 계수를 다시 계산했지만, 이후 `campaign_roas_linear_v1.json` artifact를 생성하고 API가 이를 load하도록 바꿨다.
- **`dags/dag_ig_collect_daily.py` 변경은 이번 커밋에서 제외한다**: hashtag 후보 대부분이 주석 처리된 별도 로컬 변경이다. API/ML 작업과 무관하므로 새 세션에서 의도를 확인한 뒤 커밋 또는 복원한다.

## Files changed
- `agent/eval/run_campaign_roas_model.py` - ROAS model comparison runner + linear model artifact export/load/predict helpers
- `agent/model_artifacts/campaign_roas_linear_v1.json` - current best model artifact
- `api/main.py` - FastAPI app, health endpoint, artifact-backed campaign ROAS prediction endpoint
- `api/schemas.py` - request/response schemas
- `api/__init__.py` - API package marker
- `infra/api/Dockerfile` - API service image build
- `docker-compose.yml` - `api` service on port `8000`
- `pyproject.toml`, `uv.lock` - `fastapi`, `uvicorn` dependencies
- `docs/analysis/2026-06-23_current_architecture_visualization.md` - current architecture Mermaid visualization
- `docs/portfolio_draft.md` - Text2SQL, model comparison, API serving evidence
- `metrics/run_results.jsonl` - Text2SQL eval, model comparison, model artifact export metrics

## Concepts taught
- **Model comparison harness** - 여러 모델을 같은 데이터와 같은 검증 방식으로 비교해야 baseline 대비 개선이 설득력 있다.
- **Leave-one-out validation** - labeled rows가 25개뿐일 때 각 row를 한 번씩 검증용으로 빼는 작은 데이터용 평가 방식이다.
- **Model artifact** - 학습된 계수와 전처리 정보를 파일로 저장해 API가 요청마다 재학습하지 않게 하는 산출물이다.
- **Serving skeleton** - production API는 아니지만 request/response schema, endpoint, DB 연결, model artifact loading 흐름을 갖춘 최소 serving 구조다.

## Portfolio assets added
- Mermaid architecture visualization:
  - `docs/analysis/2026-06-23_current_architecture_visualization.md`
- ROAS model comparison metrics:
  - best model: `linear_regression_numpy_v1`
  - baseline MAE/RMSE: `0.0892 / 0.1349`
  - best MAE/RMSE: `0.0474 / 0.0577`
  - delta vs baseline: MAE `-0.0418`, RMSE `-0.0771`
- FastAPI serving evidence:
  - `/health` -> `{"status":"ok","service":"adinsight-api"}`
  - `/predict/campaign-roas` for `camp_000029` -> predicted ROAS `0.597425`
  - API loads artifact `agent/model_artifacts/campaign_roas_linear_v1.json`

## Open questions
- `dags/dag_ig_collect_daily.py` currently has most candidate hashtags commented out. Decide whether this is intentional throttling, a temporary local test, or should be reverted.
- API hardening options:
  - add latency metric
  - add pytest coverage for `/health` and `/predict/campaign-roas`
  - add versioned model registry table
  - add README curl examples
- Architecture options:
  - AWS target architecture document
  - Terraform/CDK skeleton
  - FastAPI service mapping to ECS/Fargate + ALB

## Metrics
- Text2SQL expected-SQL eval: `18/18 PASS`
- ROAS model rows: `25`
- Best model: `linear_regression_numpy_v1`
- Baseline MAE: `0.0892`
- Best model MAE: `0.0474`
- API smoke:
  - `GET /health`: `200 OK`
  - `POST /predict/campaign-roas`: `200 OK`
- Latest functional commit before handoff docs: `371f24d`

## Next session — start here
1. Recover state:
   ```bash
   git status --short --branch
   git log --oneline --decorate --max-count=8
   docker compose ps
   ```
2. Note the expected local dirty file:
   ```text
   M dags/dag_ig_collect_daily.py
   ```
   Inspect it first:
   ```bash
   git diff -- dags/dag_ig_collect_daily.py
   ```
3. Validate API if server is not already running:
   ```bash
   set -a; source .env; set +a; POSTGRES_HOST=localhost uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
   curl -s http://127.0.0.1:8000/health
   curl -s -X POST http://127.0.0.1:8000/predict/campaign-roas \
     -H 'Content-Type: application/json' \
     -d '{"campaign_id":"camp_000029"}'
   ```
4. Recommended next task:
   - First decide what to do with `dags/dag_ig_collect_daily.py`.
   - Then choose one:
     - API latency + pytest smoke tests
     - README API usage section
     - AWS target architecture / IaC skeleton
