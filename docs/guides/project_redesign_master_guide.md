# AdInsight Agent — 재설계 마스터 가이드 (A+C 전략)

> **작성일**: 2026-06-16
> **목적**: 이 프로젝트 전체를 처음부터 끝까지 어떻게 진행할지 한 눈에 볼 수 있는 로드맵.
> Codex 세션을 시작할 때마다 이 문서를 먼저 읽고 현재 위치를 확인하세요.

---

## 왜 재설계했는가

Phase 4까지 진행 후 JD와의 갭을 점검한 결과:

| 문제 | 원인 | 영향 |
|---|---|---|
| 데이터 49행 | 대규모 ETL 증명 불가 | 쿼리 최적화 수치 없음 |
| ML 모델 없음 | Fintech DS JD 핵심 미충족 | DS 포지션 지원 불가 |
| Agent 없음 (eval만) | Exec Acc 수치 없음 | Text2SQL 능력 증명 불가 |
| FastAPI 없음 | API 연동 경험 없음 | DE JD 자격요건 미충족 |
| 핀테크 연결 없음 | 도메인 거리 있음 | 면접 스토리 약함 |

**결론**: 기존 구조는 살리되, 위 5가지를 채우는 방향으로 재설계.

---

## 새 프로젝트 피치

> "인플루언서 광고 집행부터 결제 전환까지 추적하는 멀티도메인 AI-Native 분석 플랫폼.
> 운영 등급 Apify 자동화 파이프라인, dbt 5레이어 데이터 마트,
> ROAS 예측 LightGBM 모델, Text2SQL BI Agent를 포함."

---

## 데이터 구성 전략

```
[실수집 — Apify 자동화]          [합성 — 핀테크 레이어]
Instagram 게시물                  결제 전환 이벤트
매일 100~300건 자동 수집    +     가설 기반 분포로 50,000건 생성
60일 누적 ~10,000건               creator_username 키로 JOIN
        │                                   │
        └──────────────┬────────────────────┘
                       ▼
              dbt 5레이어 통합 모델링
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ROAS 예측      Text2SQL      Superset
    ML 모델         Agent       대시보드
```

**왜 합성 데이터를 쓰는가**:
실제 결제 데이터는 없지만, 이건 문제가 아닙니다.
도메인 가설(engagement율 ↔ 전환율 관계 등)을 수식으로 표현한 시뮬레이션이며,
Fintech DS가 신규 분석 시스템을 만들 때 실제로 쓰는 방법입니다.

---

## 전체 Phase 로드맵

| Phase | 이름 | 기간 | 상태 | 핵심 결과물 |
|---|---|---|---|---|
| 0~3 | 기존 작업 (유지) | — | ✅ 완료 | dbt 5레이어, ai_native, eval YAML |
| **P** | **포지셔닝 재정립** | 2일 | ✅ | blueprint/CLAUDE.md 업데이트, ADR 003 |
| **2B** | **Apify 자동화 파이프라인** | 1주 | ⬜ | watermark + freshness + backfill DAG |
| **2C** | **합성 결제 데이터 생성기** | 1주 | ⬜ | 116만 행, fact_payment 5만 행 |
| **3B** | **dbt 모델 확장** | 1주 | ⬜ | 모델 18개, 테스트 120개 |
| **4B** | **ROAS 예측 ML 모델** | 1주 | ⬜ | LightGBM, Feature Importance, RMSE |
| **5B** | **Text2SQL Agent 실구현** | 1주 | ⬜ | Exec Acc 수치 (목표 72%) |
| **6B** | **FastAPI 엔드포인트** | 4일 | ⬜ | /query, /predict |
| **7B** | **Superset 대시보드 + 쿼리 최적화** | 1주 | ⬜ | Before/After EXPLAIN 수치 |
| **8B** | **CI/CD** | 4일 | ⬜ | GitHub Actions 배지 |
| **9B** | **문서화 + 데모 준비** | 1주 | ⬜ | 면접 토크포인트 + 데모 영상 |

**총 예상 기간**: 평일 1~2시간 기준 약 7~8주

---

## Phase P — 포지셔닝 재정립

**목적**: 방향을 바꾸기 전에 변경 사항을 문서화한다.

### 할 일

1. `CLAUDE.md` §1 목표 한 줄 교체
2. `README.md` TL;DR 섹션 교체
3. `docs/adinsight_project_blueprint.md` 피치 문장 교체
4. `docs/adr/003-redesign-ac-strategy.md` 작성 (이미 완료 ✅)

### Codex 요청 템플릿

```
CLAUDE.md를 읽어줘.
docs/adr/003-redesign-ac-strategy.md 도 읽어줘.

CLAUDE.md §1 프로젝트 목표를 아래로 바꿔줘:
"LINE Pay AI 인사이트 엔지니어 포트폴리오.
 인플루언서 광고 집행 → 결제 전환 분석 플랫폼 +
 ROAS 예측 ML 모델 + Text2SQL BI Agent."

README.md TL;DR도 같은 방향으로 업데이트해줘.
변경 전/후를 보여주고 내가 직접 수정할게.
```

### 완성 기준
- [ ] `CLAUDE.md` 목표 문장 변경됨
- [ ] `README.md` TL;DR 변경됨

---

## Phase 2B — Apify 운영 등급 자동화 파이프라인

**목적**: 단순 cron이 아닌 watermark + freshness + backfill을 갖춘 운영 등급 파이프라인.

**상세 가이드**: `docs/guides/phase2b_apify_daily_pipeline_guide.md`

### 만드는 것
```
dags/common/ig_collect_utils.py   watermark / freshness 공통 함수
dags/dag_ig_collect_daily.py      매일 오전 6시 자동 수집 (3 seed × 200건)
dags/dag_ig_backfill.py           특정 날짜 재수집
```

### 핵심 요소
- **watermark**: Airflow Variable `ig_collect_last_watermark`에 마지막 수집 날짜 저장
- **freshness check**: 수집 0건 → DAG FAIL / 주간평균 30% 미만 → WARNING
- **backfill**: `target_date` 파라미터로 과거 날짜 재수집, idempotent 보장

### 포트폴리오 수치 목표
```
"매일 자동 수집, 60일 누적 6,000~18,000건"
"watermark 기반 증분 적재, idempotent 검증 완료"
"freshness check + 이상치 알림 포함 운영 등급 파이프라인"
```

### 완성 기준
- [ ] `dag_ig_collect_daily` Airflow UI에서 정상 동작
- [ ] Airflow Variable `ig_collect_last_watermark` 생성됨
- [ ] freshness check 0건 시 FAIL 동작 확인
- [ ] backfill 2회 실행 후 row count 동일 (idempotency)
- [ ] `metrics/run_results.jsonl`에 daily 기록 쌓임

---

## Phase 2C — 합성 결제 데이터 생성기

**목적**: 핀테크 ML 모델의 학습 데이터가 될 결제 전환 이벤트를 생성한다.

### 만드는 것
```
data_generation/generators/creators.py         크리에이터 프로필 10,000건
data_generation/generators/campaigns.py        캠페인 5,000건
data_generation/generators/post_metrics.py     일별 성과 100만 건
data_generation/generators/payment_events.py   결제 전환 이벤트 5만 건 ← 핵심
data_generation/run_generate.py                전체 실행 진입점
```

### 핵심 설계 원칙

`payment_events.py`는 단순 난수가 아니라 **도메인 가설을 수식으로 표현**합니다:

```python
# 가설: engagement율 높은 크리에이터 → ROAS 높음
# 가설: 협찬 비율 너무 높으면 → ROAS 낮음 (광고 피로)
# 가설: 뷰티 카테고리 전환율 2배

roas = base_roas
     + engagement_rate * 3.0          # 참여율 보너스
     - sponsored_rate ** 2 * 1.5      # 광고 피로 패널티
     * category_multiplier            # 뷰티 1.8 / 게임 0.9
     + random.gauss(0, 0.3)           # 현실 노이즈
```

이 수식이 "왜 이 분포인가"를 설명할 수 있게 해줍니다 → 면접 강점.

### 생성 목표

| 테이블 | 행 수 | 소스 |
|---|---|---|
| `raw.syn_creators` | 10,000 | Faker + 로그노멀 |
| `raw.syn_campaigns` | 5,000 | Faker + 파레토 |
| `raw.syn_post_metrics_daily` | 1,000,000 | EWMA 시계열 |
| `raw.syn_payment_events` | 50,000 | 가설 기반 분포 |

### Codex 요청 템플릿

```
CLAUDE.md를 읽어줘.
docs/guides/project_redesign_master_guide.md 의 Phase 2C 섹션을 읽어줘.

data_generation/generators/payment_events.py 를 만들 거야.
이 파일이 "단순 더미"가 아니라 "도메인 가설 기반 시뮬레이션"이어야 하는 이유를
먼저 설명해줘.

그 다음 가설 3개 (engagement-ROAS 관계 / 광고 피로 / 카테고리 배수)를
파이썬 수식으로 어떻게 표현하는지 보여줘.
내가 직접 타이핑할 수 있게 핵심 함수부터 안내해줘.
```

### 포트폴리오 수치 목표
```
"합성 데이터 116만 행, Parquet 파티셔닝, seed=42 재현 가능"
"결제 전환 이벤트 5만 건, 도메인 가설 기반 ROAS 분포"
```

### 완성 기준
- [ ] `python data_generation/run_generate.py` 실행 성공
- [ ] `raw.syn_payment_events` 적재 완료 (~50,000행)
- [ ] `metrics/run_results.jsonl`에 생성 결과 기록
- [ ] `data_generation/README.md`에 분포 선택 이유 작성

---

## Phase 3B — dbt 모델 확장

**목적**: 합성 결제 데이터를 dbt 레이어에 통합하고 ML Feature Store 역할을 하는 ai_native 모델을 추가한다.

### 기존 모델 (유지)
```
staging.stg_ig_posts
intermediate.int_ig_post_source_quality
intermediate.int_ig_sponsored_candidates
intermediate.int_ig_owner_activity
marts.mart_creator_sponsored_summary
ai_native.ai_creator_sponsored_summary
```

### 추가할 모델 (신규)
```
staging.stg_syn_creators
staging.stg_syn_campaigns
staging.stg_syn_payment_events           ← 핵심 핀테크 레이어
intermediate.int_campaign_performance    ← 캠페인별 성과 집계
intermediate.int_payment_conversion      ← 전환율 계산
marts.mart_campaign_roi                  ← 캠페인 ROI (면접 핵심)
marts.mart_creator_payment_profile       ← 크리에이터별 결제 기여
ai_native.ai_campaign_360               ← LLM 쿼리용 360도 뷰
ai_native.ai_campaign_roi_features      ← ML Feature Store 역할
```

### `ai_campaign_roi_features` 핵심 컬럼
```sql
-- 이 모델이 ML 모델의 Feature Store 역할을 한다
creator_username,
follower_count_log,          -- log 변환 (스케일 정규화)
avg_engagement_rate_7d,      -- 7일 평균 참여율
sponsored_candidate_rate,    -- 협찬 비율
region_tw, region_th,        -- one-hot 인코딩
category_beauty,             -- one-hot 인코딩
past_roas_avg,               -- 과거 캠페인 평균 ROAS
next_campaign_roas           -- 예측 대상 (label)
```

### 포트폴리오 수치 목표
```
"dbt 모델 18개 (staging 4 / intermediate 5 / marts 5 / ai_native 4)"
"dbt 테스트 120개, 커버리지 85%"
"dbt docs lineage 그래프 (스크린샷)"
```

### 완성 기준
- [ ] `dbt run` 성공 (18개 모델)
- [ ] `dbt test` 성공 (120개 이상)
- [ ] `dbt docs generate` 후 lineage 그래프 스크린샷 저장
- [ ] `ai_campaign_roi_features` 에 Feature 12개 이상

---

## Phase 4B — ROAS 예측 ML 모델

**목적**: Fintech Data Scientist JD가 요구하는 "ML 모델 개발 + Feature 개발"을 증명한다.

### 비즈니스 질문
> "어떤 크리에이터에게 다음 캠페인을 맡겨야 ROAS가 높은가?"

### 데이터 흐름
```
ai_native.ai_campaign_roi_features (dbt에서 생성)
    ↓ psycopg로 읽기
Feature 전처리 (스케일링, one-hot)
    ↓
LightGBM 학습 (Walk-forward Cross-Validation)
    ↓
roas_predictor.pkl 저장
    ↓
평가: RMSE, MAE, Feature Importance
    ↓
FastAPI /predict 엔드포인트 (Phase 6B에서 연결)
```

### 만드는 것
```
ml/
├── train_roas_model.py     Feature 로드 + LightGBM 학습
├── evaluate_model.py       RMSE, MAE, Feature Importance 시각화
├── roas_predictor.pkl      학습된 모델 (gitignore)
└── README.md               모델 설계 + 성능 요약
```

### 왜 LightGBM인가 (면접 답변)
- 해석 가능성 ↑ (Feature Importance 설명 쉬움)
- 테이블 데이터에 강력, 빠른 학습
- 대안: XGBoost (비슷한 성능, 더 느림), Random Forest (해석 쉽지만 성능 낮음)

### 왜 Walk-forward CV인가 (면접 답변)
- 일반 K-Fold는 미래 데이터를 과거 예측에 사용 → 데이터 누수 발생
- 시계열 데이터는 시간 순서를 지켜야 함 → Walk-forward CV 필수

### Codex 요청 템플릿

```
CLAUDE.md를 읽어줘.

ml/train_roas_model.py 를 만들 거야.
이 파일이 하는 일을 순서대로 설명해줘:
1. ai_native.ai_campaign_roi_features 에서 psycopg로 데이터 읽기
2. Feature / label 분리
3. Walk-forward Cross-Validation 설명 (왜 일반 K-Fold가 안 되는가)
4. LightGBM 학습
5. RMSE / MAE 계산
6. Feature Importance 출력

한 단계씩 가르쳐줘.
```

### 포트폴리오 수치 목표
```
"ROAS 예측 모델, Feature 12개, Walk-forward CV 5 fold"
"RMSE: X.XX (실측값으로 채울 것)"
"Feature Importance 상위 3개: engagement_rate, past_roas_avg, category"
```

### 완성 기준
- [ ] `python ml/train_roas_model.py` 실행 성공
- [ ] Feature Importance 차트 → `docs/images/04b_feature_importance.png` 저장
- [ ] `metrics/run_results.jsonl`에 RMSE/MAE 기록
- [ ] `ml/README.md`에 모델 설계 결정 + Known Limitations 작성

---

## Phase 5B — Text2SQL Agent 실구현

**목적**: eval YAML만 있는 상태에서 실제로 동작하는 Agent를 만들고 Execution Accuracy를 측정한다.

### 구현 순서 (이 순서가 중요합니다)

```
Step 1: Agent MVP (2일)
  agent/chains/sql_agent_v1.py
  → LangChain SQLDatabaseChain 기반, 30줄
  → 일단 돌아가는 것이 목표

Step 2: Evaluator (1일)
  agent/eval/run_eval.py
  → text2sql_questions.yml 읽어서 Agent에 질문
  → SQL 실행 → row count 비교
  → Exec Acc % 출력

Step 3: Schema Retriever 추가 (2일)
  agent/chains/schema_retriever.py
  → pgvector에 dbt YAML 메타데이터 임베딩 저장
  → 질문 → top-k 관련 테이블/컬럼 검색

Step 4: 프롬프트 버전 3개 비교 (2일)
  v1: zero-shot
  v2: + schema 주입
  v3: + few-shot + CoT
```

### 목표 수치 비교표

| 버전 | 프롬프트 | 목표 Exec Acc |
|---|---|---|
| v1 | zero-shot | ~35% |
| v2 | + schema retrieval | ~55% |
| v3 | + few-shot + CoT | ~72% |

**이 숫자의 변화가 "왜 AI-Native 레이어와 schema retrieval이 필요한가"를 증명합니다.**

### 만드는 것
```
agent/
├── chains/
│   ├── sql_agent_v1.py      MVP (SQLDatabaseChain)
│   ├── sql_agent_v2.py      + schema retrieval
│   └── sql_agent_v3.py      + few-shot + CoT
├── eval/
│   ├── run_eval.py          자동 평가 실행기
│   └── results/             버전별 결과 JSON
├── prompts/
│   ├── v1_zero_shot.yaml
│   ├── v2_with_schema.yaml
│   └── v3_cot.yaml
└── embeddings/
    └── build_schema_index.py  pgvector 임베딩 빌드
```

### Codex 요청 템플릿

```
CLAUDE.md를 읽어줘.
agent/eval/text2sql_questions.yml 을 읽어줘.

agent/chains/sql_agent_v1.py 를 만들 거야.
LangChain SQLDatabaseChain 이 무엇인지 먼저 설명해줘.
그 다음 최소 동작 버전(30줄 이내)을 가르쳐줘.
```

### 포트폴리오 수치 목표
```
"Text2SQL Agent, 평가셋 30문제 (한/영)"
"v1 Exec Acc 35% → v3 72% (schema retrieval + CoT 효과)"
"Latency p95: 2.4s, 비용 $0.002/query"
```

### 완성 기준
- [ ] `python agent/eval/run_eval.py --version v1` 실행 → Exec Acc 수치 출력
- [ ] v1 / v2 / v3 결과 비교표 `agent/eval/results/` 에 저장
- [ ] `docs/images/06_text2sql_demo.gif` 데모 GIF 캡처
- [ ] `agent/eval/failure_cases.md` 실패 케이스 3건 이상 기록

---

## Phase 6B — FastAPI 엔드포인트

**목적**: DE JD 자격요건 첫 번째 항목 "데이터 서빙 API 연동 개발" 충족.

### 만드는 것
```
api/
├── main.py          FastAPI 앱 진입점
├── routers/
│   ├── query.py     POST /query  → Text2SQL Agent 호출
│   └── predict.py   POST /predict → ROAS 예측 모델 호출
└── schemas.py       Pydantic request/response 모델
```

### 엔드포인트 명세

```
POST /query
  Request:  {"question": "뷰티 카테고리에서 ROAS 2 이상 크리에이터 Top 5?"}
  Response: {"sql": "SELECT ...", "result": [...], "latency_ms": 1240}

POST /predict
  Request:  {"creator_username": "beauty_tw_001", "campaign_budget_krw": 500000}
  Response: {"predicted_roas": 2.34, "confidence": "medium"}
```

### Codex 요청 템플릿

```
CLAUDE.md를 읽어줘.

api/main.py 와 api/routers/query.py 를 만들 거야.
FastAPI 의 기본 구조와 router 패턴을 먼저 설명해줘.
그 다음 /query 엔드포인트 하나만 먼저 만들어줘.
```

### 포트폴리오 수치 목표
```
"FastAPI 2개 엔드포인트 (/query, /predict)"
"Swagger UI 스크린샷"
"curl 테스트 성공 로그"
```

### 완성 기준
- [ ] `uvicorn api.main:app` 실행 성공
- [ ] `POST /query` curl 테스트 성공
- [ ] `POST /predict` curl 테스트 성공
- [ ] Swagger UI 스크린샷 → `docs/images/06b_api_swagger.png`

---

## Phase 7B — Superset 대시보드 + 쿼리 최적화

**목적**: 100만+ 행 데이터로 실제 쿼리 최적화 수치를 만든다. (49행에선 불가능했던 것)

### 대시보드 3종

| 대시보드 | 주요 차트 | 타겟 JD |
|---|---|---|
| Campaign ROI | ROAS 분포, 지역별 히트맵, 전환 퍼널 | DE (Superset 운영) |
| Creator Performance | 크리에이터별 결제 기여 랭킹 | DS (ML 결과 시각화) |
| Payment Conversion | 게시물→결제 전환 시계열 | DE (시계열 분석) |

### 쿼리 최적화 실험 (필수)

```
초기 쿼리 → EXPLAIN ANALYZE 실행 → 시간 기록
개선 적용 → 재측정 → Before/After 표 작성
```

| 쿼리 | Before | After | 기법 |
|---|---|---|---|
| Campaign ROI 집계 | ~8,000ms | ~400ms | B-tree index + dbt 사전집계 |
| 크리에이터 전환 분석 | ~12,000ms | ~900ms | BRIN index + 파티셔닝 |
| 일별 트렌드 차트 | ~5,000ms | ~200ms | 머티리얼라이즈드 뷰 |

**주의**: 위 수치는 예상값입니다. 반드시 실측값으로 교체하세요 (CLAUDE.md 규칙 #12).

### 포트폴리오 수치 목표
```
"대시보드 3개, 차트 10개 이상"
"쿼리 최적화 3건, 평균 93% 개선"
"BRIN index / 머티리얼라이즈드 뷰 / dbt 사전집계 적용"
```

### 완성 기준
- [ ] Superset 대시보드 3개 스크린샷 저장
- [ ] `metrics/query_optimization_log.md` 실측값 채워짐
- [ ] EXPLAIN Before/After 콘솔 캡처 저장

---

## Phase 8B — CI/CD (다른 Phase와 병행 가능)

**목적**: 2026년 면접에서 "CI 없으면 감점"이므로 일찍 추가한다.

### 만드는 것
```
.github/workflows/
├── dbt-ci.yml    PR마다 dbt parse + compile + test
└── lint.yml      ruff + sqlfluff
```

### Codex 요청 템플릿

```
.github/workflows/dbt-ci.yml 을 만들 거야.
GitHub Actions 기본 구조를 설명해줘.
PR이 열릴 때마다 dbt parse, dbt compile, dbt test 를 실행하는
workflow 를 단계별로 가르쳐줘.
```

### 완성 기준
- [ ] GitHub에 push 후 Actions 탭에서 초록 체크 확인
- [ ] `README.md` 상단에 CI 배지 추가

---

## Phase 9B — 문서화 + 데모 준비

**목적**: 모든 작업을 면접 자산으로 변환한다.

### 필수 문서 4개

```
docs/request_flow.md          Text2SQL 7단계 처리 플로우 다이어그램
docs/ml_model_design.md       ROAS 예측 모델 설계 결정 + 한계
docs/interview_talking_points.md  STAR 포맷 답변 7개
docs/adr/004~006.md           LangChain 선택 / Embedding 모델 / LLM provider
```

### 면접 토크포인트 7개 주제

1. **가장 어려웠던 기술 문제** → Text2SQL 실패 케이스 + 해결 과정
2. **쿼리 최적화 경험** → Before/After EXPLAIN 수치
3. **idempotency 구현** → watermark + upsert + backfill 5회 검증
4. **요청 처리 플로우** → Text2SQL 7단계 (retrieve → generate → validate → execute)
5. **트래픽 10배 대응** → 커넥션 풀 + LLM 캐시 + fallback
6. **AI-Native 레이어 설계** → 일반 마트 vs ai_native 차이 (Exec Acc 35% → 72%)
7. **합성 데이터 전략** → "단순 더미가 아닌 도메인 가설 기반 시뮬레이션"

### 데모 영상 스크립트 (3~5분)

```
00:00  도메인 소개 — "인플루언서 광고 → 결제 전환 분석, LINE Pay 맥락 연결"
00:30  아키텍처 다이어그램
01:00  Airflow DAG 실행 — daily 파이프라인 + watermark
01:30  dbt docs lineage 그래프
02:00  Superset 대시보드 — Campaign ROI
02:30  Text2SQL Agent 데모 — 한국어 질문 1개, 영어 질문 1개
03:30  ROAS 예측 모델 — Feature Importance 차트
04:00  쿼리 최적화 Before/After
04:30  메트릭 요약 (Exec Acc, RMSE, 쿼리 개선율)
```

### 완성 기준
- [ ] `docs/interview_talking_points.md` 7개 토크포인트 완성
- [ ] ADR 003~006 모두 작성됨
- [ ] 데모 영상 스크립트 작성됨
- [ ] README.md 최종본 완성 (JD 매핑표 + 실측 메트릭 포함)

---

## 최종 포트폴리오 메트릭 목표

완성 시 README에 이 수치들이 들어가야 합니다:

```
📦 데이터 파이프라인
- 실수집: Instagram ~10,000건 (Apify 자동화, 60일 누적)
- 합성: 116만 행 (가설 기반 분포, seed=42)
- dbt: 모델 18개, 테스트 120개, 커버리지 85%
- idempotency: watermark + 5회 재실행 row count 동일

🤖 ML 모델 (Fintech DS)
- 목표: 캠페인 ROAS 예측
- 알고리즘: LightGBM, Feature 12개
- 성능: RMSE [실측], Walk-forward CV 5 fold
- Feature Store 패턴: dbt ai_native 레이어 활용

💬 Text2SQL BI Agent (Data Platform Engineer)
- 평가셋: 30문제 (한/영, easy/medium/hard)
- v1 Exec Acc: [실측] → v3 Exec Acc: [실측]
- Latency p95: [실측]s

⚡ 쿼리 최적화 (3건)
- Campaign ROI: [실측]ms → [실측]ms (-[실측]%)

🔧 인프라
- Docker Compose 8 서비스
- GitHub Actions CI (dbt + ruff)
- FastAPI 2 엔드포인트
```

---

## 현재 작업 위치 추적

이 표를 매 세션 시작 시 업데이트하세요:

| Phase | 상태 | 마지막 세션 | 다음 할 일 |
|---|---|---|---|
| P | ✅ 완료 | Session 13 | Phase 2B 착수 |
| 2B | 🟡 다음 | Session 13 | `phase2b_apify_daily_pipeline_guide.md` 따라 진행 |
| 2C | ⬜ 미시작 | — | `payment_events.py` 설계부터 |
| 3B | ⬜ 미시작 | — | `stg_syn_payment_events.sql` 부터 |
| 4B | ⬜ 미시작 | — | `ml/train_roas_model.py` |
| 5B | ⬜ 미시작 | — | `sql_agent_v1.py` MVP |
| 6B | ⬜ 미시작 | — | `api/routers/query.py` |
| 7B | ⬜ 미시작 | — | 대시보드 3종 + EXPLAIN |
| 8B | ⬜ 미시작 | — | `.github/workflows/dbt-ci.yml` |
| 9B | ⬜ 미시작 | — | 면접 토크포인트 7개 |

---

## Codex 세션 시작 공통 템플릿

모든 새 Codex 세션을 시작할 때 복사해서 쓰세요:

```
CLAUDE.md 와 AGENTS.md 를 먼저 읽어줘.
docs/session_log/ 의 최신 1~2개 파일을 읽고 "Next session — start here" 를 확인해줘.
docs/guides/project_redesign_master_guide.md 를 읽고 현재 작업 위치를 파악해줘.

오늘 진행할 Phase: [Phase 번호 입력]
해당 Phase 의 "Codex 요청 템플릿" 을 따라 시작해줘.
Teaching-First 원칙대로, 개념 설명 → 스니펫 → 내가 직접 타이핑 순서로 진행해줘.
```

---

## 참고 문서 인덱스

| 문서 | 내용 |
|---|---|
| `docs/adr/003-redesign-ac-strategy.md` | A+C 전략 채택 이유 |
| `docs/analysis/phase2b_apify_pipeline_design.md` | Apify 파이프라인 상세 설계 |
| `docs/guides/phase2b_apify_daily_pipeline_guide.md` | Phase 2B 단계별 구현 가이드 |
| `docs/session_log/2026-06-16_session-13_strategy-redesign-ac.md` | 이번 전략 결정 세션 로그 |
| `docs/adinsight_project_blueprint.md` | 원본 마스터 설계서 (업데이트 예정) |
| `docs/portfolio_draft.md` | Phase별 메트릭 기록 작업장 |
