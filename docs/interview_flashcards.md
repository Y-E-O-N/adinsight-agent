# AdInsight Interview Flashcards

이 문서는 면접 직전 10-15분 복습용입니다. 각 답변은 30-60초 안에 말할 수 있게 압축했습니다.

## 1. Project Pitch

**Q. 이 프로젝트를 한 문장으로 설명해 주세요.**

AdInsight는 인플루언서 광고 데이터를 수집해 결제 전환과 campaign ROI를 모델링하고, Superset 모니터링, ROAS 예측 API, guarded Text2SQL API까지 연결한 데이터 엔지니어링 포트폴리오 프로젝트입니다.

**Evidence**

- `README.md`
- `docs/images/00_architecture.svg`
- `docs/portfolio_one_pager.md`

## 2. End-to-End Flow

**Q. 데이터가 어디서 들어와서 어디에서 소비되나요?**

Airflow DAG가 Apify 수집과 synthetic payment generation을 실행하고, Postgres raw schema에 보존합니다. dbt가 staging, intermediate, marts, features, ai_native 레이어를 만들고, 결과는 Superset dashboard, ROAS prediction API, Text2SQL API에서 소비됩니다.

**Evidence**

- `dags/`
- `dbt/models/`
- `api/main.py`
- `text2sql_gateway/main.py`

## 3. Raw Immutability

**Q. raw 데이터를 왜 보존했나요?**

raw는 외부 입력의 원본 증거입니다. downstream 로직이 바뀌어도 raw를 보존하면 staging부터 다시 빌드할 수 있고, 수집 문제와 변환 문제를 분리해서 디버깅할 수 있습니다.

**Evidence**

- `infra/postgres/init/03_raw_schema.sql`
- `infra/postgres/init/04_synthetic_raw_schema.sql`
- `dbt/models/staging/_sources.yml`

## 4. dbt Layering

**Q. 왜 dbt 레이어를 여러 단계로 나눴나요?**

staging은 타입과 명명 정리, intermediate는 재사용 가능한 계산, marts는 BI-facing grain, features는 ML 입력, ai_native는 Text2SQL 친화 semantic layer입니다. 레이어를 나누면 각 모델의 책임과 검증 기준이 명확해집니다.

**Evidence**

- `dbt/models/staging/`
- `dbt/models/intermediate/`
- `dbt/models/features/`
- `dbt/models/ai_native/`

## 5. Synthetic Payment Data

**Q. 왜 합성 결제 데이터를 썼나요?**

실제 광고 결제 데이터는 민감하고 공개 포트폴리오에 쓰기 어렵습니다. 그래서 observed engagement를 기반으로 synthetic attribution/payment events를 만들었고, 모든 ROAS 수치는 synthetic benchmark라고 명시했습니다.

**Evidence**

- `data_generation/`
- `docs/portfolio_draft.md`
- `docs/interview_talking_points.md`

## 6. ROAS Model Choice

**Q. 왜 복잡한 ML 모델이 아니라 NumPy linear model을 선택했나요?**

현재 labeled campaign row가 25개뿐이라 복잡한 boosting model 성능을 주장하면 과장입니다. 그래서 leave-one-out으로 baseline, linear, ridge, KNN을 비교했고, 가장 방어 가능한 `linear_regression_numpy_v1` artifact를 serving했습니다.

**Evidence**

- Baseline MAE `0.0892`
- Best MAE `0.0474`
- `agent/eval/run_campaign_roas_model.py`
- `agent/model_artifacts/campaign_roas_linear_v1.json`

## 7. Artifact-Backed Serving

**Q. API에서 모델을 어떻게 서빙하나요?**

`/predict/campaign-roas`는 요청 때마다 모델을 다시 학습하지 않고 저장된 JSON artifact를 로드합니다. 응답에는 model name, training rows, feature source, artifact path, known limitation을 함께 반환해 재현성과 한계를 드러냅니다.

**Evidence**

- `api/main.py`
- `api/schemas.py`
- `agent/model_artifacts/campaign_roas_linear_v1.json`

## 8. Text2SQL v1

**Q. deterministic `/query`는 왜 만들었나요?**

LLM-generated SQL을 붙이기 전에 expected-SQL registry, SELECT-only execution, response format, latency reporting이 동작하는지 검증하기 위한 안전 baseline입니다. 현재 expected-SQL registry는 `24/24 PASS`입니다.

**Evidence**

- `agent/eval/text2sql_questions.yml`
- `agent/text2sql/registry.py`
- `agent/eval/run_expected_sql.py`

## 9. Text2SQL v2 Guardrails

**Q. generated SQL hallucination은 어떻게 막았나요?**

`/query/v2`는 provider가 만든 SQL을 바로 실행하지 않습니다. provider contract, table/column allowlist, SELECT/WITH 제한, statement timeout, negative eval, audit logging을 통과해야 실행됩니다.

**Evidence**

- `agent/text2sql/validator.py`
- `agent/text2sql/generator.py`
- `agent/eval/run_text2sql_negative_eval.py`
- `tests/unit/test_text2sql_v2.py`

## 10. Provider Fallback

**Q. 왜 Gemini primary + OpenAI fallback인가요?**

같은 38-case eval scope에서 Gemini 비용은 `$0.064098`, OpenAI 비용은 `$0.103027`로 Gemini가 더 저렴했습니다. 반면 OpenAI는 negative safety `14/14 PASS`로 Gemini `12/14 PASS`보다 안정적이라, ADR 004에서 Gemini primary + OpenAI fallback으로 결정했습니다.

**Evidence**

- `docs/adr/004-text2sql-dual-provider-fallback.md`
- `docs/analysis/stage6_text2sql_after_fixes_eval_report.md`
- `docs/api/query_v2_request_response_examples.md`

## 11. Observability

**Q. LLM/API 운영성을 어떻게 보여줬나요?**

`/query/v2` response와 audit log에 `provider_summary`를 넣었습니다. final provider, model, estimated cost, provider elapsed time, cached input ratio, fallback status, fallback reason을 request 단위로 볼 수 있습니다.

**Evidence**

- `agent/text2sql/audit.py`
- `agent/eval/summarize_text2sql_audit.py`
- `docs/analysis/stage6_text2sql_demo_evidence.md`

## 12. Quality Gates

**Q. 품질 관리는 어떻게 했나요?**

Python code는 `ruff`와 `pytest`를 GitHub Actions에서 돌립니다. Text2SQL은 positive expected-SQL set과 negative/content-safety set을 분리했고, latest documented gate는 `ruff` pass, `pytest 82 passed`, `git diff --check` pass입니다.

**Evidence**

- `.github/workflows/ci.yml`
- `tests/unit/`
- `agent/eval/text2sql_questions.yml`
- `agent/eval/text2sql_negative_questions.yml`

## 13. AWS Migration

**Q. 이걸 AWS로 옮기면 어떻게 설계하나요?**

Airflow는 MWAA, Postgres는 RDS/Aurora 또는 Redshift, artifact는 S3, FastAPI는 ECS Fargate + ALB, 로그는 CloudWatch, BI는 QuickSight 또는 managed Superset으로 옮깁니다. Text2SQL gateway는 Bedrock/OpenAI/Gemini/internal model gateway 뒤에 둘 수 있습니다.

**Evidence**

- `docs/architecture/aws_target_architecture.md`
- `infra/aws/README.md`

## 14. Limitations

**Q. 이 프로젝트의 가장 큰 한계는 무엇인가요?**

첫째, 결제와 ROAS label은 synthetic benchmark입니다. 둘째, 모델 학습 row가 25개라 production forecasting claim은 하지 않습니다. 셋째, AWS는 target architecture까지만 정리했고 실제 배포는 하지 않았습니다.

**Evidence**

- `README.md`
- `docs/portfolio_draft.md`
- `docs/portfolio_one_pager.md`

## 15. Next Improvement

**Q. 다음으로 개선한다면 무엇을 하겠나요?**

반복 dual-provider smoke set을 실행해 fallback rate, p95 latency, cost distribution을 더 크게 측정하겠습니다. 그다음 auth, rate limit, tenant boundary를 붙여 `/query/v2`를 운영 API에 가깝게 hardening하겠습니다.

**Evidence**

- `agent/eval/summarize_text2sql_audit.py`
- `docs/adr/004-text2sql-dual-provider-fallback.md`
