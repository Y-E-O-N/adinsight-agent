# AdInsight Agent - 한국 기업 지원서 입력란용 문구

원티드, 사람인, 잡코리아, 점핏, 회사 자체 채용폼에 바로 붙여넣기 위한 짧은 문구 모음입니다.  
숫자와 claim boundary는 `README.md`, `docs/korean_company_portfolio_submission.md`와 같은 기준을 사용합니다.

---

## 1. 프로젝트 기본 정보

| 항목 | 내용 |
|---|---|
| 프로젝트명 | AdInsight Agent |
| 진행 기간 | 2026.04 - 2026.07 |
| 형태 | 처음부터 끝까지 혼자 진행한 개인 포트폴리오 프로젝트 |
| 역할 | 데이터 수집, DB 설계, dbt 모델링, Airflow DAG, Superset dashboard, ROAS model comparison, FastAPI serving, Text2SQL eval/gateway, CI, 문서화 |
| 도메인 | 인플루언서 광고 성과 분석, campaign ROI, ROAS prediction |
| 주요 기술 | Python, SQL, Airflow, PostgreSQL, dbt, Superset, FastAPI, GitHub Actions |
| AI/LLM 기술 | Text2SQL, SQL validator, OpenAI/Gemini gateway, provider fallback, eval framework |
| 저장소 | GitHub README 링크 제출 |
| 포트폴리오 PDF | `docs/korean_company_portfolio_submission.md`를 PDF export해서 제출 |

---

## 2. 프로젝트 한 줄 소개

### 100자 내외

Airflow, PostgreSQL, dbt로 인플루언서 광고 데이터를 campaign ROI/ROAS 분석 플랫폼으로 모델링한 개인 데이터 엔지니어링 프로젝트입니다.

### 300자 내외

AdInsight Agent는 Instagram 인플루언서 광고 수집 데이터와 합성 결제 이벤트를 결합해 campaign ROI, ROAS prediction, Superset monitoring, FastAPI serving까지 연결한 개인 데이터 엔지니어링 프로젝트입니다. Airflow ingestion, PostgreSQL raw schema, dbt layered mart, API serving, Text2SQL guardrail, CI를 하나의 end-to-end 흐름으로 구성했습니다.

### 700자 내외

AdInsight Agent는 인플루언서 광고 집행 데이터를 결제 전환과 campaign ROI 관점으로 분석하기 위해 처음부터 끝까지 혼자 진행한 데이터 엔지니어링 포트폴리오 프로젝트입니다. Airflow DAG로 Apify 기반 Instagram 수집과 daily/backfill 파이프라인을 구성하고, PostgreSQL raw schema에 원본을 보존한 뒤 dbt로 staging, intermediate, marts, features, ai_native 레이어를 모델링했습니다. 합성 결제 이벤트를 기반으로 campaign ROI mart와 ROAS prediction monitor를 만들었고, leave-one-out model comparison 후 benchmark artifact를 FastAPI `/predict/campaign-roas`로 서빙했습니다. 또한 deterministic `/query`와 generated-SQL `/query/v2`를 분리하고, SQL validator, statement timeout, audit log, provider fallback, Text2SQL 평가 체계를 구현했습니다.

---

## 3. 주요 성과 요약

### 이력서 bullet 4개 버전

- Airflow, PostgreSQL, dbt 기반으로 Instagram 수집 데이터와 합성 결제 이벤트를 `raw -> staging -> intermediate -> marts -> features -> ai_native` 레이어로 모델링하고, campaign ROI/ROAS 분석 플랫폼을 구축했습니다.
- Apify 수집, raw loader, daily/backfill DAG, dbt run/test를 연결해 수집-적재-변환 파이프라인을 구성했으며, daily adaptive run 1회에서 `1,725`건 수집과 `1,410`건 신규 적재를 기록했습니다.
- Campaign ROI mart와 ROAS prediction monitor를 구축하고, leave-one-out model comparison을 통해 baseline MAE `0.0892` 대비 linear model MAE `0.0474`의 benchmark artifact를 FastAPI로 서빙했습니다.
- Text2SQL v2에 SQL validator, statement timeout, audit log, provider cost/latency tracking, Gemini -> OpenAI fallback을 구현하고, 24개 정답형 질의와 14개 안전성 질의 기준으로 provider 평가를 수행했습니다.

### 이력서 bullet 6개 버전

- Apify 기반 Instagram 수집, raw loader, Airflow daily/backfill DAG를 구현해 수집-적재 파이프라인을 구성했습니다.
- dbt로 `raw -> staging -> intermediate -> marts -> features -> ai_native` layered warehouse를 설계하고, BI/ML/Text2SQL 소비 목적별 모델을 분리했습니다.
- 합성 결제 attribution/payment events를 기반으로 campaign-grain ROI mart를 만들고, Superset dashboard와 export asset으로 시각화했습니다.
- ROAS model comparison을 leave-one-out 방식으로 수행해 baseline MAE `0.0892`에서 linear model MAE `0.0474`로 개선된 benchmark artifact를 만들었습니다.
- FastAPI로 `/health`, `/predict/campaign-roas`, `/query`, `/query/v2` endpoint를 구현하고, model artifact serving과 natural-language analytics API를 연결했습니다.
- Text2SQL v2 gateway에 SQL validator, timeout, audit, provider usage/cost parsing, Gemini -> OpenAI fallback을 구현하고 GitHub Actions `ruff`/`pytest` 품질 게이트를 추가했습니다.

---

## 4. 채용폼 "프로젝트 상세" 입력용

### 문제

인플루언서 광고 성과 데이터는 게시물 반응, campaign attribution, 결제 전환, ROAS 지표가 분리되어 있어 캠페인별 성과를 빠르게 비교하기 어렵습니다. 또한 자연어로 분석 질문을 처리하는 경우 LLM-generated SQL hallucination과 안전하지 않은 SQL 실행 위험이 있습니다.

### 역할

처음부터 끝까지 혼자 진행한 개인 프로젝트로, 데이터 수집, raw schema 설계, dbt 모델링, Airflow DAG, Superset dashboard, ROAS model comparison, FastAPI serving, Text2SQL gateway/eval, CI와 문서화를 모두 담당했습니다.

### 액션

Airflow DAG로 수집/백필/일일 스코어링 파이프라인을 구성하고, PostgreSQL과 dbt를 사용해 raw, staging, intermediate, marts, features, ai_native 레이어를 설계했습니다. 합성 결제 이벤트로 campaign ROI mart와 ROAS prediction monitor를 만들었고, 모델 비교 결과를 JSON artifact로 저장해 FastAPI에서 request-time fitting 없이 서빙했습니다. Text2SQL은 deterministic `/query`와 generated-SQL `/query/v2`를 분리하고, SQL validator, statement timeout, audit log, provider fallback을 추가했습니다.

### 결과

Daily adaptive run 1회에서 `1,725`건을 수집하고 `1,410`건을 신규 적재했으며, synthetic payment benchmark로 `498`개 결제 이벤트와 net payment KRW `6,329,923.59`를 생성했습니다. Campaign ROI mart는 `30` campaign rows를 만들었고, ROAS model comparison은 baseline MAE `0.0892` 대비 linear model MAE `0.0474`를 기록했습니다. Text2SQL은 24개 정답형 질의와 14개 안전성 질의 기준으로 provider를 평가했고, GitHub Actions 기반 `ruff`와 `pytest` 품질 게이트를 구성했습니다.

---

## 5. 기술 스택 입력란

### 짧은 버전

Python, SQL, Airflow, PostgreSQL, dbt, Superset, FastAPI, GitHub Actions, OpenAI/Gemini API, Text2SQL

### 상세 버전

Python 3.11, SQL, Apache Airflow, PostgreSQL 16, dbt-postgres, Apache Superset, FastAPI, Uvicorn, PyYAML, NumPy, GitHub Actions, ruff, pytest, OpenAI/Gemini gateway, Text2SQL validator/eval framework

---

## 6. 프로젝트 링크 입력란

| 링크 유형 | 입력값 |
|---|---|
| GitHub | GitHub repository URL |
| README | GitHub repository `README.md` |
| 영문 README | `README.en.md` |
| 포트폴리오 PDF | `docs/korean_company_portfolio_submission.md` export PDF |
| 포트폴리오 HTML | `docs/adinsight_portfolio_submission_ko.html` |
| 포트폴리오 DOCX | `docs/adinsight_portfolio_submission_ko.docx` |
| 이력서 최종 bullet | `docs/resume_selected_bullets_ko.md` |
| 데모 GIF | `docs/images/06_text2sql_demo.gif` |
| API 예시 | `docs/api/query_v2_request_response_examples.md` |
| 면접 답변 | `docs/interview_flashcards.md` |

---

## 7. 자기소개서 연결 문장

### 데이터 엔지니어 직무 지원 동기 연결

데이터 엔지니어링을 단순 적재 자동화가 아니라 “분석과 의사결정이 가능한 신뢰도 높은 데이터 제품을 만드는 일”로 보고 있습니다. AdInsight 프로젝트에서는 수집, 원본 보존, dbt 모델링, BI, API serving, Text2SQL guardrail, CI까지 연결하며 데이터가 실제 소비 경로까지 안전하게 전달되는 과정을 직접 구현했습니다.

### AI/데이터 플랫폼 직무 연결

LLM을 데이터 플랫폼에 붙일 때 가장 중요한 것은 모델 성능만이 아니라 안전한 실행 경계라고 생각합니다. AdInsight에서는 deterministic expected-SQL baseline, SQL validator, statement timeout, 안전성 질의 평가, audit log, provider fallback을 구현해 generated SQL이 무조건 실행되지 않도록 설계했습니다.

### 클라우드/운영 직무 연결

현재 구현은 Docker Compose 기반 로컬 플랫폼이지만, 각 구성요소를 AWS managed service로 전환하는 기준도 함께 문서화했습니다. Airflow는 MWAA, PostgreSQL은 RDS/Aurora 또는 Redshift, FastAPI는 ECS Fargate + ALB, artifact는 S3, 로그는 CloudWatch로 매핑했습니다.

---

## 8. 면접에서 먼저 말할 한계

- 결제와 ROAS label은 실제 광고주 데이터가 아니라 synthetic benchmark입니다.
- ROAS model은 25 labeled synthetic campaign rows 기반이라 production forecasting 성능으로 주장하지 않습니다.
- AWS는 target architecture와 skeleton boundary까지만 문서화했고 실제 cloud deployment는 하지 않았습니다.
- `/query/v2`는 validator와 fallback을 갖췄지만, production API로 쓰려면 auth, rate limit, tenant boundary, larger traffic measurement가 추가로 필요합니다.

---

## 9. 제출 전 체크리스트

- [ ] GitHub repository URL이 공개 접근 가능한지 확인
- [ ] README 첫 화면에 architecture, key results, known limitations가 보이는지 확인
- [ ] `docs/korean_company_portfolio_submission.md`를 PDF로 export
- [x] `docs/adinsight_portfolio_submission_ko.html` export 확인
- [x] `docs/adinsight_portfolio_submission_ko.docx` export 확인
- [ ] 이력서에는 `docs/resume_selected_bullets_ko.md`의 최종 4개 bullet만 사용
- [ ] 자기소개서에는 지원 회사 JD와 맞는 연결 문장 1개만 사용
- [ ] 면접 전 `docs/interview_flashcards.md` 15개 카드 복습
