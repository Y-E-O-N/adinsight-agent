# Portfolio Source — AdInsight Agent

마지막 갱신: **2026-07-20**
용도: README, 이력서, 면접 답변, 1-pager PDF를 만들 때 참조할 공개 가능한 증거 모음.

---

## 1. Portfolio Positioning

**One-line pitch**

AdInsight는 인플루언서 광고 집행 데이터를 결제 전환, campaign ROI, ROAS prediction, Superset monitoring, guarded Text2SQL API까지 연결한 데이터 엔지니어링 포트폴리오 프로젝트다.

**What this project proves**

| 역량 | 증거 |
|---|---|
| Workflow orchestration | Airflow collection, backfill, daily ROAS scoring DAG |
| Analytics engineering | dbt `raw -> staging -> intermediate -> marts -> features -> ai_native` 모델링 |
| Data quality | dbt tests, expected-SQL eval, negative Text2SQL eval, CI |
| BI serving | Superset creator review and campaign ROAS monitor |
| ML workflow | ROAS model comparison, artifact export, FastAPI prediction serving |
| LLM/data interface | deterministic `/query`, generated-SQL `/query/v2`, validator, provider gateway, fallback |
| Operations story | request-level provider cost, latency, fallback reason, audit log |
| Cloud translation | AWS target mapping: MWAA, RDS/Aurora, S3, ECS Fargate, ALB, CloudWatch, QuickSight |

**Portfolio claim boundary**

- Payment and ROAS labels are synthetic benchmark data.
- ROAS model scores prove the workflow and serving boundary, not production forecasting generalization.
- Text2SQL v2 is guarded generated SQL, not arbitrary SQL execution.
- AWS content is a target architecture and skeleton boundary, not a deployed cloud system.

---

## 2. Key Metrics

| Area | Metric |
|---|---:|
| Stage 0 Apify smoke | `20` items, `17.4s` actor runtime |
| Stage 1 raw load | first load inserted `20`, idempotent reruns inserted `0` / updated `20` |
| Round 1 collection | final `raw.ig_posts=49`, `raw.ig_post_sources=49` |
| Phase 2B daily adaptive run | `items_collected_total=1725`, `inserted_total=1410` |
| Phase 2C synthetic payment events | `raw.syn_payment_events=498` |
| Synthetic net payment | KRW `6,329,923.59` |
| Campaign ROI mart | `30` campaign rows, max ROAS `0.5969` |
| Prediction monitor | `25` rows, MAE `0.0799`, bias `0.0000` |
| ROAS baseline model | MAE `0.0892`, RMSE `0.1349` |
| ROAS best model | `linear_regression_numpy_v1`, MAE `0.0474`, RMSE `0.0577` |
| deterministic Text2SQL baseline | expected-SQL registry `24/24 PASS` |
| OpenAI external Text2SQL eval | positive `24/24`, negative `14/14` |
| Gemini external Text2SQL eval | positive `24/24`, negative `12/14` |
| Provider cost comparison | Gemini `$0.064098` vs OpenAI `$0.103027` over 38 cases |
| Dual positive live smoke | Gemini final provider, fallback `false`, rows `5`, cost `$0.0014719` |
| Dual safety live smoke | Gemini -> OpenAI fallback, HTTP `404`, cost `$0.0067335` |
| Latest documented quality gate | `ruff` pass, `pytest 82 passed`, `git diff --check` pass |

---

## 3. Evidence Assets

### README-facing visuals

| Asset | Path | Status |
|---|---|---|
| Architecture diagram | `docs/images/00_architecture.svg` | ready |
| Airflow UI | `docs/images/01_airflow_ui.png` | ready |
| Smoke DAG success | `docs/images/01_smoke_test_success.png` | ready |
| dbt lineage | `docs/images/03_dbt_lineage.png` | ready |
| Creator review dashboard | `docs/images/phase3_creator_review_table.jpg` | ready |
| Campaign ROAS prediction monitor | `docs/images/05_campaign_roas_prediction_monitor.png` | ready |
| Text2SQL demo GIF | `docs/images/06_text2sql_demo.gif` | ready |
| Text2SQL eval summary chart | `docs/images/06_text2sql_eval_summary.svg` | ready |
| Data loading flow | `docs/images/adinsight_execution_data_loading_flow.png` | optional |
| Data loading flow with Korean notes | `docs/images/adinsight_execution_data_loading_flow_ko_notes.png` | optional |

### Documentation assets

| Asset | Path |
|---|---|
| Korean company submission portfolio | `docs/korean_company_portfolio_submission.md` |
| Korean submission HTML export | `docs/adinsight_portfolio_submission_ko.html` |
| Korean submission DOCX export | `docs/adinsight_portfolio_submission_ko.docx` |
| Korean job application snippets | `docs/korean_job_application_snippets.md` |
| English README | `README.en.md` |
| Portfolio one-pager | `docs/portfolio_one_pager.md` |
| 3-5 minute demo script | `docs/demo_script_3min.md` |
| Interview talking points | `docs/interview_talking_points.md` |
| Interview flashcards | `docs/interview_flashcards.md` |
| Selected Korean resume bullets | `docs/resume_selected_bullets_ko.md` |
| Resume bullets | `docs/resume_bullets.md` |
| API request/response examples | `docs/api/query_v2_request_response_examples.md` |
| Text2SQL demo evidence | `docs/analysis/stage6_text2sql_demo_evidence.md` |
| Text2SQL v2 design | `docs/analysis/stage6_llm_text2sql_v2_design.md` |
| Text2SQL after-fixes eval report | `docs/analysis/stage6_text2sql_after_fixes_eval_report.md` |
| Text2SQL v1/v2 comparison | `docs/analysis/stage6_text2sql_v1_v2_eval_comparison.md` |
| Text2SQL failure cases | `docs/analysis/stage6_text2sql_v2_failure_cases.md` |
| Text2SQL strict eval report | `docs/analysis/stage6_text2sql_strict_eval_report.md` |
| AWS target architecture | `docs/architecture/aws_target_architecture.md` |
| Text2SQL gateway architecture | `docs/architecture/text2sql_gateway_architecture.md` |

### BI exports

| Export | Path |
|---|---|
| Creator review Superset export | `dashboards/superset_exports/adinsight_creator_review_export.zip` |
| Campaign ROAS prediction Superset export | `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip` |

---

## 4. Phase Summary

| Phase | Portfolio-readable result |
|---|---|
| Phase 1 | Docker Compose local stack: Postgres, Airflow, Superset, Redis/worker services, smoke DAG evidence |
| Phase 2 | Apify collection, raw loader, source-link table, idempotent reruns, daily/backfill DAGs |
| Phase 2C | Synthetic campaign attribution and payment event generation from observed engagement signals |
| Phase 3 | dbt staging/intermediate/mart models and Superset creator review dashboard |
| Phase 3B | Campaign-grain ROI mart from synthetic payment events |
| Phase 4/5 | `ai_native` semantic marts, feature tables, prediction monitor mart, Superset ROAS monitor |
| Phase 6 | ROAS model comparison, artifact-backed FastAPI prediction serving, deterministic `/query` |
| Phase 6B | Generated-SQL `/query/v2`, SQL validator, provider factory, gateway, audit, eval runners |
| Phase 6C | Local/external Text2SQL model evaluation, provider cost tracking, Gemini -> OpenAI fallback |
| Phase 8C | GitHub Actions CI with `ruff` and `pytest` |
| Phase 9B | README, demo script, API examples, interview talking points, resume bullets |

---

## 5. Resume Bullet Candidates

Use 4-5 bullets from this list, depending on the job description.

- Built an end-to-end influencer campaign analytics platform with Airflow, Postgres, dbt, Superset, and FastAPI, modeling raw Instagram collection and synthetic payment events into campaign ROI, ROAS prediction, and Text2SQL-ready semantic marts.
- Designed a layered dbt warehouse (`raw -> staging -> intermediate -> marts -> features -> ai_native`) with immutable raw inputs, idempotent transformations, semantic metadata, and portfolio evidence captured through dbt tests, screenshots, and run metrics.
- Implemented campaign payment and ROI marts from synthetic attribution/payment events, producing campaign-grain ROAS summaries and reusable feature tables for model training and daily scoring.
- Built a ROAS model comparison runner using leave-one-out validation across baseline, linear, ridge, and KNN candidates; improved MAE from objective-mean baseline `0.0892` to `0.0474` with `linear_regression_numpy_v1`.
- Served campaign ROAS predictions through FastAPI using a saved model artifact instead of request-time fitting, exposing reproducible response metadata such as model name, training rows, feature source, and scoring snapshot date.
- Built a generated-SQL Text2SQL v2 boundary with provider factory, SQL validator, statement timeout, best-effort audit logging, provider usage/cost tracking, fallback orchestration, and explicit API error handling.
- Expanded Text2SQL evaluation to 24 positive questions and 14 negative/content-safety questions, with latest external-provider runs reaching OpenAI `24/24` positive and `14/14` negative pass, and Gemini `24/24` positive and `12/14` negative pass.
- Added GitHub Actions CI for Python 3.11 with `uv sync --dev --frozen`, full `ruff check`, and `pytest`.

---

## 6. Interview Talking Points

| Question | Short answer | Evidence |
|---|---|---|
| Why synthetic payment data? | Real payment data is sensitive, so synthetic payment events are labeled as benchmark evidence and not real business performance. | `data_generation/`, `docs/interview_talking_points.md` |
| Why a simple ROAS model? | With 25 labeled synthetic rows, simple leave-one-out models are more defensible than claiming a complex boosting model generalizes. | `agent/eval/run_campaign_roas_model.py` |
| Why separate `ai_native` marts? | BI marts serve dashboards; `ai_native` marts expose clear grain, semantic metadata, and Text2SQL-friendly columns. | `dbt/models/ai_native/` |
| How is hallucination controlled? | `/query` uses reviewed expected SQL; `/query/v2` uses provider contract, SQL validator, timeout, audit, negative eval, and fallback. | `agent/text2sql/`, `text2sql_gateway/` |
| Why Gemini primary + OpenAI fallback? | Gemini was cheaper in the measured 38-case scope, OpenAI was cleaner on safety and faster overall, so ADR 004 uses Gemini primary plus OpenAI fallback. | `docs/adr/004-text2sql-dual-provider-fallback.md` |
| How would this move to AWS? | Airflow -> MWAA, Postgres -> RDS/Aurora or Redshift, FastAPI -> ECS Fargate + ALB, logs -> CloudWatch, artifacts -> S3. | `docs/architecture/aws_target_architecture.md` |

---

## 7. Public README Checklist

- [x] Clear one-line pitch
- [x] Architecture image visible near the top
- [x] Key results table with measured values only
- [x] Demo GIF and evidence links
- [x] Local Quickstart
- [x] JD/evidence mapping
- [x] Known limitations section
- [x] AWS target mapping
- [x] Local link check in current working tree
- [x] Portfolio one-pager markdown
- [x] Interview flashcards
- [x] English-only `README.en.md`
- [x] Korean company submission portfolio markdown
- [x] Korean job application snippets
- [x] Selected Korean resume bullets
- [x] Korean submission HTML export
- [x] Korean submission DOCX export
- [ ] Optional: exported 1-pager PDF

---

## 8. Not Implemented / Stretch Backlog

These should not be presented as completed work in the README.

| Item | Status |
|---|---|
| Query optimization before/after EXPLAIN study | Not implemented |
| Locust load test / traffic curve | Not implemented |
| Weekly LLM report DAG | Not implemented |
| Superset open-source contribution | Not implemented |
| Full AWS deployment | Not implemented |
| Exported 1-pager PDF | Not implemented |
| Korean submission PDF | Blocked locally: `pdflatex` is not installed |
| Live auth/rate-limit/tenant boundary for `/query/v2` | Not implemented |

---

## 9. ADR Index

| ADR | Decision | Status |
|---|---|---|
| `docs/adr/001-single-postgres-stack.md` | Use one local Postgres stack instead of adding a separate warehouse during the learning phase | Accepted |
| `docs/adr/002-layered-mart-vs-obt.md` | Use layered dbt marts instead of one wide OBT-only model | Accepted |
| `docs/adr/003-redesign-ac-strategy.md` | Reposition the project around influencer campaign analytics plus payment/ROAS/Text2SQL | Accepted |
| `docs/adr/004-text2sql-dual-provider-fallback.md` | Use Gemini primary, OpenAI fallback, deterministic registry final fallback for Text2SQL v2 serving | Accepted |

---

## 10. Next Portfolio Work

Recommended order:

1. Run a final local documentation link check.
2. Verify README Quickstart on a clean-ish local stack, or explicitly mark environment prerequisites.
3. Create a one-page recruiter PDF from sections 1, 2, 3, and 5.
4. Convert section 6 into 10 interview flashcards.
5. Decide whether `README.en.md` is worth the time for the target applications.
