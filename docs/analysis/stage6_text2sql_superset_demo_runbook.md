# Stage 6 Text2SQL + Superset Demo Runbook

## Purpose

Superset campaign ROAS dashboard와 FastAPI Text2SQL API를 하나의 데모 흐름으로 연결한다.

이 런북의 목적은 "자연어가 곧바로 임의 SQL을 만든다"는 단순 주장을 하는 것이 아니다. 데모는 두 층으로 나뉜다.

1. `/query`: 검증된 expected-SQL registry를 사용하는 deterministic Text2SQL v1.
2. `/query/v2`: OpenAI/Gemini gateway를 붙일 수 있는 generated-SQL boundary. SQL validator, timeout, audit log, usage/cost tracking, `provider_summary`를 통해 운영 가능한 self-service analytics 경계를 보여준다.

## Demo Story

면접/포트폴리오 데모에서 사용할 한 문장:

> "Superset은 운영자가 반복적으로 보는 ROAS monitoring 화면이고, Text2SQL API는 같은 mart를 자연어 질문으로 조회하는 self-service analytics layer입니다. `/query`는 안정적인 deterministic baseline이고, `/query/v2`는 provider, SQL validation, cost, latency, cache ratio까지 감사 가능한 generated-SQL serving boundary입니다."

데모 순서:

1. Superset `AdInsight Campaign ROAS Prediction Monitor` dashboard를 연다.
2. prediction error가 큰 campaign과 최신 모델 MAE/bias를 확인한다.
3. FastAPI `/query`에 같은 분석 질문을 영어/한국어로 보낸다.
4. 응답에서 `question_id`, 실행 SQL, rows, answer, latency를 확인한다.
5. `/query/v2`를 호출해 generated-SQL path의 `mode`, `sql`, `validation_tables`, `provider_summary`를 확인한다.
6. safety refusal 예시로 Gemini primary -> OpenAI fallback이 audit에 남는 것을 보여준다.
7. 한계를 명시한다: v2는 validator와 provider fallback을 갖춘 serving boundary이지만, 반복 운영 traffic에서의 fallback rate와 p95 latency는 더 쌓아야 한다.

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

Generated-SQL v2 질문:

```bash
curl -s -X POST http://127.0.0.1:8000/query/v2 \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which campaigns have the highest ROAS?"}'
```

데모에서 확인할 포인트:

- `mode`: `llm_generated_sql_v2_mock` 또는 `llm_generated_sql_v2_http_json`
- `sql`: provider가 생성하고 validator를 통과한 SQL
- `validation_tables`: 실행 허용된 semantic mart
- `validation_limit`: broad list query 방지용 LIMIT
- `usage`: provider raw token/cost payload
- `provider_summary.final_provider`: `gemini`, `openai`, `deterministic_registry` 등
- `provider_summary.estimated_cost_usd`: 요청 단위 추정 비용
- `provider_summary.provider_elapsed_ms`: provider 호출 시간
- `provider_summary.cached_input_ratio`: cached input token 비율
- `provider_summary.fallback_used`: provider fallback 발생 여부
- `provider_summary.fallback_reason`: fallback을 유발한 원인

v2 external-provider 최신 비교:

| Provider | Positive/Negative 결과 | Estimated cost | Provider elapsed |
|---|---:|---:|---:|
| Gemini `gemini-3.1-flash-lite` | 36/38 pass | `$0.064098` | 145.363 s |
| OpenAI `gpt-5.4-mini-2026-03-17` | 38/38 pass | `$0.103027` | 124.799 s |

해석:

- Gemini는 OpenAI 대비 약 37.8% 저렴했다.
- OpenAI는 total provider elapsed 기준 약 16.5% 빨랐다.
- `/query/v2`의 `provider_summary`는 이 비교를 실제 request/audit 단위로 확인하기 위한 API contract다.

Dual-provider live smoke:

| Scenario | Result | Provider summary |
|---|---|---|
| Positive primary success | HTTP `200`, rows `5`, top campaign `camp_000029` | final provider `gemini`, fallback `false`, cost `$0.0014719`, provider elapsed `4672.489ms` |
| Safety fallback refusal | HTTP `404` neutral refusal | final provider `openai`, fallback `true`, attempts `gemini -> openai`, reason `primary_content_safety_refusal`, cost `$0.0067335` |

## Guardrails

현재 `/query`의 안전장치:

- 질문은 `agent/eval/text2sql_questions.yml`의 curated question과 정확히 매칭된다.
- SQL은 `SELECT`로 시작해야 한다.
- `insert`, `update`, `delete`, `drop`, `alter`, `truncate`, `create`, `grant`, `revoke`, `copy` token은 차단한다.
- 결과는 최대 50 rows만 반환한다.

현재 `/query/v2`의 안전장치:

- provider가 반환한 SQL은 allowlisted table만 참조해야 한다.
- `SELECT` 또는 `WITH` statement만 허용한다.
- non-aggregate broad query에는 명시적 `LIMIT`가 필요하다.
- validator 실패, provider refusal, provider error는 audit에 남기고 curated registry fallback이 가능하면 deterministic response로 전환한다.
- 응답과 audit에는 `usage`, `usage_attempts`, `provider_summary`를 남겨 비용과 latency를 추적한다.

이 구조의 의미:

- 장점: hallucination과 destructive SQL 위험을 낮춘다.
- 단점: registry에 없는 자유형 질문에는 답하지 못한다.
- 다음 단계: LLM SQL generation을 붙이더라도 이 registry/evaluator를 regression baseline으로 유지한다.

## Local vs AWS Mapping

| Local implementation | AWS managed-service equivalent |
|---|---|
| Superset dashboard | Amazon QuickSight dashboard |
| FastAPI `/query` | ECS/Fargate or Lambda container behind ALB/API Gateway |
| FastAPI `/query/v2` | ECS/Fargate service with provider gateway integration |
| Text2SQL gateway | Bedrock, OpenAI, Gemini, or internal model gateway behind private endpoint |
| Postgres marts | Aurora PostgreSQL or Redshift |
| `text2sql_questions.yml` registry | S3/versioned prompt-eval artifact or DynamoDB registry |
| expected-SQL evaluator | CI job or SageMaker Processing validation step |
| `logs/text2sql_audit.jsonl` / `metrics/run_results.jsonl` | CloudWatch metrics, S3 audit log, or OpenSearch log index |

## Demo Script

1. "먼저 Superset에서 최신 ROAS prediction monitor를 봅니다. 이 화면은 모델 성능을 과장하기보다, campaign별 예측 오차를 운영자가 보는 용도입니다."
2. "같은 mart를 자연어 API로도 조회할 수 있습니다. 영어 질문은 campaign ROI summary mart로 매칭됩니다."
3. "한국어 질문은 prediction monitor mart로 매칭되고, 최신 snapshot의 MAE와 bias를 집계합니다."
4. "응답에는 SQL과 rows를 같이 반환합니다. 데모에서는 black-box agent가 아니라 어떤 SQL이 실행됐는지 보여주는 것이 핵심입니다."
5. "이제 `/query/v2`도 보여줍니다. v2는 Gemini/OpenAI gateway를 붙일 수 있고, 결과에는 provider, model, cost, latency, cache ratio가 `provider_summary`로 남습니다."
6. "즉 이 프로젝트의 Text2SQL은 모델 성능만 말하는 것이 아니라, 검증과 운영 관측성까지 포함한 serving boundary입니다."

## Evidence

- Functional commit: `848bd27 Add deterministic Text2SQL query API`
- API tests: `uv run pytest -q` -> `4 passed`
- Lint: `ruff check` -> pass
- Expected-SQL evaluator: `18/18 PASS`
- Latest expected-SQL deterministic baseline after eval expansion: `24/24 PASS`
- External provider eval after hardening: OpenAI positive/negative `38/38 PASS`, Gemini positive/negative `36/38 PASS`
- Cost comparison: Gemini `$0.064098`, OpenAI `$0.103027` over 38 positive/negative cases
- Metrics row: `metrics/run_results.jsonl` step `text2sql_query_api_v1_smoke`
- Latest demo evidence: `docs/analysis/stage6_text2sql_demo_evidence.md`
- Demo GIF artifact: `docs/images/06_text2sql_demo.gif`

## Demo Artifact

- `docs/images/06_text2sql_demo.gif`
  - Superset monitor role
  - `/query` English result
  - `/query` Korean result
  - deterministic v1 guardrail
  - `/query/v2` provider-summary frame
  - Gemini/OpenAI cost-comparison frame
- Generator: `dashboards/scripts/create_text2sql_demo_gif.sh`
- The GIF is terminal-style rather than a live browser recording. The source evidence for v2 provider-summary is documented in `docs/analysis/stage6_text2sql_demo_evidence.md` and `docs/api/query_v2_request_response_examples.md`.
