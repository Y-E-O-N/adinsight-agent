# Portfolio Draft — AdInsight Agent

> **이 문서는 "빈 자리"입니다.** Phase 진행 중에 측정값·스크린샷·결정사항을 *그때그때* 채우세요.
> 프로젝트 끝난 뒤 한 번에 정리하면 데모 데이터가 바뀌어 재현이 안 됩니다 (`docs/adinsight_portfolio_template.md` 부록 A).
>
> 이 문서가 충분히 채워지면 → `README.md`, 1-pager PDF, 이력서 bullet, 면접 토크포인트로 **거의 자동 변환** 됩니다.

마지막 갱신: **2026-06-23** (Text2SQL campaign ROI / prediction monitor eval 확장)

---

## How to use
1. 매 Phase 작업 끝에 해당 섹션의 빈 자리 채우기
2. 캡처 가능한 화면이 있으면 `docs/images/NN_topic.png` 로 저장 후 본문에 링크
3. 큰 결정은 `docs/adr/00X-...md` 별도 ADR + 여기에 1줄 요약
4. 매주 금요일 30분: 이번 주 수치 확인 + 안 채워진 칸 표시

**현재 아키텍처 시각화**
- `docs/analysis/2026-06-23_current_architecture_visualization.md` — ingestion → dbt marts → ai_native → Text2SQL eval → ROAS model comparison 흐름

---

# Part A. Phase 별 메트릭 (`portfolio_template.md` §7 압축)

## Phase 1 — 환경 셋업

| 메트릭 | 측정 방법 | 값 |
|---|---|---|
| `make up` → 전부 healthy 시간 | `time make up` | **10.7s** (이미지 캐시 후) |
| 이미지 총 크기 | `docker system df` | **8.7 GB** |
| 컨테이너 수 | `docker compose ps` | **8개 (전부 healthy)** |
| `.env.example` 변수 수 | 수동 | **18** |
| Postgres extension 목록 | `\dx` | vector / pg_trgm / pg_stat_statements |
| Smoke DAG 실행 시간 | Airflow UI | **1s** (SQLExecuteQueryOperator → Postgres) |

**스크린샷**:
- `docs/images/01_airflow_ui.png` — Airflow DAGs 목록
- `docs/images/01_smoke_test_success.png` — Smoke DAG 성공 화면

---

## Phase 2 — 데이터 생성·수집

| 메트릭 | 값 |
|---|---|
| Stage 0 Apify smoke | **20 items / 17.4s actor runtime** |
| Stage 0 Airflow DAG smoke | **20 items / 20s DAG runtime** |
| Stage 1 raw 적재 대상 | **`raw.ig_posts` + `raw.ig_post_sources`** |
| Stage 1 첫 적재 | **inserted 20 / updated 0 / source_links_inserted 20** |
| Stage 1 멱등 재실행 | **4회 반복: inserted 0 / updated 20 / source_links_inserted 0** |
| Stage 1 최종 raw row count | **20 posts / 20 source links** |
| dim_creator 행 수 (목표 10K) | **TBD** |
| fact_post 행 수 (목표 2M) | **TBD** |
| fact_post_metrics_daily 행 수 (목표 20M) | **TBD** |
| 국가 분포 (TW/TH/KR/JP) | **TBD** |
| Parquet 총 크기 | **TBD** |
| 생성 소요 시간 (시드 42) | **TBD** |
| `ingest_synthetic` DAG 실행 시간 | **TBD** |
| **Idempotency** 5회 재실행 후 행 수 변화 | **20 posts / 20 source links 유지** |
| 합성 vs 공개 데이터 비율 | **TBD** |

**스크린샷**: `docs/images/02_dag_ingest.png`, `docs/images/02_country_distribution.png`

**Stage 1 증거**
- DAG run: `ig_collect_smoke` 5회 success (`2026-05-26T06:42:16+00:00` ~ `2026-05-26T06:48:15+00:00`)
- Load metrics: 첫 실행 `inserted=20`, 이후 4회 `updated=20`, `source_links_inserted=0`
- Known limitations: smoke 규모는 `#다이소화장품` 20건이며, Stage 2 본수집에서는 XCom 대신 task 내부 collect-and-load 또는 임시 landing 방식을 검토한다.

---

## Phase 3 — dbt staging / intermediate / marts

| 메트릭 | 값 |
|---|---|
| 모델 수 (staging / intermediate / marts) | **1 / 3 / 1** |
| `dbt run` 전체 시간 | **0.18s / 5 models** |
| `dbt test` 전체 시간 / 통과 수 | **0.37s / 44 passed** |
| 컬럼 description 커버리지 | **TBD %** |
| 테스트 커버리지 (컬럼 대비) | **44 data tests / 5 models** |
| incremental vs full-refresh 시간 차 | **TBD** |
| SCD2 snapshot row 수 | **TBD** |
| 최장 모델 실행 (모델명 + 시간) | **TBD** |
| creator mart row 수 | **46 creators / 49 posts** |
| creator review 대상 | **24 creators** |
| 광고/협찬 후보 게시물 | **21 posts** |

**스크린샷**:
- `docs/images/03_dbt_lineage.png` — dbt docs lineage (`raw → staging → intermediate → mart`)
- `docs/images/phase3_creator_review_table.jpg` — Superset creator review table (`marts.mart_creator_sponsored_summary`, `included_in_creator_review = true`)

**BI export**:
- `dashboards/superset_exports/adinsight_creator_review_export.zip` — Superset dashboard/chart/dataset export (`AdInsight Creator Review`)

**Stage 3 증거**
- dbt models: `staging.stg_ig_posts`, `intermediate.int_ig_post_source_quality`, `intermediate.int_ig_sponsored_candidates`, `intermediate.int_ig_owner_activity`, `marts.mart_creator_sponsored_summary`
- dbt tests: `44/44` pass (`dbt-core 1.8.8`, `dbt-postgres 1.8.2`)
- Superset dataset: `marts.mart_creator_sponsored_summary`
- Superset chart: `Creator Sponsored Review Table`
- Known limitations: Round 1 데이터가 49건으로 작아 creator ranking은 대표성이 낮고, `is_sponsored_candidate`는 caption 키워드 기반 후보값이다.

---

## Phase 4 — AI-Native Mart ⭐

| 메트릭 | 값 |
|---|---|
| ai_native 모델 수 | **TBD** |
| 컬럼 description 커버리지 | **TBD %** |
| `meta.synonyms` 언어 수 (ko/en/zh-tw/th) | **TBD** |
| `meta.example_questions` 평균 수/모델 | **TBD** |
| pgvector chunk 수 | **TBD** |
| 임베딩 빌드 시간 (`make agent-index`) | **TBD** |
| HNSW 인덱스 빌드 시간 | **TBD** |

**ADR**: `docs/adr/003-ai-native-layer.md` — *왜 별도 레이어를 만들었는가 (예상 결과: Exec Acc 일반 마트 42% → ai_native 78%)*

**스크린샷**: `docs/images/04_erd_ai_native.svg`

**Stage 4/5 campaign AI-native 증거**
- `ai_native.ai_creator_sponsored_summary` — creator-level semantic mart
- `ai_native.ai_campaign_roi_summary` — campaign/payment semantic mart
- `features.feature_campaign_roas_training_set` — ROAS training feature table
- `features.feature_campaign_roas_scoring_set` — daily scoring feature table
- Known limitations: `ai_campaign_roi_summary`는 synthetic payment benchmark 기반이며, 실제 광고 성과 일반화 주장이 아니다.

---

## Phase 5 — Superset + 쿼리 최적화 ⭐

| 메트릭 | 값 |
|---|---|
| 대시보드 수 | **2** (`AdInsight Creator Review`, `AdInsight Campaign ROAS Prediction Monitor`) |
| 차트 수 | **2** |
| Virtual dataset 수 | **0** (현재는 dbt physical mart 기반) |
| 캐시 hit rate | **TBD** |

### Before / After EXPLAIN — Case 1: 광고주 ROI

```
[빈 자리 — Phase 5 시 채울 것]
```

| 지표 | Before | After | Δ | 적용 기법 |
|---|---:|---:|---:|---|
| 실행 시간 | TBD ms | TBD ms | — | TBD |
| Plan rows | TBD | TBD | — | — |
| Shared reads | TBD | TBD | — | — |

상세: `metrics/query_optimization_log.md` (Phase 5 시 생성)

**스크린샷**:
- `docs/images/05_campaign_roas_prediction_monitor.png` — Superset campaign ROAS prediction monitoring table
- `docs/images/05_explain_before.png`, `docs/images/05_explain_after.png` — 쿼리 최적화 단계에서 추가 예정

**BI export**:
- `dashboards/superset_exports/adinsight_creator_review_export.zip` — creator review dashboard export
- `dashboards/superset_exports/adinsight_campaign_roas_prediction_export.zip` — campaign ROAS prediction monitoring dashboard export

**Stage 5 증거**
- Superset dataset: `marts.mart_campaign_roas_prediction_monitor`
- Superset chart: `Campaign ROAS Prediction Monitor Table`
- Superset dashboard: `AdInsight Campaign ROAS Prediction Monitor`
- Dashboard rebuild script: `dashboards/scripts/create_campaign_roas_prediction_dashboard.py`
- Dashboard design note: `docs/analysis/stage5_campaign_roas_prediction_dashboard.md`
- Airflow daily refresh DAG: `dags/dag_campaign_roas_prediction_daily.py`
- Manual validation run: `manual__phase5_prediction_validation_20260619` → success
- Prediction monitor metrics: rows `25`, MAE `0.0799`, bias `0.0000`
- JD/cloud tooling strategy: `docs/analysis/stage5_jd_cloud_tooling_strategy.md`

---

## Phase 6 — Text2SQL Agent ⭐⭐ (가장 풍부한 메트릭)

### 평가셋
- 크기: **18 expected-SQL questions** (creator 10 + campaign ROI 4 + prediction monitor 4; 목표 50)
- 언어 분포: KO **9** / EN **9** / ZH-TW **0** / TH **0**
- 난이도: easy **TBD** / medium **TBD** / hard **TBD**

### 결과 비교 표

| Version | Prompt | Model | Exec Acc | p50 | p95 | $/query |
|---|---|---|---:|---:|---:|---:|
| v1 | naive | Gemini Flash | **TBD** | **TBD** | **TBD** | **TBD** |
| v2 | + schema retrieval | Gemini Flash | **TBD** | **TBD** | **TBD** | **TBD** |
| v3 | + few-shot + CoT | Gemini Flash | **TBD** | **TBD** | **TBD** | **TBD** |
| v3 | same | Claude Haiku 4.5 | **TBD** | **TBD** | **TBD** | **TBD** |

### 언어별 / 난이도별
- KO **TBD** / EN **TBD** / ZH-TW **TBD** / TH **TBD**
- easy **TBD** / medium **TBD** / hard **TBD**

### 안전성
- Refuse Rate (negative set): **TBD**
- DELETE/UPDATE/DROP/ALTER 차단: **TBD**

### 실패 사례 3선 (`agent/eval/failure_cases.md`)
1. **TBD**
2. **TBD**
3. **TBD**

**스크린샷·GIF**: `docs/images/06_text2sql_demo.gif`

**다음 Text2SQL 후보**
- expected SQL benchmark: `agent/eval/run_expected_sql.py` 기준 **18/18 PASS**
- `ai_native.ai_campaign_roi_summary` 대상 campaign ROI 질문 4개 추가 완료
- `marts.mart_campaign_roas_prediction_monitor` 대상 prediction error/model metric 질문 4개 추가 완료
- 다음: 실제 LLM-generated SQL 평가 runner, SQL validator, negative set 추가

**Stage 6 eval 증거**
- Evaluation set: `agent/eval/text2sql_questions.yml`
- Analysis note: `docs/analysis/stage4_text2sql_eval_questions.md`
- Latest verified command: `set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_expected_sql.py`
- Result: `summary passed=18 failed=0 total=18`

**ROAS ML model v1**
- Script: `agent/eval/run_campaign_roas_model.py`
- Comparison: `campaign_roas_model_comparison_v1`
- Validation: leave-one-out on `features.feature_campaign_roas_training_set`
- Rows: `25`
- Candidates: `global_mean_baseline_v1`, `objective_mean_roas_baseline_v1`, `linear_regression_numpy_v1`, `ridge_regression_numpy_v1`, `knn_regression_numpy_v1`
- Baseline `objective_mean_roas_baseline_v1`: MAE `0.0892`, RMSE `0.1349`
- Best candidate `linear_regression_numpy_v1`: MAE `0.0474`, RMSE `0.0577`
- Delta vs baseline: MAE `-0.0418`, RMSE `-0.0771`
- Deferred models: LightGBM, XGBoost, CatBoost. 25 synthetic labeled rows is too small for credible boosting-model comparison.
- Known limitation: 25 synthetic labeled campaign rows only; benchmark evidence, not production performance claim.

**FastAPI serving skeleton**
- Service files: `api/main.py`, `api/schemas.py`
- Docker service: `api` in `docker-compose.yml`, port `8000`
- Endpoints:
  - `GET /health`
  - `POST /predict/campaign-roas`
- Live smoke result:
  - `/health` → `{"status":"ok","service":"adinsight-api"}`
  - `/predict/campaign-roas` for `camp_000029` → model `linear_regression_numpy_v1`, predicted ROAS `0.597425`, training rows `25`, artifact `agent/model_artifacts/campaign_roas_linear_v1.json`
- Serving improvement: request-time model fitting removed; API loads the exported linear model artifact.
- Known limitation: artifact is still local JSON fitted on 25 synthetic rows, not a production model registry.

---

## Phase 7 — LLM 자동 리포트

| 메트릭 | 값 |
|---|---|
| 리포트 회차 | **TBD** |
| 평균 생성 시간 | **TBD** s |
| 평균 토큰 비용 | **$ TBD** |
| 수치 검증 (수동 hand count, 5% 이상 오차) | **TBD %** |
| Pydantic schema 실패율 | **TBD** |

**샘플 리포트**: `reports/2026-WW/summary.md` (Phase 7 시 생성)

---

## Phase 8 — 품질·관측·CI

| 메트릭 | 값 |
|---|---|
| pytest 통과 / 커버리지 | **TBD** / **TBD %** |
| dbt test 수 (generic / custom) | **TBD** / **TBD** |
| GitHub Actions 전체 실행 시간 | **TBD** |
| source freshness 실패 알림 동작 검증 | **TBD** |

**배지**: `![CI](https://github.com/<you>/adinsight-agent/actions/workflows/dbt-ci.yml/badge.svg)`

---

## Phase 9 — 트래픽·문서·기여

| 메트릭 | 값 |
|---|---|
| locust 30 동접 p50 / p95 / p99 | **TBD** / **TBD** / **TBD** |
| 동접 변화 커브 (10 / 20 / 30 / 50) | **TBD** |
| Singleflight dedup 비율 | **TBD %** |
| Gemini → Claude fallback 발동 횟수 | **TBD** |
| Back-pressure 503 발동 임계점 | **TBD** |
| ADR 문서 수 | **2** (목표 ≥ 3) |
| Superset 기여 (issue / PR) | **TBD** |

**스크린샷**: `docs/images/09_locust_30.png`

---

# Part B. 스크린샷 · 증거물 체크리스트 (`portfolio_template.md` §8)

## 필수 (README 용)
- [ ] 아키텍처 다이어그램 (SVG/PNG 고해상도) — Mermaid 원본: `docs/analysis/2026-06-23_current_architecture_visualization.md`, 추후 export: `docs/images/00_architecture.svg`
- [ ] ERD (ai_native 레이어 중심) — `docs/images/04_erd_ai_native.svg`
- [ ] Bus Matrix (표 또는 이미지) — README 직접
- [ ] Airflow DAG 그래프 × 3 (ingest / dbt_run / weekly_llm_report)
- [x] dbt docs lineage 그래프 — `docs/images/03_dbt_lineage.png`
- [ ] Superset 대시보드 × 2 (광고주 ROI, 크리에이터 성과)
- [ ] Text2SQL 데모 GIF
- [ ] EXPLAIN Before/After 콘솔 캡처
- [ ] locust 부하 테스트 스크린샷 (RPS, p95)
- [ ] CI 배지 (GitHub Actions)

## 권장 (블로그·심층 문서용)
- [ ] Airflow task 실행 이력 (30일)
- [ ] pg_stat_statements Top 10 쿼리
- [ ] pgvector HNSW 파라미터 비교 표
- [ ] Agent failure case 스크린샷 3건
- [ ] Redis 캐시 히트 로그
- [ ] 다국어 질문 동작 예시 (4개 언어 각 1건)
- [ ] 한 주간 `run_results.jsonl` 차트 (plotly/matplotlib)

### 스크린샷 품질 가이드
- **해상도**: retina 원본 (README 에서 `width=` 로 조절)
- **민감 정보 제거**: 비밀번호, 실 URL
- **테마 통일**: 다크/라이트 한 가지로
- **캡션**: 각 이미지 아래 한 줄 설명
- **파일명**: `docs/images/NN_topic.png` 번호 붙여 순서 유지

---

# Part C. ADR (Architecture Decision Records) 작성 큐

ADR = "왜 X 가 아니라 Y 를 선택했는가" 를 1~2페이지로 남긴 결정 문서. 면접 단골 답변 자료.

| # | 제목 | 위치 | 상태 |
|---|---|---|---|
| 001 | Postgres 단일 스택 vs DuckDB / BigQuery | `docs/adr/001-single-postgres-stack.md` | ✅ Phase 1 작성 |
| 002 | Layered mart vs OBT | `docs/adr/002-layered-mart-vs-obt.md` | ✅ Phase 3 작성 |
| 003 | AI-Native 레이어를 별도로 두는 이유 | `docs/adr/003-ai-native-layer.md` | ⏳ Phase 4 시 |
| 004 | LangChain vs 직접 호출 | `docs/adr/004-langchain.md` | ⏳ Phase 6 시 |
| 005 | Embedding 모델 선택 (bge-m3) | `docs/adr/005-embedding-model.md` | ⏳ Phase 6 시 |
| 006 | Gemini primary + Claude fallback | `docs/adr/006-llm-provider.md` | ⏳ Phase 6 시 |

---

# Part D. 면접 토크포인트 ↔ 증거 매핑 (`portfolio_template.md` §6.1 채울 것)

| 예상 질문 | 핵심 문장 | 증거 위치 | 상태 |
|---|---|---|---|
| 가장 어려웠던 문제 | TBD | `docs/failure_cases.md` (예정) | ⬜ |
| 쿼리 최적화 경험 | 18s → 1.2s, BRIN + 복합 B-tree (예정) | `docs/query_tuning.md` | ⬜ |
| idempotency 어떻게? | DELETE+INSERT, merge, 백필 5회 검증 | `dags/dbt_run.py` (예정) | ⬜ |
| 요청 처리 플로우 | 7단계 (Semaphore → retrieve → generate → validate → execute → format → log) | `docs/request_flow.md` (예정) | ⬜ |
| 트래픽 10배 | 병목 식별 → 캐시 → fallback → async → back-pressure | `docs/traffic_experiments.md` (예정) | ⬜ |
| 동시성 처리 | 4층위 (pipeline / data / serving / agent) | `docs/concurrency_notes.md` (예정) | ⬜ |
| AI-Native 뭐가 다름? | 비정규화 + metadata + Agent 친화 | ADR 003 | ⬜ |
| halucination 방지 | 5층위 (readonly / validator / prompt / refuse / eval) | `docs/agent_eval.md` (예정) | ⬜ |

---

# Part E. 최종 완성도 체크리스트 (`portfolio_template.md` §10)

> 프로젝트 끝내기 전에 훑어볼 것. 하나라도 빠지면 포트폴리오 완성도가 급락.

### 저장소
- [ ] README 가 16개 섹션 모두 채워짐
- [ ] JD 매칭 표의 모든 링크가 실제로 동작
- [ ] 모든 Before/After 표에 **실측 수치**
- [ ] 라이선스·데이터 출처 명시
- [ ] `.env.example` 제공, `.env` gitignore
- [ ] `make up` 으로 낯선 맥에서 재현 가능
- [ ] GitHub Actions CI 통과 배지
- [ ] 커밋 메시지 conventional (feat/fix/docs)
- [ ] Issues 에 "다음 할 일" 정리 (미완성도 공개)

### 문서
- [ ] ADR 최소 3개
- [ ] request_flow / concurrency_notes / traffic_experiments / query_tuning / agent_eval / failure_cases / reliability_playbook / interview_talking_points

### 시각 자산
- [ ] 아키텍처·ERD·DAG×3·대시보드×2·데모 GIF·Before/After EXPLAIN·locust

### 포트폴리오 배포물
- [ ] GitHub public + pin
- [ ] README.en.md (영문)
- [ ] 이력서 bullet 5개
- [ ] 1-pager PDF
- [ ] (선택) 노션/블로그 회고 글
- [ ] LinkedIn 프로젝트 추가

### 면접 준비물
- [ ] 토크포인트 카드 10~12장
- [ ] 1분 자기소개 / 3분 프로젝트 소개 암기
- [ ] 모든 숫자의 출처 설명 가능
