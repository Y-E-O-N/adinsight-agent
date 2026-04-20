---
title: "AdInsight Agent 포트폴리오 템플릿"
subtitle: "LINE Pay AI Insight Engineer JD 맞춤 · 구조 · 내용 · 측정 메트릭"
author: "for Yeon"
---

# 이 문서의 목적

AdInsight Agent 프로젝트가 끝났을 때, **"무엇을 · 어디에 · 어떤 형태로"** 보여줄지를 미리 설계해두는 템플릿입니다. 프로젝트 진행 중에 이 문서를 계속 돌아와서 **채워가세요**. 프로젝트가 끝난 뒤 포트폴리오를 "처음부터" 쓰면 이미 놓친 스크린샷·숫자가 많아 힘이 빠져요.

## 이 문서의 구조

1. **포트폴리오 아웃풋 5종** — 어디에 무엇을 둘지
2. **GitHub README 템플릿** (가장 중요)
3. **1-pager PDF 템플릿** (지원서 첨부용)
4. **노션/블로그 서사형 템플릿**
5. **이력서 bullet 템플릿**
6. **면접 토크포인트 매핑**
7. **측정 메트릭 카탈로그** (Phase별)
8. **스크린샷·증거물 체크리스트**
9. **JD 역매핑 표**
10. **최종 완성도 체크리스트**

---

# 1. 포트폴리오 아웃풋 5종

하나의 프로젝트 → 다섯 개의 아웃풋. 각각 **청중과 목적이 다름**.

| # | 아웃풋 | 청중 | 길이 | 목적 |
|---|---|---|---|---|
| 1 | **GitHub 저장소 README** | 기술 면접관 | 스크롤 3~4회 | "무엇을 어떻게 만들었는지" 증거 |
| 2 | **1-pager PDF** | 리크루터 · 1차 서류 | A4 1장 | "시선 30초에 걸려야" |
| 3 | **노션/블로그 회고 글** | 개발 커뮤니티 · 채용담당 | 긴 서사 | "사고 과정과 실패담" |
| 4 | **이력서 bullet 3~5줄** | ATS · 서류 통과 | 4~6줄 | "JD 키워드 hit" |
| 5 | **면접 토크포인트 메모** | 본인 (구두 답변용) | 카드 10장 내외 | "말로 설명 연습" |

### 우선순위
- **필수**: #1 (GitHub README), #4 (이력서), #5 (토크포인트)
- **권장**: #2 (1-pager) — LINE Pay 같은 글로벌 포지션은 1장 요약의 임팩트가 큼
- **선택**: #3 (블로그) — 시간 여유 있을 때. 공개하면 가산점

---

# 2. GitHub README 템플릿

README는 포트폴리오의 **얼굴**입니다. 면접관은 저장소 첫 화면에서 내리는 판단으로 30초~2분 안에 "이 사람의 프로젝트를 더 볼지"를 결정해요. 아래 구조를 따르세요.

## 2.1 전체 구성 (섹션 순서 고정)

```
1. [히어로 블록]   제목 + 1줄 설명 + 배지 + 스크린샷
2. [3줄 요약]     문제 / 해법 / 결과
3. [아키텍처 다이어그램]
4. [JD 매칭 표]   LINE Pay JD 요구사항 ↔ 이 프로젝트의 위치
5. [핵심 결과]    Before/After 수치 6~8개
6. [스택]         한 눈에 아이콘 + 버전
7. [폴더 구조]
8. [Quickstart]   5개 명령어로 띄우기
9. [데이터 모델]  ERD 축소본 + grain 설명
10. [파이프라인]  DAG 스크린샷 + 실행 시간
11. [Text2SQL Agent]  평가 결과 + 실패 사례
12. [쿼리 최적화]  Before/After EXPLAIN
13. [트래픽·동시성]  실험 결과 요약
14. [문서 링크]   docs/ 하위 링크 모음
15. [회고]       배운 점 · 다음 단계 · 한계
16. [저자]       연락처 + 라이선스
```

## 2.2 섹션별 템플릿 (복붙해서 쓰기)

### [1] 히어로 블록

```markdown
# AdInsight Agent — AI-Native Data Mart & Text2SQL BI Agent for Influencer Advertising

> 다국가 인플루언서 광고 성과를 Airflow/dbt 로 AI-Native 마트로 모델링하고,
> LangChain + pgvector 기반 Text2SQL Agent 로 자연어 질의를 제공하는 엔드투엔드 데이터 플랫폼.

![airflow](https://img.shields.io/badge/Airflow-2.9-017CEE?logo=apacheairflow)
![dbt](https://img.shields.io/badge/dbt-1.8-FF694B?logo=dbt)
![postgres](https://img.shields.io/badge/Postgres-16-336791?logo=postgresql)
![pgvector](https://img.shields.io/badge/pgvector-0.7-4169E1)
![superset](https://img.shields.io/badge/Superset-4.0-20A6C9?logo=apachesuperset)
![langchain](https://img.shields.io/badge/LangChain-0.2-1C3C3C)

<p align="center">
  <img src="docs/images/dashboard_hero.png" width="680"/>
</p>
```

**POINT**: 배지는 **실제로 쓴 것만**. 모르는 배지 붙이면 면접에서 찔림.

### [2] 3줄 요약 (TL;DR)

```markdown
## TL;DR

- **Problem** 인플루언서 광고 ROI 분석은 (1) 다국가·멀티플랫폼 데이터 통합 (2) 분석가의 애드혹 SQL 병목 (3) 모호한 지표 정의 로 인해 의사결정이 늦어짐.
- **Solution** Airflow + dbt + Postgres/pgvector + Superset + LangChain 으로 raw → star schema → AI-Native mart → Text2SQL Agent → LLM 주간 리포트까지 단일 파이프라인을 구축.
- **Result** Execution Accuracy **78%** (50문 eval set), 대시보드 쿼리 **18s → 1.2s**, DAG 성공률 **95%+**, 4개 언어(KO/EN/ZH-TW/TH) 지원.
```

> **채우는 법**: Phase 6 끝나고 실제 수치로 교체.

### [3] 아키텍처 다이어그램

```markdown
## Architecture

<p align="center">
  <img src="docs/images/architecture.svg" width="780"/>
</p>

**Layer breakdown**

| Layer | Tool | 역할 |
|---|---|---|
| Ingest | Airflow + Python/SDV | 합성·공개 데이터 생성 + raw 적재 |
| Transform | dbt | staging → intermediate → marts → ai_native |
| Semantic | dbt YAML meta + pgvector | 컬럼 설명·synonyms 임베딩 |
| Serving | Superset / FastAPI | 대시보드 + Text2SQL API |
| Agent | LangChain + LangGraph | retrieve → generate → validate → execute |
| Ops | GitHub Actions + pytest + dbt test | CI · 품질 |
```

**POINT**: SVG 또는 PNG 로 그림 하나. Excalidraw / draw.io / Mermaid 에서 그린 걸 `docs/images/` 에.

### [4] JD 매칭 표 (⭐ 핵심)

```markdown
## JD Alignment (LINE Pay · AI Insight Engineer)

| JD 요구사항 | 이 프로젝트의 위치 | 증거 |
|---|---|---|
| AI-Native Data Mart 설계 | `dbt/models/ai_native/*` | [wide_campaign_360.sql](dbt/models/ai_native/wide_campaign_360.sql) |
| Airflow ETL 파이프라인 | `dags/ingest_synthetic.py` + `dags/dbt_run.py` | [DAG 스크린샷](docs/images/dag_ingest.png) |
| Tableau/Superset 대시보드 | `dashboards/superset_exports/` | [광고주 ROI 대시보드](docs/images/dashboard_advertiser.png) |
| LLM 자동 리포트 | `dags/weekly_llm_report.py` | [샘플 리포트](docs/reports/2026-04-07.md) |
| Text2SQL BI Agent | `agent/chains/` + `agent/eval/` | [평가 결과](docs/agent_eval.md) |
| 쿼리 최적화 | BRIN + 복합 B-tree + 파티셔닝 | [Before/After EXPLAIN](docs/query_tuning.md) |
| Pandas · API 연동 | `data_generation/` + FastAPI | [API spec](docs/api_spec.md) |
| LangChain/OpenAI (우대) | `agent/chains/pipeline.py` | Gemini+Claude dual provider |
| Vector DB (우대) | pgvector hnsw | [임베딩 스크립트](agent/embeddings/) |
| Superset 기여 (우대) | 한국어 i18n PR #XXXXX | [PR 링크](...) |
| 글로벌 협업 (우대) | 영문 README 병행, 4개 언어 지원 | [README.en.md](README.en.md) |
```

> **이 표 하나가 포트폴리오의 핵심**. 면접관이 JD 출력물을 들고 왔을 때 한 표로 답할 수 있어야 함.

### [5] 핵심 결과 (Key Results)

```markdown
## Key Results

| 지표 | Before | After | 방법 |
|---|---:|---:|---|
| 대시보드 쿼리 응답 (광고주 ROI) | 18.3s | **1.2s** | BRIN + 복합 B-tree + 사전집계 |
| Text2SQL Execution Accuracy | 42% (v1) | **78%** (v3) | AI-Native 마트 + few-shot + CoT |
| 다국어 커버리지 | KO only | **KO/EN/ZH-TW/TH** | bge-m3 임베딩 교체 |
| 주간 리포트 생성 시간 | — | **3분 12초** | Airflow + Gemini Flash |
| DAG 성공률 (30일) | — | **96.7%** | retry + idempotent + sensor |
| dbt test 커버리지 | — | **컬럼의 84%** | generic + custom test |
| 동시 30명 p95 응답 | — | **3.1s** | singleflight + cache |
```

**POINT**: 비교 가능한 "Before / After" 가 없으면 **"목표 vs 달성"** 으로 대체. 아무것도 없는 칸은 둬도 됨 (채워넣는 순간 거짓).

### [6] 스택

```markdown
## Stack

- **Orchestration** Apache Airflow 2.9 (CeleryExecutor)
- **Transform** dbt-postgres 1.8 + dbt-utils + dbt-expectations
- **Warehouse** PostgreSQL 16 + pgvector 0.7 + pg_trgm + pg_stat_statements
- **BI** Apache Superset 4.0
- **Agent** LangChain 0.2 + LangGraph + sqlglot + FastAPI
- **LLM** Gemini 2.5 Flash (primary) · Claude Haiku 4.5 (fallback)
- **Embeddings** BAAI/bge-m3 (1024d, multilingual)
- **DevOps** Docker Compose + GitHub Actions + uv + pre-commit
- **Lang** Python 3.11 · SQL · Jinja
```

### [7] 폴더 구조

```markdown
## Project Structure

\```
adinsight/
├── infra/                # docker-compose, init SQL, env templates
├── dags/                 # Airflow DAGs (ingest, dbt_run, llm_report)
├── dbt/
│   └── models/
│       ├── staging/      # 1:1 정제
│       ├── intermediate/ # ephemeral 계산
│       ├── marts/        # star schema fact/dim
│       └── ai_native/    # 비정규화 + semantic metadata
├── data_generation/      # SDV 합성 + 공개 데이터 로더
├── agent/
│   ├── chains/           # retriever / generator / validator / executor
│   ├── prompts/          # v1/v2/v3 YAML
│   ├── embeddings/       # pgvector 적재
│   └── eval/             # 평가셋 + 러너
├── api/                  # FastAPI Text2SQL endpoint
├── dashboards/           # Superset exports (YAML)
├── metrics/              # run_results.jsonl + 차트
├── docs/                 # 보고서 · 스크린샷 · ADR
└── tests/                # pytest unit tests
\```
```

### [8] Quickstart

```markdown
## Quickstart

요구사항: Docker Desktop (메모리 12GB+), Python 3.11, uv.

\```bash
git clone https://github.com/<you>/adinsight.git
cd adinsight
cp .env.example .env     # POSTGRES_PASSWORD 등 채우기
make up                  # compose up + 헬스체크 대기
make seed                # 합성 데이터 + dbt seed
make dbt                 # dbt run + test + snapshot
make agent-index         # pgvector 에 스키마 임베딩 적재
make demo                # 샘플 질문 10개 실행
\```

- Airflow UI: http://localhost:8080  (admin/admin)
- Superset: http://localhost:8088
- Text2SQL API: http://localhost:8001/docs
```

**POINT**: 면접관이 "실제로 돌려볼 수 있다"는 인상이 가장 강력. `make` 한두 단계로 돌아가야 함.

### [9] 데이터 모델

```markdown
## Data Model

**Bus Matrix** (conformed dimension)

|                        | dim_date | dim_creator | dim_advertiser | dim_region | dim_currency |
|------------------------|:--------:|:-----------:|:--------------:|:----------:|:------------:|
| fct_post_daily         |    ✓     |      ✓      |                |     ✓      |              |
| fct_campaign_performance |  ✓     |      ✓      |       ✓        |     ✓      |       ✓      |
| fct_payment            |    ✓     |             |       ✓        |     ✓      |       ✓      |

**Grain 선언** (fact table 별 1 row 의 의미)

- `fct_post_daily`: **1 row = 1 creator × 1 day × 1 platform**
- `fct_campaign_performance`: **1 row = 1 campaign × 1 day × 1 region**
- `fct_payment`: **1 row = 1 payment event**

**SCD** `dim_creator_scd` — Type 2 (follower_count, category, region 변경 감지)

<p align="center">
  <img src="docs/images/erd_ai_native.svg" width="720"/>
</p>
```

### [10] 파이프라인

```markdown
## Pipeline

### DAGs

| DAG | 스케줄 | 역할 | 평균 실행 시간 |
|---|---|---|---:|
| `ingest_synthetic` | `@daily 02:00` | raw 적재 | 1m 48s |
| `dbt_run` | `@daily 03:00` | staging → marts → ai_native | 4m 12s |
| `weekly_llm_report` | `@weekly Mon 04:00` | LLM 주간 리포트 | 3m 12s |

### Idempotency

- **DELETE+INSERT** 패턴으로 Airflow task 재실행/backfill 5회 무손실 검증
- dbt `incremental + merge + unique_key` 로 upsert
- 백필 명령: `airflow dags backfill dbt_run --start-date 2026-03-01 --end-date 2026-03-31`

![DAG Screenshot](docs/images/dag_dbt_run.png)
```

### [11] Text2SQL Agent

```markdown
## Text2SQL Agent

### 요청 처리 플로우 (7단계)

1. FastAPI 수신 (Semaphore 30 + singleflight)
2. 질문 → bge-m3 임베딩 → pgvector top-8 retrieve
3. v3 프롬프트 (CoT + few-shot + schema) → Gemini 2.5 Flash
4. sqlglot 파싱 → SELECT/LIMIT/금지어 검증 → EXPLAIN 드라이런
5. `agent_readonly` 역할로 `statement_timeout 30s` 실행
6. 표 + 자연어 요약 + 후속 질문 3개
7. `metrics/run_results.jsonl` 에 latency·tokens·cost 기록

### Evaluation

- **데이터셋**: 50문 (KO 20 · EN 15 · ZH-TW 8 · TH 7)
- **난이도**: Easy 18 · Medium 22 · Hard 10
- **지표**: Execution Accuracy (집합 일치), p50/p95 latency, cost/query, Refuse Rate

| Version | Prompt | Model | Exec Acc | p50 | p95 | $/query |
|---|---|---|---:|---:|---:|---:|
| v1 | naive | Gemini Flash | 42% | 1.8s | 4.9s | $0.0012 |
| v2 | + schema retrieval | Gemini Flash | 64% | 2.1s | 5.4s | $0.0018 |
| **v3** | **+ few-shot + CoT** | **Gemini Flash** | **78%** | **2.4s** | **6.1s** | **$0.0022** |
| v3 | same | Claude Haiku 4.5 | 82% | 3.1s | 7.8s | $0.0041 |

**실패 사례 3선** → [docs/failure_cases.md](docs/failure_cases.md)

1. 태국어 "จำนวนผู้ติดตาม" ↔ follower_count 매칭 실패 (synonyms 보강으로 해결)
2. ROAS 계산 시 `AVG(roas)` 선택 — non-additive 교정 필요 (프롬프트 rule 추가)
3. "지난달" 해석의 월 경계 버그 (date helper 함수 제공)
```

### [12] 쿼리 최적화

```markdown
## Query Optimization

### Case: 광고주 ROI 대시보드 (fct_campaign_performance 20M rows)

**Before** — 18.3s, Seq Scan 19.8M rows removed by filter

\```
Seq Scan on fct_campaign_performance  (cost=0.00..185234 rows=42 width=120)
  (actual time=0.021..18234 rows=156234 loops=1)
  Filter: (region = 'TW' AND date BETWEEN '...')
  Rows Removed by Filter: 19843766
\```

**조치**
1. `ANALYZE fct_campaign_performance;` (통계 갱신)
2. `CREATE INDEX ... USING BRIN (date) WITH (pages_per_range=64);`
3. `CREATE INDEX ... (region, date);` (복합 B-tree)
4. `marts/agg_advertiser_daily.sql` 사전 집계 추가
5. dbt exposure 로 Superset dashboard 연결

**After** — **1.19s**, Index Scan + Bitmap Heap Scan

\```
Bitmap Heap Scan on fct_campaign_performance  (actual time=12.4..1180 rows=156234)
  Recheck Cond: ((region = 'TW') AND (date >= ...) AND (date <= ...))
  Heap Blocks: exact=8234
  ->  Bitmap Index Scan on idx_region_date  (actual time=8.9..8.9 rows=156234)
\```

→ **15x 개선**. 자세한 과정: [docs/query_tuning.md](docs/query_tuning.md)
```

### [13] 트래픽·동시성

```markdown
## Traffic & Concurrency Experiments

| 실험 | 도구 | 조건 | p50 | p95 | p99 | 성공률 |
|---|---|---|---:|---:|---:|---:|
| Text2SQL Agent 30 동접 | locust | 2min | 2.4s | 3.1s | 5.8s | 99.2% |
| Superset 대시보드 10 동접 | ab | n=200 | 620ms | 1.2s | 1.8s | 100% |
| Airflow max_active_runs=3 | — | 백필 7일 | — | — | — | 100% |

**설계 포인트**

- FastAPI `asyncio.Semaphore(30)` + 대기열 100 초과 시 503 (back-pressure)
- **Singleflight** 로 같은 질문 해시 dedupe — 30개 동시 요청 중 실제 LLM 호출 **1회** (관측)
- Gemini 429 시 **exponential backoff** + Claude 로 자동 fallback
- Postgres `statement_timeout 30s` + `agent_readonly` 읽기 전용 롤

상세: [docs/traffic_experiments.md](docs/traffic_experiments.md)
```

### [14] 문서 링크

```markdown
## Documentation

- [프로젝트 설계서 (Blueprint)](docs/blueprint.md)
- [ADR 1 — 왜 Postgres 단일 스택인가](docs/adr/001-single-postgres.md)
- [ADR 2 — 왜 Kimball star schema 인가](docs/adr/002-star-schema.md)
- [ADR 3 — 왜 AI-Native 레이어를 별도로 두는가](docs/adr/003-ai-native-layer.md)
- [Request Flow 다이어그램](docs/request_flow.md)
- [Concurrency Notes](docs/concurrency_notes.md)
- [Traffic Experiments](docs/traffic_experiments.md)
- [Query Tuning Report](docs/query_tuning.md)
- [Agent Evaluation Report](docs/agent_eval.md)
- [Failure Cases](docs/failure_cases.md)
- [Interview Talking Points](docs/interview_talking_points.md)
```

### [15] 회고

```markdown
## Retrospective

### 배운 것
- dbt incremental + merge 의 힘: idempotent 파이프라인의 실제 작동 방식
- AI-Native 레이어가 Agent 정확도에 미치는 영향 (42% → 78%)
- EXPLAIN ANALYZE 를 읽는 습관이 인덱스 설계에 주는 확신
- LLM 을 신뢰하지 않고 DB 레벨까지 다층 방어를 설계하는 법

### 한계
- 단일 Postgres 로 OLTP/OLAP 을 함께 — 실제 프로덕션에선 Hadoop/BigQuery 가 맞음
- 합성 데이터라 실제 트래픽 패턴과 차이 있음
- 평가셋 50문은 표본이 작음. 다국어 커버리지는 상징적 수준

### 다음 단계
- Great Expectations 도입, lineage/freshness 알림 Slack 연동
- dbt-postgres → dbt-bigquery 이식, 파티셔닝 비교
- Agent 에 "질문 재작성(query rewriter)" 노드 추가로 모호한 질문 처리 개선
```

### [16] 저자 · 라이선스

```markdown
## Author

**Yeon** — Data/AI Engineer
- GitHub: [@handle](https://github.com/handle)
- LinkedIn: [linkedin.com/in/handle](https://linkedin.com/in/handle)
- Email: you@example.com

## License

MIT — 데이터는 합성 및 공개 데이터셋만 사용.
```

---

# 3. 1-pager PDF 템플릿

리크루터가 30초 안에 판단할 수 있는 한 장짜리. A4 portrait. **이력서와 별도**로 지원서 첨부에 보내거나, 본인 사이트에서 다운로드.

## 3.1 레이아웃 (A4 기준)

```
┌─────────────────────────────────────────────────┐
│  [헤더] 이름 + 포지션 지향 + 연락처 (1줄씩)         │
├─────────────────────────────────────────────────┤
│  AdInsight Agent                                       │
│  AI-Native Data Mart & Text2SQL BI Agent         │
│                                                  │
│  [3줄 요약]                                      │
├─────────────────────────────────────────────────┤
│  [아키텍처 그림 축소본]   │   [핵심 결과 4칸]     │
│                          │   - Exec Acc 78%      │
│                          │   - 18s → 1.2s        │
│                          │   - 4 lang            │
│                          │   - 95%+ DAG success  │
├─────────────────────────────────────────────────┤
│  [스택 아이콘 한 줄]                             │
├─────────────────────────────────────────────────┤
│  [JD 매핑 요약 5개]                              │
│  ✔ AI-Native Data Mart    → dbt ai_native/*     │
│  ✔ Airflow ETL            → 3 DAG, idempotent   │
│  ✔ Text2SQL BI Agent      → LangChain + pgvec   │
│  ✔ Superset Dashboards    → 3 dashboards        │
│  ✔ Query Optimization     → 18s→1.2s, 15x       │
├─────────────────────────────────────────────────┤
│  [링크 3개] GitHub · Demo · 회고 블로그          │
└─────────────────────────────────────────────────┘
```

## 3.2 만드는 법

- **Notion → PDF export**: 한 페이지에 맞게 양 조절
- **또는** `pandoc` + LaTeX 템플릿
- **또는** Figma/Canva 로 직접 디자인 (시각 정리 잘 될 때)

## 3.3 필수 요소 체크

- [ ] 이름 + 지향 포지션 (한 줄)
- [ ] 프로젝트 한 줄 설명
- [ ] 아키텍처 1개
- [ ] 핵심 결과 숫자 4개 (크게)
- [ ] JD 키워드 매핑 5~7개
- [ ] GitHub URL QR 또는 짧은 링크
- [ ] 작성일 (버전 관리)

---

# 4. 노션/블로그 서사형 템플릿

GitHub README 가 "레퍼런스" 라면 블로그 글은 "이야기". 긴 글이지만 읽는 사람이 **프로젝트를 하는 당신의 머릿속을 엿볼 수 있게** 쓰는 것이 목적.

## 4.1 구성 (약 3,000~5,000자)

```
[1] 후킹 — "왜 이 프로젝트를 시작했나" (현업 경험과 연결된 pain point)
[2] 문제 정의 — 구체적인 병목 사례 1~2개
[3] 가설 — "이렇게 하면 풀릴 것이다" (설계 결정 3개)
[4] 설계 — 다이어그램 + 의사결정 이유 (ADR 요약)
[5] 구현 스냅샷 — 코드 하이라이트 3~4개 (전체 코드 X)
[6] 실패 — 막혔던 순간 · 잘못 들어선 길 (핵심!)
[7] 개선 - 측정값과 함께 before/after
[8] 회고 — 배운 것 · 한계 · 다음 단계
[9] (선택) JD 와의 연결 — 공개 글에는 톤 조절
```

## 4.2 "실패" 섹션이 가장 중요한 이유

블로그의 진짜 가치는 **실패담**에 있어요. 면접관은 "이 사람이 막혔을 때 어떻게 생각하는지"를 이 섹션에서 봄.

### 실패 섹션 템플릿

```markdown
### 실패 #1: 태국어 질문에서 정확도가 42%로 급락했다

처음엔 전부 한국어 질문으로만 평가셋을 만들었다. 다국어 지원을 표방하면서도
사실상 한국어만 돌고 있었던 셈. 태국어 20문을 추가했더니 **Exec Acc 가 78%에서
42%로 떨어졌다**.

원인을 두 층위로 나눠 디버깅했다.

1. **검색 단계**: pgvector 에서 top-8 청크를 뽑아봤더니, 태국어 질문과 한국어 설명의
   유사도가 구조적으로 낮았다. 임베딩 모델 (multilingual-mpnet-base) 의 한계.
2. **생성 단계**: 검색이 어느 정도 맞아도, LLM 이 한국어 컬럼 설명을 태국어 의도와
   맞추지 못했다.

### 해결 시도

- (A) 임베딩 모델을 `bge-m3` 로 교체 — 다국어 성능이 수치상 월등. 결과: **검색 recall
  66% → 89%**.
- (B) dbt YAML `meta.synonyms` 에 한·영·중·태 4개 언어 유의어를 추가.
- (C) few-shot 에 태국어 예시 3개 편입.

### 결과

태국어 Exec Acc **42% → 71%**. 남은 29% 는 대부분 복합 조인/윈도우 함수가 필요한
hard 케이스. 이건 프롬프트로 풀 문제가 아니라 **ai_native 레이어의 설계 문제**
라는 결론. `agent/eval/failure_cases.md` 에 실패 사례 3건을 정리해뒀다.
```

이런 식의 "**가설 → 디버깅 → 수치 → 결론**" 사이클이 1~2개 있으면 글은 이미 성공.

---

# 5. 이력서 Bullet 템플릿

ATS 를 통과해야 하니 **JD 키워드**가 들어가야 하고, 동시에 면접관이 한 줄만 보고도 "숫자·행동"이 느껴져야 합니다.

## 5.1 포맷 원칙 (XYZ format)

```
[행동 동사] + [무엇을, 어떻게] + [측정 가능한 결과]
```

## 5.2 좋은 Bullet 5개 예시 (한국어)

```
• Airflow + dbt + Postgres/pgvector 기반 AI-Native 데이터 마트와 Text2SQL BI Agent
  를 설계·구현하여, 50문 다국어 평가셋에서 Execution Accuracy 78% 달성
  (프롬프트 v1 대비 +36%p).

• fct_campaign_performance(2천만 행) 대시보드 쿼리를 EXPLAIN ANALYZE 기반으로
  BRIN·복합 B-tree·사전 집계 조합을 적용해 18.3s → 1.2s (15배) 개선.

• LangChain + LangGraph + sqlglot 파서 기반 Text2SQL 파이프라인에 다층 검증
  (readonly DB role, LIMIT 자동, EXPLAIN 드라이런, 프롬프트 rule) 을 설계해
  위험 쿼리 Refuse Rate 100%.

• dbt star schema + SCD Type 2 + AI-Native 마트로 모델링하고 generic/custom
  테스트 84% 커버리지, source freshness/exposure 선언으로 Data Contract 강제.

• FastAPI + Semaphore(30) + Singleflight 로 Agent 서빙 계층을 설계, locust
  30 동접 실험에서 p95 3.1s · 성공률 99.2% (같은 질문 해시 30개 → LLM 호출 1회).
```

## 5.3 좋은 Bullet 5개 예시 (영어, LINE Pay 영문 이력서용)

```
• Designed and built an AI-Native data mart and Text2SQL BI Agent on Airflow +
  dbt + Postgres/pgvector, achieving 78% execution accuracy on a 50-question
  multilingual evaluation set (+36 pp over v1 prompt).

• Optimized a 20M-row dashboard query from 18.3s to 1.2s (15×) using BRIN,
  composite B-tree indexes, and dbt pre-aggregated models, guided by
  EXPLAIN ANALYZE regression runs.

• Built a defense-in-depth Text2SQL pipeline with LangChain/LangGraph,
  sqlglot AST validation, read-only DB role, auto LIMIT, and EXPLAIN dry-run —
  100% refuse rate on unsafe queries.

• Modeled Kimball star schema with SCD Type 2 and an AI-Native denormalized
  layer in dbt, enforcing 84% column-level test coverage, source freshness,
  and exposures as data contracts.

• Implemented FastAPI + asyncio.Semaphore(30) + singleflight for agent serving;
  locust at 30 concurrent users yielded p95 3.1s and 99.2% success, with
  30 simultaneous identical queries collapsing to a single LLM call.
```

**POINT**: 숫자는 **프로젝트 끝난 뒤 본인 실제 수치**로 반드시 교체. 부풀리는 순간 면접에서 찔림.

---

# 6. 면접 토크포인트 ↔ 프로젝트 매핑

면접에서 많이 나오는 질문을 **이 프로젝트의 어느 증거물로 답할지** 미리 매핑.

## 6.1 매핑 표

| 예상 질문 | 답변의 핵심 문장 | 증거물 위치 |
|---|---|---|
| "가장 어려웠던 문제?" | 다국어 정확도 42% → 71% | `docs/failure_cases.md` #1 |
| "쿼리 최적화 경험?" | 18s → 1.2s, BRIN + 복합 B-tree | `docs/query_tuning.md` |
| "idempotency 어떻게?" | DELETE+INSERT, merge, 백필 5회 검증 | `dags/dbt_run.py`, `docs/reliability_playbook.md` |
| "요청 처리 플로우?" | 7단계 (Semaphore → retrieve → generate → validate → execute → format → log) | `docs/request_flow.md` |
| "트래픽 10배?" | 병목 식별 → 캐시 → fallback → async → back-pressure | `docs/traffic_experiments.md` |
| "동시성 처리?" | 4층위 (pipeline/data/serving/agent) | `docs/concurrency_notes.md` |
| "dbt vs Airflow?" | 오케스트레이션 vs 변환, AdInsight Agent에서 둘의 역할 | README 섹션 10 |
| "AI-Native 뭐가 다름?" | 비정규화 + metadata + Agent 친화 (42%→78%) | `docs/adr/003-ai-native-layer.md` |
| "halucination 방지?" | 5층위 (readonly/validator/prompt/refuse/eval) | `docs/agent_eval.md` |
| "팀 협업 경험?" | Aimers glossary 표준화 → AdInsight Agent glossary seed | README 회고 섹션 |
| "Superset 기여?" | i18n PR + 문서 개선 PR | README JD 매칭 표 |

## 6.2 토크포인트 카드 만들기

각 질문마다 **A5 크기 카드 한 장** (물리든 디지털이든):

```
┌─────────────────────────────────────┐
│ Q: 가장 어려웠던 문제?                │
├─────────────────────────────────────┤
│ 핵심 문장 (30초):                    │
│ "다국어 Text2SQL 정확도 42% 급락을   │
│  임베딩 모델 교체 + synonyms +       │
│  few-shot 보강으로 71% 회복"         │
│                                      │
│ STAR:                                │
│ S: 태국어 20문 추가 → 78% → 42%      │
│ T: 다국어 커버리지 복구               │
│ A: 2층위 디버깅 → 3가지 조치          │
│ R: 71% (+29pp), 실패사례 3건 정리    │
│                                      │
│ 증거: docs/failure_cases.md #1       │
│ 수치: bge-m3 recall 66%→89%          │
└─────────────────────────────────────┘
```

이런 카드 10~12장을 만들면 면접 주요 질문의 절반 이상을 커버.

---

# 7. 측정 메트릭 카탈로그 (⭐ 프로젝트 중 모을 것)

**이 섹션이 이 문서에서 가장 중요합니다.** 아래 메트릭은 **프로젝트 진행 중에** 모아야 합니다. 끝난 뒤 돌아보면 재현이 안 돼요. 각 Phase 끝에 `metrics/run_results.jsonl` 또는 `metrics/phaseN.md` 에 기록하세요.

## 7.1 Phase 1 — 환경 셋업

| 메트릭 | 측정 방법 | 목표/참고값 | 용도 |
|---|---|---|---|
| compose up → 전부 healthy 시간 | `time make up` | < 90s | Quickstart 섹션 근거 |
| 이미지 총 크기 | `docker system df` | — | 재현성 참고 |
| Docker Desktop 메모리 피크 | Docker Desktop GUI | < 10GB | Quickstart 요구사항 |
| `.env.example` 변수 수 | 수동 | — | 설정 문서화 |

## 7.2 Phase 2 — 데이터 생성·수집

| 메트릭 | 측정 방법 | 기록 위치 |
|---|---|---|
| raw 총 행 수 (플랫폼별) | `SELECT count(*) FROM raw.*` | `metrics/phase2.md` |
| 국가 분포 (TW/TH/KR/JP) | SQL 집계 | README 데이터 섹션 |
| `ingest_synthetic` 실행 시간 | Airflow UI | README DAG 표 |
| idempotency 검증 | 5회 재실행 후 total row count | 회고 섹션 |
| 합성 비율 vs 공개 데이터 | 수동 집계 | README 한계 섹션 |

## 7.3 Phase 3 — dbt 모델링

| 메트릭 | 측정 방법 | 기록 |
|---|---|---|
| 모델 수 (레이어별) | `dbt ls` | README 섹션 9 |
| `dbt run` 전체 시간 | run_results.json | DAG 표 |
| `dbt test` 전체 시간 / 통과 수 | run_results.json | CI 배지 |
| 테스트 커버리지 (컬럼 대비) | custom 집계 스크립트 | README 핵심결과 |
| incremental vs full-refresh 시간 차 | 비교 실험 | 쿼리 튜닝 섹션 |
| SCD2 snapshot row 수 변화 추이 | 주간 집계 | ADR |

## 7.4 Phase 4 — AI-Native Mart

| 메트릭 | 측정 방법 | 기록 |
|---|---|---|
| ai_native 테이블 수 | `dbt ls --select ai_native` | README |
| 컬럼당 description 커버리지 | YAML 파싱 | README |
| synonyms 언어 수 (ko/en/zh/th) | YAML 파싱 | README |
| pgvector chunk 수 | SQL count | README |
| 임베딩 빌드 시간 | `time make agent-index` | Quickstart |
| HNSW 인덱스 빌드 시간 | `\timing` | 쿼리 튜닝 |

## 7.5 Phase 5 — Superset + 쿼리 최적화

| 메트릭 | 측정 방법 | 기록 |
|---|---|---|
| 대시보드 수 / 차트 수 | 수동 | README |
| Virtual dataset 수 | YAML export | README |
| 대시보드 초기 로딩 시간 (cold) | 브라우저 DevTools | **Before/After** |
| 동일 쿼리 EXPLAIN Before/After | `EXPLAIN ANALYZE` | **Before/After** |
| 인덱스 추가 후 쿼리 시간 | `\timing` | **핵심 결과** |
| 캐시 hit rate | Superset config → Redis keys | 트래픽 실험 |

### Query tuning 측정 템플릿

```markdown
## Case: [쿼리명]

**쿼리**
\```sql
[쿼리 원문]
\```

**Before**
- 실행 시간: XX.Xs
- 계획: Seq Scan / Hash Join / ...
- 주요 비용: Rows Removed by Filter = XXX
- EXPLAIN ANALYZE: [전문 or 핵심 3줄]

**Hypothesis**
- [왜 느린지 추측]

**Actions**
1. [조치 1]
2. [조치 2]

**After**
- 실행 시간: X.Xs
- 계획: Index Scan / ...
- [개선 %]

**Learning**
- [배운 점]
```

## 7.6 Phase 6 — Text2SQL Agent (⭐ 가장 풍부한 메트릭)

| 메트릭 | 측정 방법 | 기록 |
|---|---|---|
| 평가셋 크기 / 언어 분포 / 난이도 분포 | 수동 | README 평가 표 |
| **Execution Accuracy** (전체) | eval runner | **핵심 결과** |
| Execution Accuracy (언어별) | eval runner | **핵심 결과** |
| Execution Accuracy (난이도별) | eval runner | README |
| Refuse Rate (negative set) | eval runner | README |
| p50 / p95 / p99 latency | eval runner | README |
| Tokens per query (prompt/completion 분리) | API 응답 | 비용 표 |
| Cost per query ($) | 토큰 × 단가 | 비용 표 |
| 버전 비교 (v1/v2/v3) | 동일 eval 반복 | **핵심 결과** |
| 모델 비교 (Gemini/Claude) | 동일 eval | 추가 표 |
| 임베딩 모델 비교 (recall@k) | 별도 실험 | 실패 #1 |
| 프롬프트 변경 효과 (아블레이션) | v2a/v2b/v2c | ADR |

### Agent eval 결과 템플릿 (jsonl 1 row)

```json
{
  "run_id": "2026-04-15T02:30:00Z",
  "prompt_version": "v3",
  "llm_model": "gemini-2.5-flash",
  "embedding_model": "bge-m3",
  "dataset_size": 50,
  "exec_accuracy": 0.78,
  "exec_acc_by_lang": {"ko": 0.85, "en": 0.80, "zh-tw": 0.75, "th": 0.71},
  "exec_acc_by_difficulty": {"easy": 0.94, "medium": 0.77, "hard": 0.50},
  "refuse_rate": 1.0,
  "latency_p50_ms": 2400,
  "latency_p95_ms": 6100,
  "latency_p99_ms": 9200,
  "avg_prompt_tokens": 2840,
  "avg_completion_tokens": 180,
  "avg_cost_usd": 0.0022,
  "total_duration_s": 127
}
```

**주의**: 이 jsonl 이 프로젝트의 **정량 서사 전체**입니다. 시각화까지 해서 README 에 차트로 박으면 임팩트 3배.

## 7.7 Phase 7 — LLM 리포트

| 메트릭 | 측정 방법 |
|---|---|
| 리포트 생성 시간 | DAG task duration |
| 프롬프트 토큰 수 | Gemini API |
| 숫자 검증 (hand count) | 샘플 10건 수동 |
| Pydantic schema 실패율 | DAG 로그 |

## 7.8 Phase 8 — 품질·CI

| 메트릭 | 측정 방법 |
|---|---|
| pytest 통과 수 / 커버리지 | pytest-cov |
| dbt test 수 (generic/custom 분리) | `dbt test` 로그 |
| GitHub Actions 전체 실행 시간 | Actions UI |
| PR 평균 merge 시간 | git log |

## 7.9 Phase 9 — 트래픽·문서

| 메트릭 | 측정 방법 | 기록 |
|---|---|---|
| locust 30 동접 p50/p95/p99 | locust UI | README |
| 동접 변화 커브 (10/20/30/50) | 별도 실험 | 트래픽 실험 |
| Singleflight dedup 비율 | 로그 집계 | README |
| Gemini fallback 발동 횟수 | 로그 집계 | README |
| Back-pressure 503 발동 지점 | 로드 증가 실험 | 트래픽 실험 |
| ADR 문서 수 | 수동 | README |

## 7.10 메트릭 기록 원칙

1. **append-only**: 기록을 덮어쓰지 말고 누적.
2. **실험 ID**: 날짜/커밋해시 포함.
3. **재현 가능**: 각 실험에 커맨드 한 줄.
4. **정직**: 안 된 것은 안 된 대로. 실패도 데이터.
5. **자동화**: 가능한 건 DAG/make target 으로 자동 수집.

---

# 8. 스크린샷 · 증거물 체크리스트

포트폴리오의 시각 자산. 프로젝트 끝나기 전에 이 리스트를 **체크해서 캡처**해두세요. 끝난 뒤 재캡처는 귀찮고, 데모 데이터가 바뀌면 재현 안 됨.

## 8.1 필수 (README 용)

- [ ] **아키텍처 다이어그램** (SVG 또는 PNG 고해상도)
- [ ] **ERD** (ai_native 레이어 중심 축소본)
- [ ] **Bus Matrix** (표 또는 이미지)
- [ ] **Airflow DAG 그래프** (최소 3개: ingest, dbt_run, weekly_llm_report)
- [ ] **dbt docs lineage 그래프** (전체 또는 marts→ai_native 구간)
- [ ] **Superset 대시보드 최소 2개** (광고주 ROI, 크리에이터 성과)
- [ ] **Text2SQL 데모 GIF** (질문 입력 → SQL → 표 → 요약)
- [ ] **EXPLAIN Before/After 콘솔 캡처**
- [ ] **locust 부하 테스트 스크린샷** (RPS, p95)
- [ ] **CI 배지 (GitHub Actions)**

## 8.2 권장 (블로그·심층 문서용)

- [ ] Airflow task 실행 이력 (30일)
- [ ] pg_stat_statements Top 10 쿼리
- [ ] pgvector HNSW 파라미터 비교 표
- [ ] Agent failure case 스크린샷 3건
- [ ] Redis 캐시 히트 로그
- [ ] 다국어 질문 동작 예시 (4개 언어 각 1건)
- [ ] 한 주간 run_results.jsonl 차트 (plotly/matplotlib)

## 8.3 스크린샷 품질 가이드

- **해상도**: retina 기준 원본 (README 에서는 width 로 조절)
- **크롭**: 민감 정보(비밀번호, 실서비스 URL) 제거
- **일관성**: 같은 다크/라이트 테마로 통일
- **캡션**: 각 이미지 아래 한 줄 설명 (무엇을 보여주는지)
- **파일명**: `docs/images/NN_topic.png` 번호 붙여 순서 유지

---

# 9. JD 역매핑 표 (완전판)

LINE Pay AI Insight Engineer JD 를 한 줄씩 뜯어서, 이 프로젝트의 어디가 대응하는지 빠짐없이.

## 9.1 필수 요건

| JD 원문 (요약) | AdInsight Agent 의 대응 | 산출물 |
|---|---|---|
| AI-Native 데이터 마트 설계/개발 | dbt `ai_native/` 레이어 (비정규화 + semantic metadata) | `dbt/models/ai_native/`, ADR 003 |
| Airflow 기반 ETL 파이프라인 | 3개 DAG (ingest, dbt_run, llm_report) | `dags/`, DAG 스크린샷 |
| BI 대시보드 개발 (Tableau/Superset) | Superset 4 dashboards (advertiser ROI, creator performance, ...) | `dashboards/superset_exports/` |
| LLM 기반 자동 리포트 | `weekly_llm_report` DAG (Gemini + Pydantic 검증) | `docs/reports/`, 샘플 주간 리포트 |
| Text2SQL BI Agent 개발 | LangChain + LangGraph + sqlglot 파이프라인 | `agent/chains/`, eval report |
| 쿼리 성능 최적화 | EXPLAIN 기반 인덱스·파티셔닝·사전집계 | `docs/query_tuning.md` (18s→1.2s) |
| Pandas/API 데이터 연동 | `data_generation/` (pandas + SDV) + FastAPI | `api/`, `data_generation/` |

## 9.2 우대 사항

| JD 원문 (요약) | AdInsight Agent 의 대응 | 산출물 |
|---|---|---|
| LangChain / OpenAI API 경험 | LangChain 0.2 + dual provider (Gemini + Claude) | `agent/chains/pipeline.py` |
| Vector DB 사용 경험 | pgvector + HNSW | `infra/postgres/init/03_pgvector.sql` |
| Superset 오픈소스 기여 | i18n PR + docs PR (예정) | [PR 링크] |
| 글로벌 협업 (영어) | 영문 README + 4개 언어 질문 지원 | `README.en.md`, eval dataset |

## 9.3 면접 후기 반영 (LINE Pay 면접 단골 주제)

| 단골 질문 | 이 프로젝트에서 답할 위치 |
|---|---|
| 가장 어려웠던 기술 문제 | failure case #1 (다국어 정확도) |
| 요청 처리 플로우 | request flow 다이어그램 |
| 트래픽 처리 경험 | traffic experiments (locust) |
| 데이터 동시성 | concurrency notes (4 레이어) |
| 업무 프로세스 | reliability playbook (9개 실패 시나리오) |

---

# 10. 최종 완성도 체크리스트

프로젝트 끝내기 전에 훑어보세요. 하나라도 빠지면 포트폴리오 완성도가 급락합니다.

## 10.1 저장소

- [ ] README 가 위 16개 섹션 모두 채워짐
- [ ] JD 매칭 표의 모든 링크가 실제로 동작
- [ ] 모든 Before/After 표에 **실측 수치** (추정 금지)
- [ ] 라이선스·데이터 출처 명시
- [ ] `.env.example` 제공, `.env` gitignore
- [ ] `make up` 으로 실제 낯선 맥에서 재현됨 (가능하면 다른 기기에서 테스트)
- [ ] GitHub Actions CI 통과 배지
- [ ] 커밋 메시지가 conventional (feat/fix/docs/...)
- [ ] Issues/Projects 에 "다음 할 일" 정리 (미완성은 **숨기지 말고 공개**)

## 10.2 문서

- [ ] ADR 최소 3개 (blueprint, star schema, ai-native layer)
- [ ] request_flow.md 다이어그램
- [ ] concurrency_notes.md 4층위
- [ ] traffic_experiments.md 실험 결과
- [ ] query_tuning.md Before/After
- [ ] agent_eval.md 버전별 결과 표
- [ ] failure_cases.md 3건 이상
- [ ] reliability_playbook.md 9개 시나리오
- [ ] interview_talking_points.md (비공개 권장)

## 10.3 시각 자산

- [ ] 아키텍처 다이어그램 (SVG)
- [ ] ERD
- [ ] DAG 스크린샷 × 3
- [ ] 대시보드 스크린샷 × 2
- [ ] 데모 GIF
- [ ] Before/After EXPLAIN 캡처
- [ ] locust 결과

## 10.4 포트폴리오 배포물

- [ ] GitHub 저장소 public + pin
- [ ] README.en.md (영문 버전) 최소 3줄 요약 + 매핑 표
- [ ] 이력서 bullet 5개 교체 완료
- [ ] 1-pager PDF 작성
- [ ] (선택) 노션/블로그 회고 글 공개
- [ ] LinkedIn 프로젝트 추가 (링크 + 3줄 설명)

## 10.5 면접 준비물

- [ ] 토크포인트 카드 10~12장
- [ ] 1분 자기소개 암기
- [ ] 3분 프로젝트 소개 암기
- [ ] "질문 있으신가요?" 답 3개 준비
- [ ] 모든 숫자의 출처를 말할 수 있음 (이력서의 모든 숫자 포함)

---

# 부록 A. "매일 10분 투자" 포트폴리오 적립 루틴

프로젝트가 길어지면 포트폴리오 정리를 뒤로 미루게 됩니다. 다음 루틴을 매일 반복하세요.

```
매일 저녁 10분:
1. 오늘 한 작업을 한 줄로 `docs/daily_log.md` 에 append
2. 수치가 나왔으면 metrics/ 에 기록
3. 스크린샷 찍을 게 있으면 `docs/images/` 에 저장
4. README 의 "Phase 진행도" 체크박스 업데이트

매주 금요일 30분:
1. 이번 주 수치를 README 핵심 결과 표에 반영
2. 실패 사례가 있으면 failure_cases.md 에 정리
3. GitHub Issues 에서 "다음 주" 라벨 정리
```

매일 10분 × 10주 = 16시간. 이 시간이 프로젝트 끝에 몰아서 정리하는 40시간을 아껴줍니다.

---

# 부록 B. 피해야 할 안티패턴 7가지

1. **추상어 범람**: "확장 가능한 · 견고한 · 효율적인" 같은 수식어만 있고 수치가 없으면 의심받음.
2. **JD 단어 그대로 복붙**: "AI-Native 데이터 마트 개발" 이라고만 쓰면 JD 외우기. **무엇을** 어떻게 **구현했는지**가 핵심.
3. **아키텍처 그림만 있고 증거 없음**: 네모 박스와 화살표는 누구나 그림. 각 박스에 대응되는 코드·DAG·테이블이 있어야 함.
4. **README 에 코드 전문 붙이기**: 코드는 저장소에 있음. README 는 **하이라이트**.
5. **부풀린 숫자**: 면접에서 재현 안 되면 끝. 정직한 낮은 숫자 > 거짓 높은 숫자.
6. **한계 섹션 생략**: "완벽하다"는 주장은 비전문가의 신호. 한계를 말할 수 있는 게 프로의 증거.
7. **영문 README 엉터리 기계번역**: LINE Pay 같은 글로벌 포지션은 영문 자료를 봄. 서툴러도 **본인 손으로 쓴** 영문이 번역기 돌린 것보다 낫다.

---

# 마치며

포트폴리오의 본질은 **"이 사람이 우리 팀에서 내일 뭘 할 수 있을지"** 를 면접관이 상상하게 만드는 것입니다. AdInsight Agent 는 이미 JD 의 거의 모든 축을 다룹니다. 남은 건 그 작업을 **측정·기록·서사화**하는 일.

이 템플릿은 **"채우면 되는 빈 자리"** 로 설계했어요. 프로젝트 시작 첫날 저장소에 `docs/portfolio_draft.md` 로 넣어두고, 매일 한 칸씩 채워나가세요. 10주 뒤에는 별도 정리 시간 없이도 지원 가능한 포트폴리오가 생겨 있을 겁니다.

행운을 빕니다 🚀
