# AdInsight Agent - 한국 기업 데이터 엔지니어 제출용 포트폴리오

> 권장 제출 형태: 이 문서를 PDF로 export하고, 지원서에는 `README.md` GitHub URL과 데모 GIF/증거 문서 링크를 함께 첨부한다.
> 현재 HTML export: `docs/adinsight_portfolio_submission_ko.html`
> 현재 DOCX export: `docs/adinsight_portfolio_submission_ko.docx`
> PDF export는 로컬에 `pdflatex` 또는 다른 pandoc PDF engine이 필요하다.

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

| 데이터 엔지니어 요구 역량 | 구현 증거 |
|---|---|
| 데이터 수집/적재 파이프라인 | Apify collector, raw loader, Airflow daily/backfill DAG |
| 데이터 웨어하우스 모델링 | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` |
| 데이터 품질 관리 | dbt tests, expected-SQL eval, negative Text2SQL eval |
| BI/분석 서빙 | Superset creator review dashboard, campaign ROAS prediction monitor |
| API 기반 데이터 서빙 | FastAPI `/predict/campaign-roas`, `/query`, `/query/v2` |
| ML/feature workflow 이해 | ROAS feature tables, model comparison, artifact-backed serving |
| 운영/관측성 | provider cost, latency, fallback reason, audit JSONL |
| 클라우드 전환 사고 | MWAA, RDS/Aurora, S3, ECS Fargate, CloudWatch, QuickSight mapping |

---

## 3. 담당 역할과 문제 정의

### 문제

인플루언서 광고 성과는 게시물 반응, 캠페인 attribution, 결제 전환, ROAS 지표가 분리되어 있어 “어떤 캠페인이 성과가 좋았는지”를 빠르게 판단하기 어렵다.

### 내가 설계한 해결 방식

1. Instagram 수집 데이터를 raw schema에 보존한다.
2. 결제 데이터는 공개 포트폴리오에 실제 데이터를 사용할 수 없으므로 synthetic payment benchmark로 만든다.
3. dbt로 campaign-grain ROI mart와 feature table을 만든다.
4. Superset dashboard와 FastAPI endpoint로 소비 경로를 만든다.
5. Text2SQL API를 붙이되, generated SQL은 validator와 audit boundary를 통과해야만 실행한다.

### 주요 의사결정

| 결정 | 이유 |
|---|---|
| raw 원본 보존 | 재빌드, 감사, 디버깅이 가능하도록 변환을 staging 이후로 제한 |
| layered dbt 모델 | 각 레이어의 책임과 grain을 분리 |
| synthetic payment 명시 | 민감한 결제 데이터를 공개 포트폴리오에 쓰지 않기 위함 |
| 단순 ROAS 모델 우선 | labeled row가 25개라 복잡한 모델 성능 주장을 피함 |
| `/query`와 `/query/v2` 분리 | 안정 baseline과 generated-SQL 실험 경로를 분리 |

---

## 4. 시스템 아키텍처

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

## 5. 데이터 모델링

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

## 6. 파이프라인과 품질 관리

| 항목 | 구현 |
|---|---|
| 수집 | Apify collector + Airflow DAG |
| 적재 | Postgres raw schema upsert/load |
| 백필 | Airflow backfill DAG and idempotency check |
| 변환 | dbt run/test |
| 스코어링 | daily ROAS prediction DAG |
| API 테스트 | FastAPI unit tests |
| Text2SQL 평가 | positive expected-SQL set + negative/content-safety set |
| CI | GitHub Actions `ruff` + `pytest` |

최신 문서화된 품질 게이트:

- `ruff` pass
- `pytest 82 passed`
- `git diff --check` pass

---

## 7. 주요 성과 지표

| 영역 | 결과 |
|---|---:|
| Phase 2B daily adaptive run | `items_collected_total=1725`, `inserted_total=1410` |
| Synthetic payment benchmark | `498` payment events |
| Synthetic net payment | KRW `6,329,923.59` |
| Campaign ROI mart | `30` campaign rows, max ROAS `0.5969` |
| Prediction monitor | `25` rows, MAE `0.0799`, bias `0.0000` |
| ROAS model comparison | baseline MAE `0.0892` -> linear model MAE `0.0474` |
| deterministic Text2SQL baseline | expected-SQL registry `24/24 PASS` |
| OpenAI Text2SQL eval | positive `24/24`, negative `14/14` |
| Gemini Text2SQL eval | positive `24/24`, negative `12/14` |
| Provider cost comparison | Gemini `$0.064098` vs OpenAI `$0.103027` over 38 cases |

---

## 8. API와 Text2SQL

### FastAPI endpoints

| Endpoint | 목적 |
|---|---|
| `GET /health` | API health check |
| `POST /predict/campaign-roas` | campaign ROAS prediction serving |
| `POST /query` | deterministic expected-SQL query |
| `POST /query/v2` | generated-SQL Text2SQL boundary |

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
| OpenAI | fallback | negative safety와 속도가 더 안정적 |
| deterministic registry | final fallback | curated question에 대해 안정적인 demo path 제공 |

---

## 9. 트러블슈팅과 설계 학습

| 이슈 | 대응 |
|---|---|
| small labeled data | 복잡한 모델 성능 주장을 피하고 leave-one-out simple model 비교로 제한 |
| generated SQL hallucination | validator, allowlist, timeout, refusal, negative eval 추가 |
| provider별 응답 shape 차이 | gateway adapter boundary로 분리 |
| LLM 비용/속도 비교 어려움 | request-level `provider_summary`와 audit summary CLI 추가 |
| synthetic data 과장 위험 | README와 포트폴리오 문서에 claim boundary 명시 |

---

## 10. 한계와 후속 개선

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

## 11. 제출 시 요약 문장

지원서 프로젝트 설명란에는 아래 문장을 사용한다.

> Airflow, Postgres, dbt, Superset, FastAPI로 인플루언서 광고 수집 데이터와 합성 결제 이벤트를 campaign ROI/ROAS 분석 플랫폼으로 모델링했습니다. ROAS model comparison과 artifact-backed serving을 구현했고, Text2SQL API는 expected-SQL baseline, SQL validator, provider gateway, OpenAI/Gemini fallback, request-level cost/latency observability까지 포함해 평가했습니다.

---

## 12. 조사 기준

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
