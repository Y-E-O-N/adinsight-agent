# AdInsight Agent - 한국 기업 데이터 엔지니어 제출용 포트폴리오

> 권장 제출 형태: 이 문서를 PDF로 export하고, 지원서에는 `README.md` GitHub URL과 데모 GIF/증거 문서 링크를 함께 첨부한다.
> 현재 HTML export: `docs/adinsight_portfolio_submission_ko.html`
> 현재 DOCX export: `docs/adinsight_portfolio_submission_ko.docx`
> PDF export는 로컬에 `pdflatex` 또는 다른 pandoc PDF engine이 필요하다.

---

## 0. 30초 요약

| 항목 | 내용 |
|---|---|
| 프로젝트 기간 | 2026.04 - 2026.07 |
| 프로젝트 형태 | 처음부터 끝까지 혼자 진행한 개인 포트폴리오 프로젝트 |
| 담당 범위 | 데이터 수집, raw schema, dbt 모델링, Airflow DAG, Superset dashboard, ROAS model comparison, FastAPI serving, Text2SQL validator/gateway/eval, CI, 제출 문서화 |
| 핵심 기술 | Python, SQL, Airflow, PostgreSQL, dbt, Superset, FastAPI, GitHub Actions, OpenAI/Gemini gateway |
| 핵심 성과 1 | Airflow daily adaptive run 1회에서 `1,725`건 수집, `1,410`건 신규 적재 |
| 핵심 성과 2 | ROAS benchmark model MAE를 baseline `0.0892`에서 linear model `0.0474`로 개선하고 FastAPI artifact serving 구현 |
| 핵심 성과 3 | Text2SQL v2에 SQL validator, timeout, audit, provider fallback을 붙이고 OpenAI `24/24 + 14/14`, Gemini `24/24 + 12/14` eval 결과 확보 |

한 줄 요약:

> 인플루언서 광고 수집 데이터를 결제 전환과 campaign ROI 관점으로 모델링하고, Airflow/dbt 기반 데이터 파이프라인부터 Superset, FastAPI, Text2SQL gateway까지 연결한 개인 데이터 엔지니어링 프로젝트입니다.

---

## 0. 제출 패키지

한국 기업 데이터 엔지니어 포지션 기준으로는 아래 3개를 함께 제출하는 구성이 가장 안전하다.

| 제출물 | 용도 | AdInsight 위치 |
|---|---|---|
| 이력서 PDF | 채용 담당자 1차 스크리닝 | `docs/resume_selected_bullets_ko.md` |
| 포트폴리오 PDF | 프로젝트 깊이와 역할 설명 | 현재 문서 |
| 포트폴리오 HTML | PDF export 전 미리보기/인쇄용 | `docs/adinsight_portfolio_submission_ko.html` |
| 포트폴리오 DOCX | 채용 플랫폼 첨부 또는 PDF 변환용 | `docs/adinsight_portfolio_submission_ko.docx` |
| GitHub 저장소 | 코드, 실행 방법, 증거 확인 | `README.md` |

추가 링크:

- 데모 GIF: `docs/images/06_text2sql_demo.gif`
- 3-5분 데모 스크립트: `docs/demo_script_3min.md`
- 지원서 입력란용 문구: `docs/korean_job_application_snippets.md`
- 이력서 최종 bullet: `docs/resume_selected_bullets_ko.md`
- 면접 복습 카드: `docs/interview_flashcards.md`

---

## 1. 프로젝트 한 줄 소개

**AdInsight Agent**는 인플루언서 광고 데이터를 수집하고, 합성 결제 전환 이벤트를 결합해 campaign ROI와 ROAS를 분석하며, Superset dashboard, FastAPI serving, guarded Text2SQL API까지 연결한 데이터 엔지니어링 포트폴리오 프로젝트입니다.

이 프로젝트는 팀 프로젝트가 아니라 **기획, 설계, 구현, 검증, 문서화까지 처음부터 끝까지 혼자 진행한 개인 프로젝트**입니다. 따라서 아래 산출물의 담당 범위는 별도 표기가 없는 한 모두 본인이 직접 수행한 범위입니다.

핵심 흐름:

```text
Airflow ingestion
  -> Postgres raw/staging
  -> dbt intermediate/marts/features/ai_native
  -> Superset dashboard
  -> ROAS model artifact
  -> FastAPI serving
  -> Text2SQL gateway/eval/audit
```

---

## 2. 지원 직무 매칭

데이터 엔지니어 지원용 문서이므로, 핵심 강조점은 LLM 자체가 아니라 **수집-적재-모델링-품질-서빙으로 이어지는 데이터 제품화 흐름**입니다. Text2SQL은 이 데이터 플랫폼 위에 붙인 소비 인터페이스이자 운영/검증 경계로 설명합니다.

| 데이터 엔지니어 요구 역량 | 구현 증거 |
|---|---|
| 데이터 수집/적재 파이프라인 | Apify collector, raw loader, Airflow daily/backfill DAG |
| 데이터 웨어하우스 모델링 | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` |
| 데이터 품질 관리 | dbt tests, idempotency check, expected-SQL baseline |
| BI/분석 서빙 | Superset creator review dashboard, campaign ROAS prediction monitor |
| API 기반 데이터 서빙 | FastAPI `/predict/campaign-roas`, `/query`, `/query/v2` |
| 운영/관측성 | CI, audit JSONL, provider cost/latency/fallback reason |
| 클라우드 전환 사고 | MWAA, RDS/Aurora, S3, ECS Fargate, CloudWatch, QuickSight mapping |
| AI/LLM 데이터 인터페이스 | Text2SQL validator, gateway, 정답형/안전성 질의 평가 |

---

## 3. 내가 직접 구현한 범위

| 범위 | 직접 구현한 내용 |
|---|---|
| 데이터 수집 | Apify 기반 Instagram 수집 함수, Airflow smoke/daily/backfill DAG |
| 저장/적재 | PostgreSQL raw schema, source lineage table, upsert/load flow |
| 변환/모델링 | dbt staging, intermediate, marts, features, ai_native 레이어 |
| 분석/BI | Superset dataset, chart, dashboard, export, screenshot evidence |
| ML workflow | ROAS feature table, model comparison, model artifact export |
| API serving | FastAPI `/health`, `/predict/campaign-roas`, `/query`, `/query/v2` |
| Text2SQL safety | expected-SQL registry, SQL validator, statement timeout, 안전성 질의 평가, audit log |
| Provider gateway | mock/Ollama/OpenAI/Gemini/dual fallback gateway boundary |
| 품질/운영 | GitHub Actions CI, `ruff`, `pytest`, portfolio metric/evidence 문서화 |
| 제출 자산 | README, 영문 README, 한국 기업 제출용 문서, DOCX/HTML export, 이력서 bullet, 면접 flashcards |

---

## 4. 담당 역할과 문제 정의

### 문제

인플루언서 광고 성과는 게시물 반응, 캠페인 attribution, 결제 전환, ROAS 지표가 분리되어 있어 “어떤 캠페인이 성과가 좋았는지”를 빠르게 판단하기 어렵다.

### 내가 설계한 해결 방식

1. Instagram 수집 데이터를 raw schema에 보존한다.
2. 결제 데이터는 공개 포트폴리오에 실제 데이터를 사용할 수 없으므로 synthetic payment benchmark로 만든다.
3. dbt로 campaign-grain ROI mart와 feature table을 만든다.
4. Superset dashboard와 FastAPI endpoint로 소비 경로를 만든다.
5. 데이터 소비 인터페이스로 Text2SQL API를 붙이되, generated SQL은 validator와 audit boundary를 통과해야만 실행한다.

### 주요 의사결정

| 결정 | 이유 |
|---|---|
| raw 원본 보존 | 재빌드, 감사, 디버깅이 가능하도록 변환을 staging 이후로 제한 |
| layered dbt 모델 | 각 레이어의 책임과 grain을 분리 |
| synthetic payment 명시 | 민감한 결제 데이터를 공개 포트폴리오에 쓰지 않기 위함 |
| 단순 ROAS 모델 우선 | labeled row가 25개라 복잡한 모델 성능 주장을 피함 |
| `/query`와 `/query/v2` 분리 | 안정 baseline과 generated-SQL 실험 경로를 분리 |

---

## 5. 시스템 아키텍처

```text
[Ingestion]
  Airflow DAGs + Apify collector + synthetic payment generator
      |
      v
[Storage]
  Postgres schemas: raw -> staging -> intermediate -> marts -> features -> ai_native
      |
      +--> Superset dashboard
      +--> ROAS model comparison/scoring
      +--> FastAPI /predict/campaign-roas
      +--> FastAPI /query and /query/v2
              |
              v
          Text2SQL gateway: mock | Ollama | OpenAI | Gemini | dual fallback
```

시각 자료:

- `docs/images/00_architecture.svg`
- `docs/images/03_dbt_lineage.png`
- `docs/images/05_campaign_roas_prediction_monitor.png`

---

## 6. 데이터 모델링

### dbt 레이어

| Layer | 역할 | 대표 모델 |
|---|---|---|
| raw | 외부 입력 원본 보존 | `raw.ig_posts`, `raw.syn_payment_events` |
| staging | 타입/명명/기본 정제 | `stg_ig_posts`, `stg_syn_payment_events` |
| intermediate | 재사용 가능한 계산 | `int_campaign_payment_performance` |
| marts | BI-facing 지표 | `mart_campaign_roi_summary`, `mart_campaign_roas_prediction_monitor` |
| features | ML 학습/스코어링 입력 | `feature_campaign_roas_training_set`, `feature_campaign_roas_scoring_set` |
| ai_native | Text2SQL 친화 semantic mart | `ai_campaign_roi_summary` |

### 핵심 grain

| 모델 | Grain |
|---|---|
| `mart_campaign_roi_summary` | 1 row = 1 campaign |
| `mart_campaign_roas_prediction_monitor` | 1 row = 1 campaign scoring snapshot |
| `ai_campaign_roi_summary` | 1 row = 1 campaign, Text2SQL-friendly semantic view |

---

## 7. 파이프라인과 품질 관리

| 항목 | 구현 |
|---|---|
| 수집 | Apify collector + Airflow DAG |
| 적재 | Postgres raw schema upsert/load |
| 백필 | Airflow backfill DAG and idempotency check |
| 변환 | dbt run/test |
| 스코어링 | daily ROAS prediction DAG |
| API 테스트 | FastAPI unit tests |
| Text2SQL 평가 | 정답형 질의 set + 안전성 질의 set |
| CI | GitHub Actions `ruff` + `pytest` |

최신 문서화된 품질 게이트:

- `ruff` pass
- `pytest 82 passed`
- `git diff --check` pass

---

## 8. 주요 성과 지표

| 영역 | 결과 |
|---|---:|
| Phase 2B daily adaptive run | `1,725`건 수집, `1,410`건 신규 적재 |
| Synthetic payment benchmark | `498` payment events |
| Synthetic net payment | KRW `6,329,923.59` |
| Campaign ROI mart | `30` campaign rows, max ROAS `0.5969` |
| Prediction monitor | `25` rows, MAE `0.0799`, bias `0.0000` |
| ROAS model comparison | baseline MAE `0.0892` -> linear model MAE `0.0474` |
| deterministic Text2SQL baseline | expected-SQL registry `24/24 PASS` |
| OpenAI Text2SQL eval | 정답형 `24/24`, 안전성 `14/14` |
| Gemini Text2SQL eval | 정답형 `24/24`, 안전성 `12/14` |
| Provider cost comparison | Gemini `$0.064098` vs OpenAI `$0.103027` over 38 cases |

### 채용자 관점의 해석

| 성과 지표 | 채용자가 이해할 수 있는 의미 |
|---|---|
| `1,725`건 수집, `1,410`건 신규 적재 | Airflow daily DAG가 실제 수집 작업을 수행하고, 신규 데이터와 기존 데이터를 구분해 적재한 증거 |
| synthetic payment `498` events | 실제 결제 데이터를 공개하지 않고도 campaign ROI mart, feature table, prediction monitor를 검증할 수 있는 benchmark 데이터셋을 만든 것 |
| campaign ROI mart `30` rows | 캠페인 단위 grain을 명확히 정의해 BI와 API가 같은 지표를 보도록 만든 것 |
| prediction monitor MAE `0.0799`, bias `0.0000` | 모델 예측 결과를 dashboard에서 운영 지표처럼 모니터링할 수 있게 만든 것 |
| ROAS MAE `0.0892 -> 0.0474` | 단순 baseline보다 나은 benchmark model을 고르고, 그 결과를 artifact로 저장해 API serving까지 연결한 것 |
| expected-SQL `24/24 PASS` | 자연어 질문을 검증된 SQL 기준선으로 평가할 수 있는 regression baseline을 만든 것 |
| OpenAI/Gemini eval 결과 | LLM을 단순 호출하지 않고 provider별 정확도, 안전성, 비용 차이를 같은 기준으로 비교한 것 |
| provider cost comparison | 모델 선택을 감이 아니라 request-level cost/latency 관측값으로 설명할 수 있게 만든 것 |

---

## 9. API와 Text2SQL

### FastAPI endpoints

| Endpoint | 목적 |
|---|---|
| `GET /health` | API health check |
| `POST /predict/campaign-roas` | campaign ROAS prediction serving |
| `POST /query` | deterministic expected-SQL query |
| `POST /query/v2` | generated-SQL Text2SQL boundary |

이 섹션은 데이터 엔지니어링 본체라기보다 **모델링된 데이터를 어떻게 안전하게 소비하게 만들었는지**를 보여주는 확장 영역입니다. 핵심 구현은 generated SQL을 무조건 신뢰하지 않고, 데이터 플랫폼의 table/column contract와 validator를 통해 통제하는 점입니다.

### Text2SQL guardrails

`/query/v2`는 provider가 만든 SQL을 바로 실행하지 않는다. 아래 boundary를 통과해야 한다.

1. provider response contract
2. approved table/column allowlist
3. SELECT/WITH only
4. statement timeout
5. negative/content-safety eval
6. audit logging
7. fallback reason tracking

### Provider strategy

| Provider | 역할 | 근거 |
|---|---|---|
| Gemini | primary | 같은 38-case scope에서 비용이 더 낮음 |
| OpenAI | fallback | 안전성 질의 평가와 속도가 더 안정적 |
| deterministic registry | final fallback | curated question에 대해 안정적인 demo path 제공 |

---

## 10. 트러블슈팅과 설계 학습

| 이슈 | 대응 |
|---|---|
| small labeled data | 복잡한 모델 성능 주장을 피하고 leave-one-out simple model 비교로 제한 |
| generated SQL hallucination | validator, allowlist, timeout, refusal, 안전성 질의 평가 추가 |
| provider별 응답 shape 차이 | gateway adapter boundary로 분리 |
| LLM 비용/속도 비교 어려움 | request-level `provider_summary`와 audit summary CLI 추가 |
| synthetic data 과장 위험 | README와 포트폴리오 문서에 claim boundary 명시 |

---

## 11. 한계와 후속 개선

### 한계

- 결제/ROAS label은 synthetic benchmark다.
- ROAS model은 25 synthetic labeled campaign rows 기반이라 production forecasting claim을 하지 않는다.
- AWS 문서는 target architecture와 skeleton boundary이며 실제 배포는 아니다.
- `/query/v2`는 validation과 fallback을 갖췄지만, 운영 API로 쓰려면 auth, rate limit, tenant boundary, larger traffic measurement가 필요하다.

### 후속 개선

1. repeated dual-provider smoke set으로 fallback rate, p95 latency, cost distribution 측정
2. `/query/v2` auth/rate limit/tenant boundary 추가
3. 더 큰 synthetic 또는 공개 benchmark dataset으로 ROAS model 재평가
4. query optimization before/after EXPLAIN study 추가
5. README 기반 PDF export 자동화

---

## 12. 면접 질문 유도 포인트

면접관이 아래 질문을 던지면, 이 프로젝트의 설계 의도를 가장 잘 설명할 수 있습니다.

| 예상 질문 | 답변 방향 |
|---|---|
| 왜 raw 데이터를 그대로 보존했나요? | raw는 외부 입력 증거이고, downstream 로직 변경 시 staging 이후를 재빌드할 수 있기 때문입니다. |
| 왜 합성 결제 데이터를 사용했나요? | 실제 결제 데이터는 민감하므로 공개 포트폴리오에서는 synthetic benchmark로 pipeline/modeling/serving pattern을 검증했습니다. |
| 왜 복잡한 모델 대신 simple model을 썼나요? | labeled row가 25개뿐이라 복잡한 모델 성능을 주장하는 것보다 leave-one-out simple model 비교가 더 방어 가능했습니다. |
| dbt 모델 grain은 어떻게 정했나요? | campaign ROI는 campaign grain, prediction monitor는 campaign scoring snapshot grain으로 분리해 BI/API 해석이 흔들리지 않게 했습니다. |
| generated SQL hallucination은 어떻게 막았나요? | `/query` baseline, `/query/v2` validator, table/column allowlist, timeout, 안전성 질의 평가, audit log로 실행 경계를 만들었습니다. |
| AWS로 옮긴다면 무엇이 바뀌나요? | Airflow는 MWAA, Postgres는 RDS/Aurora 또는 Redshift, FastAPI는 ECS Fargate + ALB, logs는 CloudWatch로 대응합니다. |

---

## 13. 제출 시 요약 문장

지원서 프로젝트 설명란에는 아래 문장을 사용한다.

> Airflow, Postgres, dbt, Superset, FastAPI로 인플루언서 광고 수집 데이터와 합성 결제 이벤트를 campaign ROI/ROAS 분석 플랫폼으로 모델링했습니다. ROAS model comparison과 artifact-backed serving을 구현했고, Text2SQL API는 expected-SQL baseline, SQL validator, provider gateway, OpenAI/Gemini fallback, request-level cost/latency observability까지 포함해 평가했습니다.

---

## 14. 조사 기준

이 문서 형식은 아래 기준을 반영했다.

- 한국 기업 지원서에서는 이력서/자기소개서/포트폴리오를 PDF로 첨부하는 사례가 많으므로, PDF export 가능한 Markdown 문서로 구성한다.
- 채용 담당자는 성과, 액션, 사용 기술을 빠르게 확인하므로 각 섹션을 숫자/역할/도구 중심으로 작성한다.
- 개발 과제나 프로젝트 검토에서는 GitHub 저장소, README, 실행 가능성, 디렉토리 구조, 최종 결과물을 확인하는 흐름이 많으므로 README와 실행 링크를 별도로 둔다.
- README는 목적, 기능, 기술, 구조, 실행 방법, 직접 구현한 부분, 한계, 확장 방향을 빠르게 답해야 한다.

참고:

- Wanted resume article: `https://blog.wantedlab.com/library/insight/resume-tip2`
- Wanted job posting PDF note: `https://www.wanted.co.kr/wd/20972`
- Programmers assignment review flow: `https://prgms.tistory.com/16`
- README portfolio guide: `https://wikidocs.net/346435`
