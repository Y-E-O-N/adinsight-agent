# Session 19 Concepts — ROAS Model Comparison and API Serving

## 1. Model comparison harness

하나의 모델만 만들면 “이 모델이 좋은지” 판단하기 어렵다. 그래서 같은 feature table, 같은 label, 같은 validation 방식으로 여러 후보를 비교하는 구조를 만들었다.

이번 비교 후보는 아래 5개다.

- `global_mean_baseline_v1`
- `objective_mean_roas_baseline_v1`
- `linear_regression_numpy_v1`
- `ridge_regression_numpy_v1`
- `knn_regression_numpy_v1`

현재 best는 `linear_regression_numpy_v1`이고, baseline MAE `0.0892` 대비 MAE `0.0474`를 기록했다.

## 2. 왜 LightGBM / XGBoost / CatBoost를 보류했나

Boosting 계열 모델은 강력하지만 현재 labeled campaign row가 25개뿐이다. 이 정도 데이터에서는 복잡한 모델이 패턴을 학습했다기보다 데이터를 외웠을 가능성이 크다.

그래서 지금은 단순 모델을 먼저 비교하고, campaign row가 충분히 늘어난 뒤 같은 harness에 boosting 후보를 추가하는 것이 더 정직하다.

## 3. Model artifact

처음 FastAPI skeleton은 요청이 들어올 때마다 training table을 읽고 선형 회귀 계수를 다시 계산했다. 이것은 skeleton 검증에는 괜찮지만 serving 구조로는 비효율적이다.

그래서 현재는 `agent/model_artifacts/campaign_roas_linear_v1.json`에 아래 정보를 저장한다.

- model name
- training row count
- categorical feature categories
- numeric feature means/stds
- fitted coefficients
- limitation note

API는 이 JSON artifact를 읽고, request campaign의 scoring feature에 같은 전처리를 적용한 뒤 예측값만 계산한다.

## 4. Serving skeleton

Serving skeleton은 production API가 아니라 최소 API 구조다.

현재 갖춘 것:

- `GET /health`
- `POST /predict/campaign-roas`
- request/response schema
- Postgres scoring feature lookup
- artifact-backed prediction
- Docker Compose `api` service

아직 production이 아닌 이유:

- 인증 없음
- API latency benchmark 없음
- model registry 없음
- model artifact versioning 정책 없음
- pytest API test 없음

## 5. 다음 학습 포인트

다음 단계에서 배우면 좋은 개념:

- API latency와 p50/p95
- model registry
- model artifact versioning
- FastAPI dependency injection
- Docker service healthcheck
- ECS/Fargate + ALB로의 AWS mapping

