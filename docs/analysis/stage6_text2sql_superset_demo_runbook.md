# Stage 6 Text2SQL + Superset Demo Runbook

## Purpose

Superset campaign ROAS dashboard와 FastAPI `/query`를 하나의 데모 흐름으로 연결한다.

이 런북의 목적은 "자연어가 곧바로 임의 SQL을 만든다"는 주장을 하는 것이 아니다. 현재 구현은 검증된 expected-SQL registry를 사용하는 deterministic Text2SQL v1이며, Superset에서 보이는 운영 지표를 같은 질문으로 API에서 재현할 수 있음을 보여준다.

## Demo Story

면접/포트폴리오 데모에서 사용할 한 문장:

> "Superset은 운영자가 반복적으로 보는 ROAS monitoring 화면이고, `/query`는 같은 mart를 자연어 질문으로 조회하는 self-service analytics API입니다. 현재 v1은 LLM 자유 생성이 아니라 검증된 질문 registry 기반으로 SELECT만 실행합니다."

데모 순서:

1. Superset `AdInsight Campaign ROAS Prediction Monitor` dashboard를 연다.
2. prediction error가 큰 campaign과 최신 모델 MAE/bias를 확인한다.
3. FastAPI `/query`에 같은 분석 질문을 영어/한국어로 보낸다.
4. 응답에서 `question_id`, 실행 SQL, rows, answer, latency를 확인한다.
5. 한계를 명시한다: free-form LLM SQL generation은 아직 붙이지 않았고, 이 v1은 validator baseline이다.

## Superset View

- Dashboard: `AdInsight Campaign ROAS Prediction Monitor`
- Dataset: `marts.mart_campaign_roas_prediction_monitor`
- Export: `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip`
- Screenshot: `docs/images/05_campaign_roas_prediction_monitor.png`
- Design note: `docs/analysis/stage5_campaign_roas_prediction_dashboard.md`

Superset에서 먼저 보여줄 관점:

| View | Why it matters |
|---|---|
| `absolute_roas_prediction_error` descending | 평균 성능보다 어떤 campaign에서 크게 틀렸는지 먼저 본다. |
| `predicted_roas` vs `actual_roas` | 모델 출력이 BI monitoring layer까지 연결됐는지 확인한다. |
| `prediction_reason` | 예측 결과를 운영자가 해석할 수 있는 텍스트로 노출한다. |

## Text2SQL API Calls

서버 실행:

```bash
set -a; source .env; set +a; POSTGRES_HOST=localhost uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

영어 질문:

```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

예상 포인트:

- `question_id`: `p5_q001`
- `expected_model`: `ai_native.ai_campaign_roi_summary`
- `row_count`: `5`
- live smoke latency: `41.013ms`

한국어 질문:

```bash
curl -s -X POST http://127.0.0.1:8000/query \
  -H 'Content-Type: application/json' \
  -d '{"question":"최신 ROAS 예측 모델의 MAE와 bias를 요약해줘."}'
```

예상 포인트:

- `question_id`: `p5_q008`
- `expected_model`: `marts.mart_campaign_roas_prediction_monitor`
- `row_count`: `1`
- live smoke latency: `42.839ms`

## Guardrails

현재 `/query`의 안전장치:

- 질문은 `agent/eval/text2sql_questions.yml`의 curated question과 정확히 매칭된다.
- SQL은 `SELECT`로 시작해야 한다.
- `insert`, `update`, `delete`, `drop`, `alter`, `truncate`, `create`, `grant`, `revoke`, `copy` token은 차단한다.
- 결과는 최대 50 rows만 반환한다.

이 구조의 의미:

- 장점: hallucination과 destructive SQL 위험을 낮춘다.
- 단점: registry에 없는 자유형 질문에는 답하지 못한다.
- 다음 단계: LLM SQL generation을 붙이더라도 이 registry/evaluator를 regression baseline으로 유지한다.

## Local vs AWS Mapping

| Local implementation | AWS managed-service equivalent |
|---|---|
| Superset dashboard | Amazon QuickSight dashboard |
| FastAPI `/query` | ECS/Fargate or Lambda container behind ALB/API Gateway |
| Postgres marts | Aurora PostgreSQL or Redshift |
| `text2sql_questions.yml` registry | S3/versioned prompt-eval artifact or DynamoDB registry |
| expected-SQL evaluator | CI job or SageMaker Processing validation step |
| `metrics/run_results.jsonl` | CloudWatch metrics, S3 audit log, or OpenSearch log index |

## Demo Script

1. "먼저 Superset에서 최신 ROAS prediction monitor를 봅니다. 이 화면은 모델 성능을 과장하기보다, campaign별 예측 오차를 운영자가 보는 용도입니다."
2. "같은 mart를 자연어 API로도 조회할 수 있습니다. 영어 질문은 campaign ROI summary mart로 매칭됩니다."
3. "한국어 질문은 prediction monitor mart로 매칭되고, 최신 snapshot의 MAE와 bias를 집계합니다."
4. "응답에는 SQL과 rows를 같이 반환합니다. 데모에서는 black-box agent가 아니라 어떤 SQL이 실행됐는지 보여주는 것이 핵심입니다."
5. "현재 v1은 deterministic registry 기반입니다. 다음 확장에서는 LLM generation을 붙이되, 이 expected-SQL evaluator로 회귀 검증합니다."

## Evidence

- Functional commit: `848bd27 Add deterministic Text2SQL query API`
- API tests: `uv run pytest -q` -> `4 passed`
- Lint: `ruff check` -> pass
- Expected-SQL evaluator: `18/18 PASS`
- Metrics row: `metrics/run_results.jsonl` step `text2sql_query_api_v1_smoke`
- Latest demo evidence: `docs/analysis/stage6_text2sql_demo_evidence.md`
- Demo GIF artifact: `docs/images/06_text2sql_demo.gif`

## Demo Artifact

- `docs/images/06_text2sql_demo.gif`
  - Superset monitor role
  - `/query` English result
  - `/query` Korean result
  - deterministic v1 guardrail
- Generator: `dashboards/scripts/create_text2sql_demo_gif.sh`
