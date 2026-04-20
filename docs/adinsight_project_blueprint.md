# LINE Pay AI Insight Engineer 포트폴리오 프로젝트 설계서

> **목적**: LINE Pay "AI Insight Engineer" JD에 정확히 매칭되는 포트폴리오 프로젝트를, MacBook 로컬 환경에서 Claude Code로 실행 가능한 형태로 설계.
> **도메인**: 글로벌 멀티 플랫폼 인플루언서 광고 성과 분석 (TikTok / Instagram / YouTube Shorts)
> **작성자 맥락**: Aimers 인플루언서 마케팅 데이터 업무 경험을 그대로 살리되, DE 역량(ETL·데이터 마트·BI Agent·LLM 연동)에 집중.

---

## 0. 한 줄 피치 & 프로젝트 명

**프로젝트명**
- 정식 명칭: `Project-AdInsight-Agent`
- 짧게: `AdInsight Agent`
- GitHub 저장소명: `adinsight-agent` (소문자, 하이픈)
- 코드/폴더/DB명: `adinsight` (snake_case)

> 이 문서 이하에서는 `AdInsight Agent`로 통일.

**한 줄 피치 (한국어)**
> "대만·태국·한국·일본 4개 지역의 TikTok / Instagram / YouTube Shorts 인플루언서 광고 성과 데이터를 수집·정제·모델링하고, LLM AI Agent가 자연어로 질의할 수 있는 AI-Native 데이터 마트와 Text2SQL BI Agent를 제공하는 글로벌 인플루언서 광고 분석 플랫폼."

**한 줄 피치 (영어, 이력서용)**
> "A multi-region influencer ad performance analytics platform with an AI-Native data mart and Text2SQL BI agent, built on Airflow, dbt, Superset, and LangChain."

**LINE Pay JD와의 도메인 브릿지**
- LINE Pay 광고 추천 시스템 ↔ 인플루언서 광고 채널 매칭 (둘 다 "광고주 ↔ 채널/오디언스 매칭" 문제)
- LINE Pay 다국가 서비스 (TW·TH) ↔ 다국가 인플루언서 데이터 (타임존·통화·지역 규칙)
- LINE Pay Advertiser Portal 지표 ↔ 광고 캠페인 ROI / CTR / CVR / ROAS
- 면접에서 안전한 화법: *"현재 업무와 직접 연관된 도메인을 심화시키면서 DE 스택을 실전 적용해본 프로젝트"*

---

## 1. JD → 프로젝트 산출물 매핑

| JD 항목 | 프로젝트 산출물 |
|---|---|
| **AI Native 데이터 마트 설계·운영** | `marts/ai_native/` 레이어 (LLM 친화 비정규화 테이블 + dbt YAML에 semantic description, synonyms, 예시 질문 포함) |
| **대규모 ETL 파이프라인 (Airflow)** | Airflow DAG 5~7개 (plat별 수집 / 정제 / 집계 / 품질 / 리포트) + 백필·재처리 |
| **AI 학습용 데이터 전처리** | 캡션·해시태그·댓글 텍스트 정제 + 임베딩 생성 + Vector DB 적재 |
| **Tableau/Superset 대시보드** | Superset 대시보드 3종 (Advertiser ROI / Creator Rank / Campaign Ops) |
| **LLM 연동 자동 분석 리포트** | 주간 자동 리포트 생성 DAG (대시보드 캡처 + LLM 요약 + Slack/이메일 전송) |
| **Text2SQL BI Agent** | LangChain 기반 schema-aware SQL Agent + 평가 프레임워크 + 프롬프트 iteration 로그 |
| **데이터 리터러시 교육** | README·아키텍처 문서·쿼리 예시 북 + 내부 글로서리 |
| **대용량 쿼리 최적화** | Before/After 성능 비교 기록 (EXPLAIN, 인덱스, 파티셔닝, 집계 테이블) |
| **Pandas + API 연동** | 수집 레이어: TikTok/YouTube 공개 API·scraped dataset 병합 |
| **LangChain·Vector DB 우대** | LangChain SQL Agent + pgvector (Postgres extension) |
| **Superset 오픈소스 기여 우대** | 이 문서 섹션 11 참고 (Good First Issue 리스트 + 기여 플랜) |
| **글로벌 협업 경험 우대** | 다국가 모델링 (타임존·i18n·통화) + 영문 README·다이어그램 병행 |

---

## 2. 데이터 전략 — 공개 데이터셋 + 합성 데이터

### 2-1. 공개 데이터셋 (raw 레이어의 현실감 확보용)

| 데이터셋 | 설명 | 활용 레이어 |
|---|---|---|
| **YouTube Trending Video Dataset** (Kaggle, Mitchell J.) | 다국가 일별 트렌딩 영상 메타·통계 | YouTube raw |
| **TikTok Influencers Dataset** (Kaggle, HuggingFace 내 공개본) | 상위 크리에이터 팔로워·카테고리 | TikTok profile raw |
| **Instagram Influencers Dataset** (HypeAuditor / Kaggle 공개본) | 인스타 탑 인플루언서 ER, 팔로워 | Instagram raw |
| **Social Media Ads / Marketing Campaign Datasets** (Kaggle) | 광고 캠페인 비용·노출·클릭 | Campaign raw |
| **Multilingual Text Corpora** (HuggingFace — 댓글/캡션 샘플) | 텍스트 전처리·임베딩 실습 | NLP staging |

> ⚠️ Kaggle 데이터셋은 라이선스 꼭 확인 (개인 포트폴리오 한정, 재배포 금지 등). README에 출처·라이선스 명시.

### 2-2. 합성 데이터 생성 전략 (Synthetic Layer)

실제 인플루언서 DB 규모와 현업 패턴을 재현하는 합성 데이터를 직접 생성. **공개 데이터만으로는 "광고주-캠페인-인플루언서-정산" 전체 파이프라인을 못 만들기 때문에 반드시 필요.**

**사용 라이브러리**
- `Faker` — 이름·지역·다국어 텍스트
- `mimesis` — 더 빠른 다국어 로케일 지원
- `SDV` (Synthetic Data Vault) — 공개 데이터셋의 분포를 학습해 통계적으로 유사한 데이터 생성 (면접 어필 포인트)
- `numpy` / `scipy` — 로그노멀·파레토 분포로 팔로워·ER 생성 (현실감)

**생성 테이블 (합성 + 반합성)**

| 테이블 | 행 수 | 분포·로직 |
|---|---|---|
| `dim_creator` | 10,000 | 팔로워: 로그노멀(μ=10, σ=2), 지역: TW 40 / TH 25 / KR 20 / JP 15, 플랫폼 중복 허용 |
| `dim_advertiser` | 500 | 카테고리: 뷰티·푸드·핀테크·게임·패션, 예산 규모 파레토 |
| `dim_campaign` | 5,000 | advertiser × 기간 × 목표(KPI) |
| `fact_post` | 2,000,000 | creator × 일별 × 플랫폼. 시계열 EWMA 패턴으로 조회수 생성 |
| `fact_post_metrics_daily` | 20,000,000 | 일별 스냅샷 (SCD-2 대안) |
| `fact_campaign_match` | 50,000 | 캠페인 ↔ 인플루언서 매칭 (advertiser ad recommendation 시뮬) |
| `fact_payment` | 30,000 | LINE Pay 스타일: 정산 · 다국가 통화 · FX rate 적용 |
| `dim_date` / `dim_region` / `dim_currency` | — | 컨포먼드 디멘션 |

**포인트**
- **스케일**: 합쳐서 약 2천만~5천만 행 → 로컬에서 쿼리 최적화 실습에 딱 좋은 규모
- **저장**: Parquet + 날짜 파티셔닝 (`year=YYYY/month=MM/day=DD`)
- **결정성**: 시드 고정(`SEED=42`), 재생성 가능
- **CDC 시뮬**: `updated_at` 필드 + 일부 레코드 매일 수정되도록 생성 → 증분 적재 실습

### 2-3. 면접 무기화 포인트
> *"단순 더미 데이터가 아니라, 공개 데이터셋의 분포를 SDV로 학습시킨 뒤, 현업에서 관측한 팔로워·ER의 로그노멀/파레토 분포에 맞춰 재샘플링했습니다. 덕분에 쿼리 플랜·집계 성능 실험이 실제 운영 환경과 유사하게 재현됩니다."*

---

## 3. 아키텍처 & 기술 스택 (MacBook 로컬)

### 3-1. 스택 선정 근거 (JD 기준)

| 레이어 | 도구 | 선정 이유 |
|---|---|---|
| **Orchestration** | **Apache Airflow 2.9+** (Docker, CeleryExecutor) | JD 명시. CeleryExecutor로 동시성·트래픽 실험 가능 |
| **Warehouse** | **PostgreSQL 16 + pgvector** | 로컬 부담↓, pgvector로 Vector DB까지 단일 스택 |
| **Transform** | **dbt-postgres 1.8+** | JD 명시. AI-Native mart 레이어의 핵심 |
| **BI** | **Apache Superset 4.x** (Docker) | JD 명시. Tableau 대신 Superset을 메인으로 (오픈소스 기여도 우대 항목) |
| **LLM Framework** | **LangChain + LangGraph** | SQL Agent 표준. Gemini / Claude / OpenAI 모두 교체 가능하게 |
| **LLM Provider** | Gemini 2.5 Flash (URL/저비용) + Claude Haiku 4.5 (신뢰성) | 본인이 이미 평가 끝낸 조합 — 면접 설득력↑ |
| **Vector DB** | **pgvector** | Postgres extension → 인프라 단순화 |
| **Data Quality** | `dbt tests` + `Great Expectations` (선택) | 테스트 피라미드 |
| **Lineage / Docs** | `dbt docs` + `SQLMesh`(선택) | JD의 "데이터 리터러시" 항목 대응 |
| **Local Python** | `uv` + `pyproject.toml` | 2025년 기준 de facto |
| **IaC 대안** | `docker-compose` + `Makefile` | 로컬 재현성 |

### 3-2. MacBook (Apple Silicon) 주의사항 — **놓치기 쉬운 포인트**

- **Airflow 이미지는 반드시 `linux/arm64` 또는 `linux/amd64` 명시** → 미명시 시 M1/M2/M3에서 Rosetta로 느려짐
- **Superset 4.x는 arm64 공식 이미지 있음** (`apache/superset:4.0.0` 확인)
- **pgvector는 `ankane/pgvector` 이미지** (arm64 멀티아치)
- **메모리 할당**: Docker Desktop → Resources → Memory **최소 8GB, 권장 12GB** (Airflow + Postgres + Superset + LangChain 동시 구동)
- **포트 충돌**: 5432(Postgres), 8080(Airflow), 8088(Superset), 5555(Flower) 미리 확보
- **파일 마운트 I/O**: Docker Desktop의 VirtioFS 활성화 (Settings → General)
- **Rosetta x86_64 에뮬레이션** 체크박스는 Postgres/Redis에는 **끄는 게 낫다** (arm64 네이티브 이미지 쓰므로)

### 3-3. 전체 아키텍처 (텍스트 다이어그램)

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER (raw)                         │
│  Kaggle CSV  ▸  Public APIs (YT Data API v3)  ▸  SDV synthetic  │
└───────────────────────┬─────────────────────────────────────────┘
                        │ Airflow DAG: ingest_*
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│         STORAGE  (Postgres schemas: raw / staging / mart)        │
│  raw.*       →  schema-on-read, 원본 보존                         │
│  staging.*   →  타입 캐스팅, PII 마스킹, 1:1 정제                 │
│  intermediate.* → 조인 / 증분 / EWMA                              │
│  marts.*     →  비즈 모델 (star schema)                            │
│  ai_native.* →  LLM 친화 denormalized + rich metadata             │
└───────────────────────┬─────────────────────────────────────────┘
                        │ dbt run / test / docs
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CONSUMPTION LAYER                         │
│  ┌──────────────┐   ┌────────────────┐   ┌──────────────────┐   │
│  │  Superset    │   │ Text2SQL Agent │   │ Weekly Report DAG│   │
│  │  (dashboards)│   │ (LangChain)    │   │  (LLM summaries) │   │
│  └──────────────┘   └────────────────┘   └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌───────────────────────┐
              │ pgvector (schema emb) │
              └───────────────────────┘
```

---

## 4. 폴더 구조 (모노레포)

```
adinsight/
├── README.md                    # 영/한 병기, JD 매핑표 포함
├── CLAUDE.md                    # Claude Code 전용 컨텍스트 (섹션 14)
├── pyproject.toml               # uv 기반
├── Makefile                     # make up / down / seed / test / dbt-run
├── docker-compose.yml
├── .env.example
│
├── infra/
│   ├── airflow/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── superset/
│   │   ├── Dockerfile
│   │   └── superset_config.py
│   └── postgres/
│       └── init/01_extensions.sql  # CREATE EXTENSION vector, pg_trgm;
│
├── data_generation/             # 합성 데이터 생성
│   ├── generators/
│   │   ├── creators.py
│   │   ├── campaigns.py
│   │   ├── posts_timeseries.py
│   │   └── payments.py
│   ├── sdv_models/              # SDV 학습 아티팩트
│   └── run_generate.py
│
├── dags/                        # Airflow DAGs
│   ├── common/                  # callbacks, hooks, macros
│   ├── ingest_tiktok.py
│   ├── ingest_instagram.py
│   ├── ingest_youtube_shorts.py
│   ├── ingest_synthetic.py
│   ├── dbt_run.py
│   ├── data_quality.py
│   ├── weekly_llm_report.py
│   └── backfill_helper.py
│
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml             # (gitignore)
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   ├── marts/
│   │   │   ├── advertiser/
│   │   │   ├── creator/
│   │   │   └── campaign/
│   │   └── ai_native/           # ⭐ LLM-facing denormalized layer
│   ├── seeds/
│   ├── snapshots/               # SCD Type 2
│   ├── tests/
│   └── macros/
│
├── agent/                       # Text2SQL BI Agent
│   ├── app.py                   # FastAPI or Streamlit
│   ├── chains/
│   │   ├── schema_retriever.py  # pgvector 기반
│   │   ├── sql_generator.py
│   │   ├── validator.py
│   │   └── executor.py
│   ├── prompts/                 # 버전 관리 yaml
│   │   ├── v1_zero_shot.yaml
│   │   ├── v2_few_shot.yaml
│   │   └── v3_cot_with_schema.yaml
│   ├── eval/
│   │   ├── dataset.jsonl        # custom eval set (질문, 정답 SQL, 정답 결과)
│   │   ├── run_eval.py
│   │   └── metrics.py
│   └── embeddings/
│       └── build_schema_index.py
│
├── dashboards/
│   ├── superset_exports/        # YAML/ZIP export
│   └── screenshots/
│
├── reports/                     # 주간 자동 리포트 산출물
│   └── {YYYY-WW}/
│       ├── data.json
│       ├── summary.md
│       └── charts/
│
├── metrics/                     # ⭐ 포트폴리오 지표 자동 기록 (섹션 7)
│   ├── portfolio_metrics.md
│   ├── run_results.jsonl
│   ├── query_optimization_log.md
│   └── text2sql_eval_results/
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── request_flow.md          # ⭐ 요청 처리 플로우 (면접 대비)
│   ├── concurrency_notes.md     # ⭐ 동시성 처리 (면접 대비)
│   ├── traffic_experiments.md   # ⭐ 트래픽 실험 (면접 대비)
│   └── interview_talking_points.md
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── .github/
    └── workflows/
        ├── lint.yml             # ruff + sqlfluff
        ├── dbt-ci.yml
        └── agent-eval.yml
```

---

## 5. 단계별 구현 계획 (Phase 1 → 9)

각 Phase 끝에 **Claude Code 프롬프트 템플릿**을 포함. 한 Phase가 대략 1주~1주 반 분량 (평일 저녁 1~2시간 기준).

### Phase 1 — 환경 셋업 & 스켈레톤 (2~3일)

**Goals**
- docker-compose로 Postgres + Airflow + Superset + pgvector 기동
- uv 기반 Python 환경, Makefile, .env.example
- 최소 smoke test

**체크리스트**
- [ ] `make up` 한 방에 올라오는지
- [ ] Airflow UI 접속 (localhost:8080)
- [ ] Superset UI 접속 (localhost:8088)
- [ ] Postgres에 `vector`, `pg_trgm`, `pg_stat_statements` extension 생성
- [ ] Airflow → Postgres 연결 테스트 DAG 1개

**Claude Code 프롬프트 템플릿**
````
CLAUDE.md를 먼저 읽고 이 프로젝트의 목표와 제약을 이해해줘.

Phase 1 목표: MacBook (Apple Silicon, M-series) 로컬에서 한 번에 기동 가능한 데이터 스택을 구축한다.

요구사항:
1. docker-compose.yml 작성 — 서비스: postgres(16, pgvector), airflow-webserver, airflow-scheduler, airflow-worker, redis, superset
2. 모든 이미지는 arm64 호환을 명시적으로 확인 (platform: linux/arm64 또는 멀티아치)
3. Postgres init SQL로 extension 생성: vector, pg_trgm, pg_stat_statements
4. Airflow는 CeleryExecutor. DAG 디렉토리는 ./dags 마운트
5. Superset metadata DB도 같은 postgres 컨테이너의 별도 DB로 분리 (superset_metadata)
6. .env.example 작성 (AIRFLOW_UID, POSTGRES_PASSWORD 등)
7. Makefile: up, down, logs, psql, airflow-cli, superset-init
8. uv 기반 pyproject.toml (python 3.11)
9. 최소 smoke DAG: sample_smoke_test.py — Postgres에 SELECT 1

제약:
- docker-compose V2 문법 (version 필드 제거)
- 메모리 합계 8GB 이내로 동작하게 worker 수 조정
- 포트 충돌 피하기 위해 Superset 8088, Airflow 8080 사용

끝나면 README에 "Quick Start" 섹션을 추가하고, `make up` 후 확인 절차를 한국어로 적어줘.

작업 시작 전에 구성 계획을 먼저 번호 매겨 요약하고, 내 confirm을 받은 뒤 구현해.
````

---

### Phase 2 — 합성 데이터 + 공개 데이터 수집 (5~7일)

**Goals**
- `data_generation/`에 생성기 구현
- 공개 데이터셋 다운로드 스크립트
- raw 스키마 적재 DAG

**포인트**
- SDV로 공개 데이터셋 분포 학습 → 재샘플링 (면접 어필)
- 로그노멀/파레토 분포로 현실감
- `updated_at` 기반 CDC 시뮬

**메트릭 기록 (섹션 7 참고)**
- 생성된 행 수, 용량(GB), 생성 시간, 시드

**Claude Code 프롬프트**
````
Phase 2: 인플루언서 광고 성과 분석용 데이터 생성·수집 레이어를 구축한다.

데이터 설계:
- dim_creator: 10,000명, 팔로워 로그노멀(μ=10, σ=2), 지역 TW/TH/KR/JP 가중치 40/25/20/15
- dim_advertiser: 500, 카테고리(뷰티/푸드/게임/핀테크/패션), 예산 파레토
- dim_campaign: 5,000
- fact_post: 2M, 플랫폼 TikTok/Instagram/YouTube Shorts
- fact_post_metrics_daily: 20M (일별 스냅샷, EWMA 시계열 패턴)
- fact_campaign_match: 50K
- fact_payment: 30K (다국가 통화 TWD/THB/KRW/JPY, FX rate 적용)

구현:
1. data_generation/generators/ 하위에 모듈별 파일, 타입 힌트 + pydantic 스키마
2. SDV를 이용해 Kaggle YouTube Trending Video Dataset을 학습시켜 fact_post의 뷰/좋아요 분포 생성 (학습 모델은 ./sdv_models에 저장)
3. 모든 생성은 SEED=42로 재현 가능
4. 출력은 Parquet + 날짜 파티셔닝 (year=YYYY/month=MM/day=DD/)
5. Airflow DAG ingest_synthetic: Parquet → Postgres raw 스키마 COPY 적재
6. Airflow DAG ingest_public_*: 공개 데이터셋 다운로드 + 라이선스 기록

제약:
- 실행 시간 30분 이내 (로컬 기준)
- updated_at 컬럼 포함, 매일 5% 레코드가 수정되도록 → 증분 실습용
- PII는 절대 실데이터 사용 금지. 생성된 이름·이메일도 faker

추가 산출물:
- data_generation/README.md에 생성 로직, 분포 선택 이유, 재현 방법
- metrics/run_results.jsonl에 생성 결과 append (rows, size_mb, duration_s, seed)

먼저 스키마 ERD와 파일 리스트를 제시하고 confirm 받아.
````

---

### Phase 3 — dbt 모델링: staging / intermediate / marts (1주~1주 반)

**Goals**
- dbt 프로젝트 구조
- staging → intermediate → marts 레이어
- **star schema**로 설계 (Kimball 스타일)
- SCD Type 2 스냅샷 (creator 팔로워 변화)

**포인트 (면접 무기)**
- dbt YAML `description`·`tests`·`meta` 완성도 (리터러시·거버넌스)
- `not_null` / `unique` / `relationships` / `accepted_values` 최소 테스트
- 커스텀 테스트 1~2개 (예: 팔로워 수 단조증가가 아닌 경우 플래그)
- `dbt docs generate` → 정적 사이트

**Claude Code 프롬프트**
````
Phase 3: dbt 프로젝트를 Kimball 스타일 star schema로 구축한다.

레이어:
- staging/*: 타입 캐스팅, 컬럼 리네이밍 (snake_case), 1:1 관계, PII 마스킹 (email → hash)
- intermediate/*: 증분 모델(materialized='incremental', unique_key + updated_at), 조인
- marts/*:
  - dim_creator_scd (snapshot 기반 SCD2)
  - dim_advertiser
  - dim_campaign
  - dim_date, dim_region, dim_currency (conformed)
  - fct_post_daily
  - fct_campaign_performance
  - fct_payment_settled (FX 환산 컬럼 포함)

요구:
1. dbt_project.yml에 레이어별 +materialized, +schema 설정
2. 모든 모델에 description, columns.description, tests 추가
3. macros/: generate_schema_name 커스텀, cents_to_currency, fx_convert
4. 커스텀 테스트 2개: assert_followers_monotonic_or_flagged, assert_no_future_dates
5. snapshot: snapshots/creator_snapshot.sql (strategy='check', check_cols=['follower_count','category'])
6. dbt docs 생성 스크립트 + CI에서 돌릴 것
7. sqlfluff 설정 (.sqlfluff) dialect=postgres

메트릭:
- metrics/portfolio_metrics.md에 모델 수, 테스트 수, doc 커버리지(%), snapshot 수 자동 업데이트
- dbt compile 시간 기록

제약:
- 모든 SQL은 CTE 스타일, 윈도우 함수 적극 활용
- 하드코딩 금지, ref()/source() 일관

완료 후 ai_native 레이어 설계를 위한 Phase 4 진입 준비 보고서를 작성해.
````

---

### Phase 4 — AI-Native Data Mart (⭐ JD 핵심) (5~7일)

**Goals**
- LLM Agent가 쉽게 해석·조회할 수 있도록 특화된 별도 마트 레이어
- "일반 마트"와의 **의도된 차이**를 문서화 (면접 포인트)

**설계 원칙**
1. **비정규화**: 팩트 + 자주 쓰이는 차원을 미리 조인 (Agent가 조인 실수 안 하도록)
2. **Semantic naming**: 컬럼명을 비즈 용어로 (`view_count_24h` not `vc_24`)
3. **Rich metadata**: 각 컬럼에 단위·집계 가능 여부·비즈 정의·예시 값
4. **Synonyms YAML**: `views ≈ 조회수 ≈ view count ≈ impression`
5. **Example questions bank**: 모델별로 `meta.example_questions: [...]`
6. **Row-level security 준비**: region / advertiser_id 필드 명시적

**핵심 테이블 예시**
```sql
-- ai_native.wide_campaign_360
-- 하나의 캠페인에 대해 Agent가 물어볼 법한 거의 모든 필드를 denormalized
campaign_id, campaign_name, advertiser_id, advertiser_name, advertiser_category,
region, currency, budget_usd, spent_usd,
start_date, end_date, duration_days,
total_impressions, total_views, total_likes, total_comments, total_shares,
avg_engagement_rate, ctr, cvr, roas,
top_creator_id, top_creator_name, top_creator_followers,
platform_mix_jsonb, -- {"tiktok": 0.4, "ig": 0.3, "yt_shorts": 0.3}
updated_at
```

**Claude Code 프롬프트**
````
Phase 4: ai_native 데이터 마트 레이어를 설계·구축한다. 이 레이어는 LLM 기반 Text2SQL Agent의 1차 타깃이다.

설계 원칙을 dbt YAML meta에 모두 반영:
- description: 비즈 용어 중심
- columns[].description: 단위(원화·USD·% 등), 집계 가능 여부, NULL 의미
- meta.synonyms: 한/영 유의어 리스트
- meta.example_questions: 이 모델로 답 가능한 질문 3~5개
- meta.grain: 모델 granularity (예: "1 row per campaign")

만들 모델:
1. ai_native.wide_campaign_360 — 캠페인 단위 고정폭 360
2. ai_native.wide_creator_profile — 크리에이터 프로필 + 최근 30일 성과
3. ai_native.wide_daily_platform_summary — 일/플랫폼/지역 집계
4. ai_native.glossary — seed 테이블, 용어·정의·예시

요구:
- 각 모델에 대해 일반 marts 레이어와의 차이를 docs/ai_native_design_rationale.md 에 서술
- 모든 ai_native 모델은 materialized='table'
- 컬럼명 규칙 문서화: 시간창 suffix(_1d, _7d, _30d), 통화 suffix(_usd, _local)
- 예시 쿼리 10개를 agent/eval/dataset.jsonl 의 seed로 생성 (Phase 6에서 사용)

면접 무기화:
- docs/ai_native_design_rationale.md 에 "왜 일반 마트로는 LLM Agent가 실수하는가"의 실제 실패 사례 2~3개와 그 해결을 기록

완료 후 구축한 모델 요약 + 예시 쿼리 10개를 보여줘.
````

---

### Phase 5 — Superset 대시보드 + 쿼리 최적화 (5~7일)

**Goals**
- 대시보드 3종
- **Before/After 쿼리 최적화 기록** (면접 핵심)

**대시보드 구성**
1. **Advertiser ROI** — 광고주별 ROAS, CPM, CVR, 지역별 히트맵
2. **Creator Rank** — 카테고리별 Top creator, 성장률, ER 분포
3. **Campaign Ops** — 진행중/예정/완료 캠페인, 지연/이상 플래그

**쿼리 최적화 실험**
- 초기 대시보드 로드 시간 측정 → EXPLAIN ANALYZE
- 개선안 적용: 인덱스, 머티리얼라이즈드 뷰, dbt 사전 집계, `pg_stat_statements` 기반 핫쿼리 파악
- 개선율을 `metrics/query_optimization_log.md` 에 기록

**Claude Code 프롬프트**
````
Phase 5: Superset 대시보드 3종을 구축하고 쿼리 최적화 실험을 수행한다.

Superset:
1. superset_config.py에 FEATURE_FLAGS 설정 (DASHBOARD_NATIVE_FILTERS, ALERT_REPORTS 등)
2. Dataset 정의는 ai_native.* 모델 기반
3. 대시보드 export/import는 YAML (dashboards/superset_exports/)

대시보드:
- advertiser_roi.yaml
- creator_rank.yaml
- campaign_ops.yaml

쿼리 최적화 실험 (반드시 기록):
1. 각 대시보드 차트의 쿼리를 수집해 EXPLAIN ANALYZE 실행
2. 초기 load time, 총 planning/execution time, shared reads 기록
3. 개선안 적용:
   a) B-tree / BRIN / GIN(for jsonb) 인덱스
   b) 일부 차트용 머티리얼라이즈드 뷰
   c) dbt에서 집계 테이블 선계산
4. Before/After 비교 테이블 metrics/query_optimization_log.md 에 저장 (ms, %개선, 사용된 기법)

반드시 기록할 항목:
- 쿼리 원본
- EXPLAIN plan 요약
- 적용 기법
- 개선율 %
- 이 최적화가 운영환경에서 가지는 함의

면접 대비 부록:
- docs/traffic_experiments.md 에 "대시보드 트래픽이 10배로 늘면?" 시나리오 분석 (커넥션 풀, 캐시, 집계 테이블, Superset async queries)

완료 후 최적화 before/after 표를 보여줘.
````

---

### Phase 6 — Text2SQL BI Agent (⭐ JD 가장 핵심) (1주 반~2주)

**Goals**
- LangChain 기반 Text2SQL Agent
- Schema-aware retrieval (pgvector로 dbt 메타데이터 임베딩)
- 프롬프트 버전 관리 + 평가 프레임워크
- **실패 사례 로그** (면접 골드)

**아키텍처**
```
User Question (자연어, 한/영/중/태)
        │
        ▼
[Schema Retriever]  ← pgvector (dbt yaml의 description/synonyms 임베딩)
        │  top-k 관련 모델·컬럼
        ▼
[SQL Generator]     ← Gemini 2.5 Flash (저비용) / Claude Haiku 4.5 (신뢰성)
        │
        ▼
[Validator]         ← SQL parse / dry-run / LIMIT 자동 삽입 / DELETE·UPDATE 차단
        │
        ▼
[Executor]          ← 읽기 전용 DB 유저
        │
        ▼
[Result Formatter]  ← 표/요약/후속질문 제안
```

**평가셋**
- `agent/eval/dataset.jsonl`: 50~100개 질문
- 난이도: easy(15) / medium(20) / hard(15)
- 다국어: 한 60 / 영 20 / 중국어 10 / 태국어 10
- 각 항목: `{question, gold_sql, gold_result_hash, tags}`

**메트릭**
- **Execution Accuracy**: 결과 hash 일치율
- **Exact Match**: SQL AST 일치율 (참고용)
- **Latency**: p50, p95, p99
- **Token Cost**: 질문당 평균 USD
- **Refuse Rate**: 모호한 질문 안전 거부율

**Claude Code 프롬프트**
````
Phase 6: Text2SQL BI Agent를 LangChain으로 구축한다.

요구사항:
1. agent/ 하위에 chains/, prompts/, eval/ 구조
2. SchemaRetriever:
   - dbt YAML의 description, meta.synonyms, meta.example_questions, column descriptions을 JSON으로 직렬화
   - HuggingFace multilingual embedding (예: BAAI/bge-m3 또는 sentence-transformers/paraphrase-multilingual-mpnet-base-v2) 또는 Gemini embedding
   - pgvector에 적재 (schema: vector_store)
   - top-k (default 8) 반환
3. SQLGenerator:
   - 프롬프트 3개 버전 (prompts/v1_zero_shot.yaml, v2_few_shot.yaml, v3_cot_with_schema.yaml)
   - LLM provider는 env로 교체 가능 (Gemini / Claude / OpenAI)
   - 출력은 SQL + 근거(reasoning)
4. Validator:
   - sqlglot로 parse, SELECT 전용 강제, LIMIT 1000 자동 삽입
   - DELETE/UPDATE/DROP/ALTER/TRUNCATE 차단
   - dry-run (EXPLAIN only)
5. Executor:
   - 읽기 전용 role (agent_readonly) 사용
   - 타임아웃 30s
   - 결과 1000 row 상한
6. 평가 프레임워크:
   - agent/eval/dataset.jsonl: 50개 seed 질문 생성 (한/영/중/태, easy/medium/hard)
   - run_eval.py: 프롬프트 버전별, 모델별로 실행
   - 저장: agent/eval/results/{version}_{model}_{timestamp}.json
   - 집계: Execution Accuracy, Exact Match, Latency p50/p95, Token Cost, Refuse Rate
7. 로깅:
   - 모든 실패 케이스 agent/eval/failure_cases.md 에 자동 append
   - 면접용 설명을 위해 "왜 실패했는가 → 어떻게 고쳤는가" 섹션 구조

면접 대비 필수:
- docs/request_flow.md 에 "사용자가 자연어 질문을 던지면 어떤 단계로 처리되는가"를 다이어그램+텍스트로
- docs/concurrency_notes.md 에 "여러 사용자가 동시에 쿼리할 때 락·커넥션 풀·타임아웃·재시도" 분석

완료 후 평가 결과 표와 가장 흥미로운 실패 케이스 3건 보고.
````

---

### Phase 7 — LLM 자동 리포트 생성 DAG (5일)

**Goals**
- 주간 자동 리포트 DAG
- ai_native 마트에서 핵심 지표 추출 → LLM 요약 → 마크다운·이미지
- 면접 스토리: "데이터 리터러시 확산"

**Claude Code 프롬프트**
````
Phase 7: 주간 자동 인사이트 리포트 DAG를 만든다.

Airflow DAG (weekly_llm_report):
- 매주 월요일 오전 9시 (Asia/Seoul)
- Tasks:
  1. extract_weekly_metrics: ai_native.wide_daily_platform_summary에서 직전 7일 vs 이전 7일 비교
  2. detect_anomalies: z-score 기반 이상치 + 최대 증감 TOP 10
  3. render_charts: matplotlib으로 PNG 3장 (trend, mix, top movers)
  4. generate_summary_ko: Claude Haiku 4.5로 한국어 요약 (bullet, 수치 강조, 원인 추정 금지)
  5. generate_summary_en: 영어 버전
  6. save_report: reports/{YYYY-WW}/
  7. (옵션) notify: Slack webhook

프롬프트 설계 주의:
- 수치는 반드시 데이터에서만 (halucination 방지)
- 컨텍스트 < 8K tokens 유지 (비용·안정성)
- 출력 스키마 Pydantic 검증

메트릭 자동 기록:
- metrics/run_results.jsonl 에 회차별 토큰 비용·실행시간·생성 글자수 append

면접 대비:
- docs/llm_report_design.md 에 "LLM halucination을 어떻게 방지했는가" 서술
````

---

### Phase 8 — 데이터 품질 · 관측성 · CI (5일)

**Goals**
- dbt tests 커버리지 ≥ 80%
- freshness 체크
- Airflow SLA + callback
- GitHub Actions CI

**Claude Code 프롬프트**
````
Phase 8: 데이터 품질 · 관측성 · CI/CD를 강화한다.

1. dbt:
   - source freshness 설정 (warn: 24h, error: 48h)
   - 테스트 커버리지 측정 스크립트 (dbt ls + dbt test 파싱)
   - Elementary 또는 커스텀으로 테스트 결과 → metrics/data_quality_trend.jsonl
2. Airflow:
   - on_failure_callback: Slack/stdout
   - SLA 설정 (각 DAG별)
   - 재시도 정책: exponential backoff, max 3
   - DAG 문서화 doc_md=
3. Observability:
   - pg_stat_statements 덤프 주간 DAG
   - Airflow task duration 히스토그램 스크립트
4. CI (.github/workflows/):
   - lint.yml: ruff + sqlfluff + yamllint
   - dbt-ci.yml: dbt parse → dbt compile → dbt test --select state:modified
   - agent-eval.yml: 평가셋 smoke (5문제) PR마다
5. pre-commit:
   - ruff, sqlfluff, yamllint, detect-secrets

면접 대비:
- docs/reliability_playbook.md: 실패 시나리오 5가지와 대응 (예: 소스 지연, 스키마 변경, LLM API 장애, DB 커넥션 폭증, 디스크 풀)
````

---

### Phase 9 — 문서화 · 데모 · 면접 준비 (1주)

**Goals**
- README 완성 (JD 매핑표 포함)
- 데모 영상 (3~5분)
- 면접 talking points 문서
- Superset 오픈소스 기여 1건 시도

**Claude Code 프롬프트**
````
Phase 9: 최종 문서화와 포트폴리오 준비를 한다.

산출물:
1. README.md (한/영 병기):
   - 1분 피치
   - JD 매핑표
   - 아키텍처 다이어그램 (Mermaid)
   - Quick Start (make up → dbt run → Superset)
   - 주요 스크린샷 4장
   - 메트릭 요약 (섹션 7 데이터 자동 삽입)
2. docs/interview_talking_points.md:
   - STAR 포맷 7개 (섹션 10 참고)
   - 예상 질문 20개 + 답변 요지
   - "가장 어려웠던 기술 문제" 3가지 준비
3. 데모 영상 스크립트 (demo_script.md):
   - 0:00 도메인 소개 (LINE Pay 맥락 연결)
   - 0:30 아키텍처
   - 1:00 Airflow DAG 실행
   - 1:30 dbt docs
   - 2:00 Superset 대시보드
   - 3:00 Text2SQL Agent 데모 (한/영 질문 각 1개)
   - 4:00 주간 리포트
   - 4:30 메트릭·최적화 사례
5. 기여 1건 준비:
   - Apache Superset good first issue 탐색
   - 최소 문서 수정 or plugin idea 1건
````

---

## 6. 면접 대비 — 면접 후기 반영 (⭐)

면접 후기에서 드러난 4가지 핵심 질문 유형을 **프로젝트 안에 실제 산출물로 남겨두면**, 답변할 때 "이건 제가 실제로 측정한 수치인데요…"로 시작할 수 있음.

### 6-1. "가장 어려웠던 프로젝트·기술적 문제"

**프로젝트 안 근거물**
- `agent/eval/failure_cases.md` — Text2SQL 실패 3건 이상 + 해결 과정
- `metrics/query_optimization_log.md` — before/after 쿼리 최적화 사례
- `docs/reliability_playbook.md` — 실패 시나리오 대응

**준비 답변 3개 (미리 시나리오 작성)**
1. **Text2SQL이 다국어(태국어) 질문에서 조인 실패** → 해결: dbt meta.synonyms 한·태 병기 → Execution Accuracy 42% → 71%
2. **20M 행 일별 스냅샷 대시보드 로딩 18초** → 해결: 일자 파티션 + BRIN 인덱스 + 집계 사전 계산 → 1.2초
3. **Airflow backfill 시 동일 파티션 중복 적재** → 해결: idempotent MERGE + unique_key + dbt snapshot invalidate 로직

### 6-2. "사용자 요청이 처리되는 과정"

**산출물**: `docs/request_flow.md`

```
사용자: "지난주 대만에서 가장 ROAS 높은 뷰티 캠페인 Top 5?"
 │
 │ 1. Text2SQL Agent 수신
 │ 2. SchemaRetriever: pgvector 검색 → top-8 관련 모델/컬럼
 │    └ wide_campaign_360 (meta.synonyms: ROAS/광고수익률)
 │ 3. SQLGenerator: CoT 프롬프트 + few-shot → SQL draft
 │ 4. Validator:
 │    a) sqlglot parse OK
 │    b) SELECT only ✓
 │    c) LIMIT 1000 주입
 │    d) EXPLAIN dry-run: 120ms 예상
 │ 5. Executor: agent_readonly 롤로 실행, 타임아웃 30s
 │ 6. ResultFormatter: 표 + 자연어 요약 + 후속 질문 제안
 │ 7. Logging: latency, tokens, cost, 성공여부
```

면접 답변 스크립트:
> "저는 요청 처리 플로우를 7단계로 분리 설계했습니다. 특히 3단계와 4단계 사이에 Validator를 두는 것이 중요했는데, 그 이유는…"

### 6-3. "트래픽 처리"

**산출물**: `docs/traffic_experiments.md`

로컬에서도 **트래픽 실험을 실제로 수행**해서 수치를 남긴다:
1. **Text2SQL Agent**: `locust` 또는 `hey`로 동시 요청 1 / 5 / 10 / 30 수준 실험
   - 기록: p50, p95, 실패율, LLM 토큰 병목
2. **Superset 대시보드**: `ab`로 같은 대시보드 동시 로드
   - 기록: Postgres 커넥션 수, `pg_stat_activity`
3. **Airflow**: 동시 DAG run 수를 `max_active_runs`로 조정
   - 기록: worker 포화 시점, 큐 대기 시간

**준비 답변 템플릿**
> "로컬이긴 하지만 트래픽 실험을 직접 수행했습니다. Text2SQL Agent는 동시 요청 10까지는 p95 2.3초였는데 30부터 Gemini API rate limit에 걸려서 요청 큐잉 + 배치 묶기 + 세션별 캐시를 도입했고, 그 후 30동접까지 p95 3.1초로 안정화됐습니다. 운영 수준의 트래픽 처리는 추가로 Redis 캐시 층과 LLM provider fallback을 얹어야 할 것 같습니다."

### 6-4. "데이터 동시성 처리"

**산출물**: `docs/concurrency_notes.md`

다룰 주제 (프로젝트에 실제 구현해서 근거 만들기):
- **Airflow 동시 DAG run**: `max_active_runs=1` vs `>1`일 때 idempotency
- **dbt incremental**: `unique_key` + `on_schema_change` + `merge` 전략
- **Snapshot 경쟁**: 같은 row가 같은 초에 두 번 업데이트될 때
- **Text2SQL Agent 동시 쿼리**: Postgres 커넥션 풀 (pgbouncer 시뮬), 타임아웃, advisory lock
- **대시보드 vs ETL 충돌**: long-running SELECT vs MERGE, `SET LOCAL statement_timeout`
- **캐시 stampede**: 같은 질문 10명 동시 → LLM 호출 1번으로 dedupe (singleflight)

**준비 답변 템플릿**
> "동시성은 4개 층위에서 다뤘습니다. (1) 파이프라인 레벨에선 Airflow max_active_runs과 dbt의 unique_key 기반 MERGE로 idempotency를 보장했고, (2) 데이터 레이어에선 SCD Type 2 snapshot의 경쟁 조건을 다뤘고, (3) 서빙 레이어에선 Postgres 커넥션 풀과 statement_timeout을, (4) Agent 레벨에선 같은 질문에 대한 singleflight로 LLM 중복 호출을 막았습니다."

### 6-5. "해온 업무·처리 프로세스"

> Aimers에서의 실제 업무 경험 + 이 프로젝트에서 같은 문제를 **일반화·정형화**한 것이라는 내러티브가 가장 강력.

**연결 스크립트 (예시)**
> "Aimers에서는 6,000개 계정 ETL을 EWMA 스코어링 기반으로 운영했는데, 현업에서는 주기적으로 '이 카테고리에서 최근 이상치 크리에이터가 누구냐' 같은 애드혹 질문이 쏟아졌습니다. 이걸 매번 분석가가 SQL을 짜주는 게 병목이었고, 이번 AdInsight Agent 프로젝트는 그 병목을 AI Native 데이터 마트와 Text2SQL Agent로 해소하는 범용화된 해법을 제 힘으로 설계·구현한 것입니다."

---

## 7. 포트폴리오 지표 자동 기록 체계 (⭐)

`metrics/` 디렉토리 아래에 **모든 단계가 끝나면 한 줄씩 추가되는 구조**. 나중에 README·이력서에 바로 인용.

### 7-1. `metrics/run_results.jsonl` (machine-readable)

```jsonl
{"phase":"p2","step":"generate_synthetic","ts":"2026-04-20T21:00:00+09:00","rows":20000000,"size_mb":1450,"duration_s":1180,"seed":42}
{"phase":"p3","step":"dbt_run","ts":"2026-04-27T23:10:00+09:00","models":47,"tests":112,"test_cov_pct":84,"duration_s":73}
{"phase":"p5","step":"query_opt","query_id":"q_advertiser_roi_top10","before_ms":18430,"after_ms":1190,"improvement_pct":93.5,"techniques":["brin_index","mv","dbt_agg"]}
{"phase":"p6","step":"text2sql_eval","model":"gemini-2.5-flash","prompt_ver":"v3","n":50,"exec_acc":0.78,"exact_match":0.34,"p95_ms":2430,"avg_cost_usd":0.0021}
```

### 7-2. `metrics/portfolio_metrics.md` (human-readable, README에 삽입)

```markdown
# AdInsight Agent Portfolio Metrics (자동 생성)

## Pipeline
- 합성 데이터 규모: 20M rows / 1.45GB (Parquet)
- 생성 재현성: seed 고정, 1,180초

## dbt
- 모델 수: 47 (staging 18 / intermediate 9 / marts 14 / ai_native 6)
- 테스트 수: 112 (커버리지 84%)
- 문서 커버리지: 96%
- 최장 모델 실행: fct_post_daily 38초
- snapshot: 1개 (creator_snapshot, SCD2)

## Query Optimization
| Query | Before | After | Δ | 기법 |
|---|---|---|---|---|
| q_advertiser_roi_top10 | 18.4s | 1.19s | **-93.5%** | BRIN + MV + 사전집계 |
| q_creator_rank_7d | 9.8s | 0.84s | **-91.4%** | 파티션 프루닝 + CTE 재구조화 |
| q_campaign_ops_dashboard | 12.1s | 1.67s | **-86.2%** | Composite Index |

## Text2SQL BI Agent
- 평가셋: 50 질문 (한 30 / 영 10 / 중 5 / 태 5, easy 15 / medium 20 / hard 15)
- 최고 조합: gemini-2.5-flash + v3_cot_with_schema
  - Execution Accuracy: **78%**
  - Exact Match: 34%
  - Latency p95: 2.43s
  - 평균 비용: $0.0021/query
- 안전성: Refuse Rate (모호 질문) 100%, DELETE/DROP 차단 100%

## LLM Weekly Report
- 자동 리포트 회차: 8
- 평균 생성 시간: 52초
- 평균 토큰 비용: $0.015/회
- halucination 비율 (수동 검증): 0% (5% 이상 수치 오차 기준)

## Traffic Experiments
- Text2SQL Agent: 30 concurrent req까지 p95 3.1s 안정
- Superset: 20 concurrent dashboard load 평균 2.1s
```

### 7-3. 자동 기록 유틸리티

`metrics/recorder.py`:
```python
import json, datetime, pathlib
def log(phase:str, step:str, **kv):
    rec = {"phase":phase, "step":step, "ts":datetime.datetime.now().astimezone().isoformat(), **kv}
    pathlib.Path("metrics/run_results.jsonl").open("a").write(json.dumps(rec, ensure_ascii=False)+"\n")
```

각 DAG/스크립트 끝에서 `log("p3","dbt_run", models=47, ...)` 호출. Phase 9에서 jsonl → markdown 렌더링 스크립트 작성.

---

## 8. 자주 놓치는 포인트 체크리스트 (DE 일반)

- [ ] **Idempotency**: 같은 파티션 재실행 시 중복 없음 (MERGE / upsert)
- [ ] **Backfill**: 과거 특정 날짜만 재처리하는 명시 DAG 존재 (`backfill_helper.py`)
- [ ] **SCD Type 2**: creator.follower_count·category 변경 이력
- [ ] **타임존**: 모든 raw timestamp는 UTC 저장, 표시 시점에 지역 변환
  - TW: Asia/Taipei, TH: Asia/Bangkok, KR: Asia/Seoul, JP: Asia/Tokyo
  - `dim_region`에 timezone 컬럼
- [ ] **스키마 진화**: dbt `on_schema_change='append_new_columns'` + CI에서 breaking change 탐지
- [ ] **PII 마스킹**: email / handle → hash (staging에서 바로). 원본은 raw에만
- [ ] **데이터 리니지**: dbt docs가 기본, README에 링크
- [ ] **늦게 도착한 데이터**: `updated_at` watermark + re-materialize 윈도우 3일
- [ ] **워터마크**: incremental high-watermark를 seed 테이블 또는 Airflow Variable로
- [ ] **데이터 컨트랙트**: staging ↔ marts 사이에 `source` freshness + required columns
- [ ] **테스트 피라미드**:
  - 단위: 매크로/파이썬 함수 (pytest)
  - 컴포넌트: DAG import 테스트
  - 데이터: dbt tests
  - e2e: smoke DAG
- [ ] **로깅·재시도**: Airflow retries, exponential backoff, on_failure_callback
- [ ] **시크릿**: `.env` + `.gitignore`, `detect-secrets` pre-commit
- [ ] **CI/CD**: dbt parse/compile/test PR마다
- [ ] **비용 시뮬**: LLM 호출 건당 비용 기록 → 월간 추정
- [ ] **문서**: README, data dictionary, architecture, request flow, concurrency, traffic, interview talking points — 이 7개는 필수
- [ ] **README에 "Known Limitations"**: 솔직하게 적기 (오히려 시니어는 플러스 평가)
- [ ] **라이선스**: 공개 데이터셋 출처·라이선스 명시
- [ ] **재현성**: seed 고정, Dockerfile pin, uv.lock 커밋

### 놓치기 쉬운 Mac 전용 함정
- Airflow `logs/` 권한 (AIRFLOW_UID=50000) 미설정 시 부팅 실패
- Postgres 데이터 볼륨 (`pgdata`) 재생성 시 extension 재설치 필요 → `infra/postgres/init/` 확실히
- Docker Desktop 메모리 부족 시 Airflow scheduler가 silent kill → 먼저 Desktop 메모리부터 확인
- 한글 파일명·로케일 이슈 방지: 컨테이너 `LANG=C.UTF-8`

---

## 9. LINE Pay 특화 차별화 포인트

### 9-1. 다국가 모델링 (TW·TH·KR·JP)
- `dim_region` + `dim_currency` + `fact_fx_rate`
- 통화 환산 매크로 `{{ fx_convert('amount_local', 'currency', 'USD', 'tx_date') }}`
- 지역별 비즈 규칙: 예) 태국은 한국보다 숏폼 점유율 높음 → 합성 데이터 분포에 반영

### 9-2. 광고 추천 관점 지표 (LINE Pay 광고 서비스)
- **CTR / CVR / ROAS / CPM / CPC** — 광고주 관점
- **Reach / Frequency / Completion rate** — 도달 관점
- **Creator-Advertiser fit score** — 매칭 추천 시뮬 (간단한 content-based)

### 9-3. LINE 메신저 생태계 맥락
- `docs/linepay_context.md` 에 "LINE Pay가 LINE 메신저 내 광고와 결합되는 지점"에 대한 본인 해석 (1페이지)
- 면접에서 LINE Pay 서비스를 이해하고 있음을 드러내는 장치

### 9-4. 컴플라이언스 인식
- PII 해싱, 데이터 레지던시 주석, 액세스 롤 분리 (agent_readonly, analyst_ro, admin) — 전부 **주석과 문서로라도** 구현

### 9-5. Superset 오픈소스 기여 (JD 명시 우대)
가능한 기여 시도:
- **문서 수정 PR**: 한국어 사용자가 흔히 겪는 설치 이슈 문서 보강
- **i18n**: 한국어/태국어/번체중 번역 누락 보완
- **good first issue**: Superset GitHub `good first issue` 라벨 탐색 → 작은 UI/docs 버그
- **Plugin 아이디어 문서**: 인플루언서 시계열 특화 시각화 제안서 (PR 전에 issue로 제출해도 기여로 인정)

> 시간이 촉박하면 **PR까지 아니어도 issue 1건 등록 + 로컬 빌드 성공 스크린샷**만으로도 면접에서 이야깃거리가 됨.

### 9-6. 리모트/하이브리드 근무 대비
- JD에 LINE Hybrid Work 2.0 언급 → 프로젝트 README에 "비동기 협업을 전제한 문서화" 섹션 추가. 모든 의사결정을 ADR(Architecture Decision Record) 포맷으로 남기기 (`docs/adr/0001-why-postgres-not-duckdb.md`)

---

## 10. STAR 포맷 면접 토크포인트 7선

면접 전에 `docs/interview_talking_points.md`에 **본인 말투로** 다듬어 저장.

1. **AI-Native 데이터 마트 설계**
   - S: LLM Agent가 일반 마트에서 조인 실수로 틀린 답을 반복
   - T: Agent가 쉽게 쓸 수 있는 전용 레이어를 별도 설계
   - A: 비정규화 + semantic naming + dbt meta(synonyms/example_questions) + glossary seed
   - R: Execution Accuracy 42% → 78% (+36%p)

2. **Text2SQL 평가 프레임워크**
   - S: 프롬프트 iteration 효과를 주관적으로 판단 중
   - T: 재현 가능한 평가셋·지표 구축
   - A: 50문 다국어 평가셋, 5개 지표 자동 측정
   - R: v1→v3 정확도 +21%p, 비용 -34%

3. **쿼리 최적화**: 대시보드 로딩 18.4s → 1.19s

4. **동시성 설계**: Agent singleflight + readonly role + statement_timeout + pgbouncer 시뮬

5. **LLM Halucination 방지**: 수치는 데이터에서만, Pydantic 검증, 5% 이상 오차 0건

6. **Airflow 백필·idempotency**: MERGE + watermark + 3일 윈도우 re-materialize

7. **Aimers 실무 경험 → 프로젝트 일반화**: EWMA 스코어링 + SCD2 + 자연어 질의 병목 해소

---

## 11. Superset 기여 플랜 (우대사항 직격)

1. **저장소 클론 → arm64 빌드** 성공 스크린샷
2. **이슈 탐색**: `label:"good first issue" is:open` 5건 shortlist
3. **문서 1건**: 한국어 사용자 FAQ / 오타 수정 수준으로 부담 낮게 시작
4. **PR 1건**: 위 선택 이슈 해결
5. **면접 스토리**: "오픈소스 기여 경험을 만들기 위해 Superset에 기여했고, 빌드·이슈·코드베이스 구조를 실제로 살펴봤습니다."

> 시간 없으면 **PR 대신 issue 1건 등록 + 재현 Dockerfile 공유**로도 화두가 됨.

---

## 12. 타임라인 (주 10~12시간, 약 10주)

| 주차 | Phase | 목표 | MVP 필수 여부 |
|---|---|---|---|
| 1 | P1 | 환경·compose·smoke DAG | ✅ |
| 2 | P2 | 합성+공개 데이터 적재 | ✅ |
| 3 | P2 마무리 + P3 시작 | dbt staging·intermediate | ✅ |
| 4 | P3 | marts + SCD2 | ✅ |
| 5 | P4 | **ai_native 레이어** | ✅ |
| 6 | P5 | Superset 대시보드 + 쿼리 최적화 | ✅ |
| 7 | P6 | **Text2SQL Agent** | ✅ |
| 8 | P6 | 평가셋 + iteration | ✅ |
| 9 | P7 + P8 | 자동 리포트 + 품질/CI | 🔶 |
| 10 | P9 | 문서화·데모·면접 준비 | ✅ |

**MVP (시간 부족 시 스트레치 컷)**
- MVP 필수: P1, P2, P3, P4, P5 일부, P6 ← **이게 JD 핵심 5개 전부**
- 스트레치: P7 주간 리포트, P8 CI 전체, P9 데모 영상, Superset 기여

**하루 루틴 제안**
- 평일 저녁 1.5시간: Claude Code로 1 task
- 주말 4~5시간: 통합 테스트·리팩토링·문서화

---

## 13. Claude Code 활용 팁

### 13-1. 세션 구조
- **Phase 단위로 세션 분리**. 한 세션이 너무 길어지면 컨텍스트 노이즈↑
- 각 세션 시작에 `CLAUDE.md`를 읽히고, **직전 Phase 완료 요약**을 붙여넣기

### 13-2. 유용한 패턴
- `"먼저 계획을 번호 매겨 제시하고, 내 confirm 후 구현해"` — 섣부른 대규모 변경 방지
- `"변경 범위는 파일 X, Y만. 나머지는 건드리지 마"` — 이탈 방지
- `"완료 후 metrics/run_results.jsonl에 한 줄 append"` — 지표 자동 기록 강제
- `"제약 조건 상충하면 구현 전에 질문"` — 추측 코딩 방지
- `"각 단계 마지막에 make test 통과 확인"` — 릴리스 게이트

### 13-3. `CLAUDE.md` 템플릿 (루트에 저장)

```markdown
# AdInsight Agent — Claude Code Context

## 프로젝트 한줄 목표
LINE Pay AI Insight Engineer JD 타깃 포트폴리오. 인플루언서 광고 성과 분석 + AI-Native data mart + Text2SQL BI Agent.

## 실행 환경
- MacBook (Apple Silicon)
- Docker Desktop (메모리 12GB 할당)
- Python 3.11, uv
- Postgres 16 + pgvector, Airflow 2.9, dbt-postgres 1.8, Superset 4.x, LangChain

## 작성 언어
- 코드 주석·README·문서는 **한국어 우선**, 필요 시 영문 병기
- 변수·함수·테이블명은 영어 snake_case

## 불변 규칙
1. raw 레이어는 원본 보존. 모든 변환은 staging 이후.
2. 모든 SQL은 dbt 모델로 관리. 애드혹 SQL은 `docs/` 또는 메모에만.
3. PII(이메일·실명)는 staging에서 즉시 해시. raw 외부 노출 금지.
4. 모든 파이프라인은 idempotent. MERGE / upsert 패턴.
5. 타임스탬프는 UTC 저장. 표시 시 지역 변환.
6. 모든 ai_native 모델은 dbt YAML meta에 synonyms, example_questions, grain 명시.
7. Text2SQL Agent는 반드시 validator를 통과한 SELECT만 실행.
8. 지표 기록은 `metrics/recorder.py` 사용.

## 디렉토리 규칙
- infra/: docker, compose, init SQL
- dags/: Airflow
- dbt/: dbt project
- agent/: Text2SQL
- data_generation/: 합성 데이터
- metrics/: 자동 기록
- docs/: 면접·아키텍처 문서

## 작업 방식
- 먼저 계획을 번호 매겨 제시 → 사용자 confirm → 구현
- 한 번에 너무 많은 파일을 건드리지 말 것
- 변경 후 반드시 관련 테스트 실행
- 각 Phase 완료 시 metrics/run_results.jsonl 에 append
- 모호하면 질문. 추측 코딩 금지.

## 현재 Phase
(여기를 매 세션 시작마다 업데이트)
```

### 13-4. Makefile 예시

```makefile
.PHONY: up down logs psql airflow-cli superset-init dbt-run test fmt lint

up:
	docker compose up -d
	@echo "Airflow: http://localhost:8080 | Superset: http://localhost:8088"

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

psql:
	docker compose exec postgres psql -U postgres -d adinsight

airflow-cli:
	docker compose exec airflow-webserver airflow $(cmd)

superset-init:
	docker compose exec superset superset fab create-admin --username admin --password admin --firstname a --lastname b --email a@b.c
	docker compose exec superset superset db upgrade
	docker compose exec superset superset init

dbt-run:
	docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt run"

dbt-test:
	docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt test"

test:
	uv run pytest -q

fmt:
	uv run ruff format .
	uv run sqlfluff fix dbt/models

lint:
	uv run ruff check .
	uv run sqlfluff lint dbt/models
```

---

## 14. 바로 시작할 수 있는 Claude Code 부트스트랩 프롬프트

프로젝트 첫 세션에 그대로 붙여넣기:

```
이 프로젝트는 "AdInsight Agent"라는 이름의 DE 포트폴리오입니다.

첨부한 설계 문서(LINE Pay 포트폴리오 프로젝트 설계서)의 내용을 기준으로 작업합니다.
나는 Yeon이고, Aimers에서 인플루언서 데이터 엔지니어링 업무를 하며 DE로 전환 준비 중입니다.
로컬 환경은 MacBook (Apple Silicon, Docker Desktop, 메모리 12GB 할당).

먼저 해줄 일:
1. 위 문서의 폴더 구조(섹션 4)와 CLAUDE.md 템플릿(섹션 13-3)을 참고해 프로젝트 루트 스켈레톤을 생성
2. CLAUDE.md를 루트에 배치 (섹션 13-3 템플릿 그대로, "현재 Phase"만 "Phase 1 — 환경 셋업"으로)
3. Makefile, pyproject.toml (uv 기반), .env.example, .gitignore
4. 빈 디렉토리에는 .gitkeep
5. README.md 초안 (JD 매핑표 + Quick Start 섹션 자리만)

작업 규칙:
- 먼저 생성할 파일 목록과 각 파일의 역할을 번호 매겨 보여주고, 내 confirm을 받은 뒤에 실제 파일을 만드세요.
- 모호한 부분은 질문. 추측 금지.
- 한국어로 소통하세요.

그다음 Phase 1 구현으로 넘어갑니다.
```

---

## 15. 참고 링크 모음 (북마크용)

> 각 링크는 프로젝트 README 하단 "References"에도 추가 권장.

- Airflow 공식 docs: https://airflow.apache.org/docs/
- dbt 공식 docs: https://docs.getdbt.com/
- Superset docs: https://superset.apache.org/docs/intro/
- Superset GitHub (good first issue 탐색): https://github.com/apache/superset/issues?q=is%3Aopen+label%3A%22good+first+issue%22
- LangChain SQL Toolkit: https://python.langchain.com/docs/use_cases/sql/
- pgvector: https://github.com/pgvector/pgvector
- SDV (Synthetic Data Vault): https://sdv.dev/
- BIRD / Spider (Text2SQL benchmark 참고): https://bird-bench.github.io/ , https://yale-lily.github.io/spider
- dbt Kimball 레퍼런스: Kimball "The Data Warehouse Toolkit" 3rd ed.
- LINE Engineering 블로그 (면접 분위기 파악): https://engineering.linecorp.com/ko

---

## 마지막 — 이 문서를 사용하는 방법

1. 이 문서를 프로젝트 루트에 `docs/project_blueprint.md`로 저장
2. Phase 시작할 때마다 해당 섹션의 **Claude Code 프롬프트 템플릿**을 그대로 복사해 사용
3. Phase 끝나면 `metrics/portfolio_metrics.md` 업데이트 확인
4. **면접 1주 전**에 섹션 6(면접 대비) + 섹션 10(STAR 7선)만 출력해서 오프라인 리뷰
5. **면접 1일 전**에 `docs/request_flow.md`, `docs/concurrency_notes.md`, `docs/traffic_experiments.md` 3개만 재정독

> 이 프로젝트의 진짜 무기는 "만든 것"이 아니라 **"왜 그렇게 만들었는지 설명할 수 있는 근거 문서와 수치"** 입니다. 코드 품질보다 그쪽이 면접에서 훨씬 차별화돼요.

행운을 빕니다 🚀
