# Stage 5 — LINE JD 기반 Cloud / Tooling Strategy

**작성일**: 2026-06-19  
**기준 JD**:
- `docs/job_description/LINE_Data Platform Engineer.md`
- `docs/job_description/LINE_Fintech Data Scientist.md`

## 1. 결론

현재 AdInsight는 로컬에서 이미 아래 축을 갖췄다.

| 현재 로컬 구현 | 역할 | JD 연결 |
|---|---|---|
| Airflow DAG | batch ETL / ML scoring orchestration | Data Engineering & Governance, MLOps |
| Postgres schemas (`raw`, `staging`, `intermediate`, `marts`, `features`, `ai_native`) | warehouse / mart / feature layer | Data Warehouse/Data Mart, Feature Store |
| dbt | transform, schema tests, semantic metadata | data quality, schema governance |
| Python scoring scripts | baseline model eval/scoring | ML feature development, model operation |
| Superset dashboard/export | BI monitoring | service/business performance monitoring |
| Text2SQL eval draft | agent evaluation seed | LLM Agent / RAG architecture |

다음 도구 선택은 **클라우드 이름을 붙이는 것**이 아니라, JD의 운영 문제를 하나씩 매핑하는 방식이 좋다.

추천 우선순위:

1. **AWS mapping 문서 + IaC skeleton**: 비용 없이 JD cloud 이해도를 보여준다.
2. **FastAPI model serving endpoint**: Data Platform Engineer JD의 AI Model Serving & API Development에 직접 대응한다.
3. **Text2SQL campaign ROI eval 확장**: AI Agent Development와 Data Scientist JD의 AI 활용 분석에 대응한다.
4. **ML model v1 + model registry style metadata**: Fintech Data Scientist JD의 feature/modeling/MLOps 축을 강화한다.
5. **Streaming은 optional**: 현재 데이터 도메인은 daily batch가 자연스럽다. 스트리밍은 과하게 붙이기보다 “event ingestion 확장안”으로 설계 문서에 남기는 편이 안전하다.

## 2. JD 요구사항 → 현재 구현 → AWS/유사 도구

| JD 요구사항 | 현재 구현 | AWS로 말하면 | 유사/오픈소스 도구 | 다음 액션 |
|---|---|---|---|---|
| 대규모 데이터 수집/정제/변환/적재 | Apify collect DAG, synthetic payment loader, dbt | MWAA, Glue, ECS/Fargate, Lambda | Airflow, Dagster, Prefect | 현재 Airflow DAG를 “MWAA 대응”으로 문서화 |
| DWH/Data Mart 설계/운영 | Postgres schemas + dbt marts | Redshift, Aurora/RDS, Athena + Glue Catalog | BigQuery, Snowflake, ClickHouse | schema lineage와 mart grain 정리 |
| 데이터 품질/무결성 모니터링 | dbt tests 248개, Airflow metrics JSONL | CloudWatch, Glue Data Quality, Deequ | Great Expectations, Soda, dbt tests | dbt test 결과를 운영 지표로 문서화 |
| Feature Store 적용 | `features.feature_campaign_roas_*` | SageMaker Feature Store | Feast, Tecton | feature table 계약 문서 추가 |
| ML 모델 운영 | baseline eval/scoring script, Airflow DAG | SageMaker Processing/Training/Batch Transform | MLflow, BentoML | sklearn/LightGBM v1 + model metrics table |
| 모델 서빙 API | 아직 없음 | ECS/Fargate + ALB, Lambda, API Gateway, SageMaker Endpoint | FastAPI, BentoML, KServe | FastAPI `/predict` skeleton 추가 |
| LLM Agent / RAG | Text2SQL eval draft, ai_native marts | Bedrock, OpenSearch Serverless, RDS pgvector | LangChain, LlamaIndex, pgvector | campaign ROI questions 추가 |
| Vector DB 검색 최적화 | pgvector extension 준비 | OpenSearch Serverless, Aurora/RDS pgvector | Qdrant, Milvus, Weaviate | schema embedding index 단계에서 사용 |
| Docker/K8s 운영 | Docker Compose local stack | ECS/Fargate, EKS | Kubernetes, Helm | Compose → ECS/EKS mapping 문서 |
| 실시간 스트리밍 | 아직 없음 | Kinesis, MSK, Lambda | Kafka, Redpanda, Flink | payment event stream 확장안으로 보류 |

## 3. Data Platform Engineer JD 대응 전략

이 JD는 “모델을 잘 만드는 사람”보다 **AI/ML이 서비스로 안정적으로 연결되게 만드는 사람**에 가깝다.

강화해야 할 포트폴리오 메시지:

- Airflow로 daily data + prediction refresh를 운영 DAG로 구성했다.
- dbt tests로 mart/feature/prediction source의 품질 계약을 관리했다.
- Superset dashboard로 예측 오차를 운영자가 볼 수 있게 만들었다.
- 다음은 FastAPI `/predict`와 `/query`를 붙여 model/data serving API까지 확장한다.

추천 AWS stack:

| 레이어 | AWS 선택 | 이유 |
|---|---|---|
| Orchestration | MWAA | 현재 Airflow DAG와 1:1 대응이 가장 명확하다. |
| Warehouse | Redshift Serverless 또는 RDS Postgres | 포트폴리오 비용을 고려하면 RDS/Postgres mapping이 현실적이고, 대규모 DWH 설명은 Redshift로 확장 가능하다. |
| Transform | dbt Core on MWAA/ECS 또는 dbt Cloud | 현재 dbt 구조를 그대로 운영화할 수 있다. |
| Model batch scoring | SageMaker Processing 또는 ECS scheduled task | 현재 Python scoring script와 대응된다. |
| API serving | ECS Fargate + FastAPI + ALB | Spring Boot 경험이 없더라도 API serving 역량을 보여주기 좋다. |
| Monitoring | CloudWatch + dbt artifacts + dashboard | DAG success, dbt test, prediction MAE를 운영 지표로 묶는다. |
| Secrets | Secrets Manager | `.env` 로컬 운영과 managed secret 차이를 설명할 수 있다. |

## 4. Fintech Data Scientist JD 대응 전략

이 JD는 SQL/Python으로 직접 feature를 설계하고, AI/ML 모델을 만들어 사업화 가능성을 검토하는 역할이다.

강화해야 할 포트폴리오 메시지:

- observed engagement 기반으로 campaign attribution/payment feature를 설계했다.
- label과 feature를 분리해 leakage를 피했다.
- baseline model을 먼저 만들고 MAE/RMSE로 평가했다.
- 다음은 ML model v1을 추가해 baseline 대비 개선 여부를 수치로 비교한다.

추천 tool stack:

| 레이어 | 선택 | 이유 |
|---|---|---|
| Feature engineering | dbt + Python | SQL feature와 Python model boundary가 명확하다. |
| Modeling | scikit-learn first, LightGBM style second | 데이터가 작으므로 sklearn으로 검증 흐름을 먼저 만든 뒤 LightGBM으로 확장한다. |
| Experiment tracking | MLflow local | 모델명, metric, artifact를 남겨 MLOps 스토리를 만들기 좋다. |
| Batch scoring | Airflow DAG | 이미 구현된 daily refresh와 자연스럽게 연결된다. |
| Explainability | permutation importance / SHAP optional | 비개발자에게 모델 원리 설명 역량을 보여준다. |
| Model registry style | Postgres `features.model_runs` or MLflow | 포트폴리오에서는 lightweight registry가 충분하다. |

## 5. 지금 당장 하지 않는 것이 좋은 것

- **Kubernetes/EKS부터 시작**: JD에는 K8s가 우대사항이지만, 현재 프로젝트의 핵심 증거는 데이터/ML/Agent다. K8s는 운영 복잡도가 커서 지금 붙이면 본질이 흐려질 수 있다.
- **실시간 스트리밍을 억지로 붙이기**: LINE JD에는 streaming이 있지만 현재 AdInsight의 campaign ROAS는 daily batch가 더 자연스럽다. 스트리밍은 payment event ingestion 확장안으로 문서화하고, 실제 구현은 뒤로 미룬다.
- **SageMaker endpoint부터 붙이기**: 아직 model v1이 baseline 수준이다. 먼저 local FastAPI endpoint와 model metrics를 만든 뒤 managed serving으로 대응시키는 편이 좋다.
- **클라우드 전체 배포**: 비용과 운영 부담이 크다. 우선 architecture mapping, Docker/IaC skeleton, local reproducibility를 우선한다.

## 6. 추천 다음 작업 순서

### Step 1 — Text2SQL campaign ROI eval 확장

파일 후보:
- `agent/eval/text2sql_questions.yml`
- `docs/analysis/stage4_text2sql_eval_questions.md`

목표:
- `ai_native.ai_campaign_roi_summary`
- `marts.mart_campaign_roas_prediction_monitor`

질문 예:
- ROAS가 가장 높은 캠페인 5개는?
- 예측 오차가 가장 큰 campaign은?
- objective별 평균 actual ROAS와 predicted ROAS 차이는?
- conversion campaign 중 예측보다 실제 ROAS가 높은 campaign은?

JD 연결:
- LLM Agent Development
- AI를 활용한 데이터 분석 서비스
- SQL/Python 기반 분석

### Step 2 — ML model v1 추가

파일 후보:
- `agent/eval/run_campaign_roas_model.py`
- `features.model_runs` 또는 `metrics/model_metrics.jsonl`

목표:
- baseline objective mean vs sklearn regression 비교
- MAE/RMSE/bias 기록
- 모델이 baseline보다 못하면 그 결과도 정직하게 문서화

JD 연결:
- Feature 개발 및 ML/DL modeling
- MLOps 관련 업무 경험
- 비개발 직군도 이해할 수 있는 모델 설명

### Step 3 — FastAPI serving skeleton

파일 후보:
- `api/main.py`
- `api/schemas.py`
- `docker-compose.yml` service 추가

엔드포인트 후보:
- `GET /health`
- `POST /predict/campaign-roas`
- `POST /query/text2sql` 또는 이후 단계에서 추가

JD 연결:
- 데이터 서빙 API 연동 개발
- AI/ML 모델 프로덕션 서빙
- 고가용성 API 설계의 로컬 축소판

### Step 4 — AWS architecture mapping / IaC skeleton

파일 후보:
- `docs/architecture/aws_target_architecture.md`
- `infra/aws/README.md`
- optional: Terraform skeleton

목표:
- 현재 local service와 AWS managed service 대응표 작성
- 비용 통제 때문에 실제 apply는 하지 않아도 된다.

JD 연결:
- AWS 기반 데이터 플랫폼 구축 경험
- Docker/K8s 기반 데이터 파이프라인 운영 이해

## 7. 한 줄 포트폴리오 메시지

> 로컬 Docker 기반 Airflow/Postgres/dbt/Superset 스택에서 인플루언서 광고 campaign 데이터를 수집·정제·mart화하고, ROAS baseline prediction을 daily Airflow DAG로 갱신하며, Superset에서 예측 오차를 모니터링하는 AI-native 데이터 플랫폼을 구현했다. 이 구조는 AWS에서는 MWAA + Redshift/RDS + SageMaker Processing/ECS + QuickSight + CloudWatch로 확장 가능하다.

## Known Limitations

- 현재 prediction model은 objective mean baseline이며, 실제 LightGBM/ML model은 아직 구현 전이다.
- labeled campaign row가 25개 수준이라 모델 성능 수치는 synthetic smoke benchmark로만 해석해야 한다.
- AWS managed service는 아직 실제 배포하지 않았고, 현재는 local implementation과 target architecture mapping 단계다.
- 실시간 streaming은 현재 구현 범위 밖이며, daily batch scoring이 현 도메인에 더 적합하다.
