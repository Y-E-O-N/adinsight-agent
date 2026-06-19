# AdInsight Agent — Claude Code Context

> 매 Claude Code 세션 시작 시 이 파일을 먼저 읽어주세요.
> 1급 참조 문서: `docs/adinsight_project_blueprint.md` (마스터 설계서) · `docs/adinsight_portfolio_template.md` (포트폴리오 템플릿)

---

## 0. 메타 원칙 — 이 프로젝트의 정체성

이 프로젝트는 **포트폴리오용 학습 프로젝트**입니다. Claude 의 모든 작업은 두 축에서 평가됩니다:

- **(A) 포트폴리오 적립** — 코드를 만드는 것이 끝이 아니다. 면접 답변·스크린샷·메트릭·문서·ADR로 환산되어야 한다.
- **(B) 학습 강화 (Teaching-First)** — Yeon 이 코드의 *목적·구조·동작*을 함께 이해할 수 있도록 친절한 설명이 따라붙어야 한다.

코드 + 포트폴리오 자산 + 학습 설명, 이 세 가지가 한 번의 작업 단위(Phase / Task) 에서 모두 산출되어야 합니다.

---

## 1. 프로젝트 한 줄 목표
LINE Pay AI 인사이트 엔지니어 포트폴리오. 인플루언서 광고 집행부터 결제 전환까지 추적하는 분석 플랫폼 + ROAS 예측 ML 모델 + Text2SQL BI Agent.

## 2. 실행 환경
- MacBook (Apple Silicon)
- Docker Desktop (메모리 12GB 할당 권장)
- Python 3.11, uv 패키지 매니저
- Postgres 16 + pgvector / Airflow 2.9 (CeleryExecutor) / dbt-postgres 1.8 / Superset 4.x / LangChain
- LLM: Gemini 2.5 Flash (저비용) + Claude Haiku 4.5 (신뢰성 fallback)

## 3. 작성 언어
- 코드 주석·README·문서: **한국어 우선**, 필요 시 영문 병기
- 변수·함수·테이블·디렉토리명: **영문 snake_case**
- Yeon 과의 소통: **한국어**

---

## 4. 불변 규칙 (Inviolable Rules)

### 데이터·파이프라인
1. `raw` 레이어는 **원본 보존**. 모든 변환은 `staging` 이후.
2. 모든 SQL 은 dbt 모델로 관리. 애드혹 SQL 은 `docs/` 또는 노트로만.
3. PII (이메일·실명) 는 `staging` 에서 즉시 해시. raw 외부 노출 금지.
4. 모든 파이프라인은 **idempotent** (MERGE / upsert).
5. 타임스탬프는 **UTC 저장**, 표시 시점에 지역 변환.
6. 모든 `ai_native` 모델은 dbt YAML `meta` 에 `synonyms`, `example_questions`, `grain` 명시.
7. Text2SQL Agent 는 **반드시 validator 통과 SELECT 만** 실행.
8. 지표 기록은 `metrics/recorder.py` 사용.
9. 시크릿은 `.env` 에만, 절대 커밋 금지 (`detect-secrets` pre-commit).

### 포트폴리오 안티패턴 회피 ⭐
10. **수치 없는 추상어 금지** — "확장 가능한 · 견고한 · 효율적인" 같은 무근거 수식어 사용 금지. 항상 `rows / ms / %` 등 측정값으로 대체.
11. **JD 단어 그대로 복붙 금지** — README/문서에 "AI-Native 데이터 마트 구축" 만 쓰면 JD 외우기. *무엇을* 어떻게 *구현했는지* 구체로.
12. **Before/After 표는 실측만** — 추정값 금지. 정직한 낮은 숫자 > 거짓 높은 숫자.
13. **스크린샷·메트릭은 작업이 살아있을 때 즉시** 캡처/기록. 끝난 뒤 재현 불가 (데모 데이터가 바뀜).
14. **한계 섹션 생략 금지** — 모든 산출물에 "Known Limitations" 한 줄이라도 포함.

---

## 5. 디렉토리 규칙

| 경로 | 용도 | 갱신 시점 |
|---|---|---|
| `infra/` | Docker, compose, init SQL | Phase 1 |
| `dags/` | Airflow DAG | Phase 2~ |
| `dbt/` | dbt project (staging / intermediate / marts / ai_native) | Phase 3~4 |
| `agent/` | Text2SQL Agent (chains / prompts / eval / embeddings) | Phase 6 |
| `data_generation/` | SDV·Faker 합성 데이터 생성기 | Phase 2 |
| `dashboards/` | Superset YAML export | Phase 5 |
| `metrics/` | 자동 기록 (`run_results.jsonl` + `portfolio_metrics.md`) | 매 Phase |
| `reports/` | 주간 LLM 리포트 산출물 (gitignore) | Phase 7 |
| `tests/` | unit / integration | 상시 |
| `api/` | 향후 FastAPI 자리 (현재 미사용, 유지) | Phase 6 후반 |
| **`docs/`** | 아키텍처·면접·세션 로그·포트폴리오 ⭐ | 상시 |
| ├ `docs/adinsight_project_blueprint.md` | 마스터 설계서 | 고정 |
| ├ `docs/adinsight_portfolio_template.md` | 포트폴리오 템플릿 | 고정 |
| ├ `docs/portfolio_draft.md` | **포트폴리오 작업장** (Phase 진행 중 채움) | 매 Phase 끝 |
| ├ `docs/daily_log.md` | 매일 10분 적립 루틴 | 매 작업일 |
| ├ `docs/images/` | 스크린샷·다이어그램 (`NN_topic.png`) | 즉시 캡처 |
| ├ `docs/adr/` | Architecture Decision Records | 의사결정 시 |
| └ `docs/session_log/` | 세션별 진행 로그 | 매 세션 종료 |

---

## 6. 작업 방식 (필수 워크플로)

1. **계획 우선 (Plan-First)** — 변경 전에 ① 만들/수정할 파일 목록 ② 각 파일의 역할 ③ 미확인 항목(질문)을 **번호 매겨** 제시 → 사용자 confirm → 가이드 모드로 구현
2. **가이드 모드 구현 (Guided-Coding)** ⭐ — Yeon 은 초보자이며, 프로덕션 파일은 **본인이 직접 타이핑**한다. Claude 의 역할은 멘토:
   - (a) **Pre-code 매우 상세 설명** — 관련 개념, 언어 규칙(들여쓰기·import 순서·타입힌트·주석 관례), 네이밍 관행(snake_case·UPPER_SNAKE·PascalCase 선택 근거), 사용할 모든 키워드·데코레이터·연산자·식별자의 의미와 대안. 사소한 문법까지 누락 금지
   - (b) Concept / Structure / **한국어 주석 포함 참고 스니펫** / 라인별 해설 제공
   - (c) Yeon 이 자신의 에디터에서 파일을 직접 타이핑·저장
   - (d) Yeon 이 **"작성완료"** 또는 **"done"** 으로 신호
   - (e) Claude 가 Read → 오타·누락·문법 오류·보안 이슈 리뷰 → 교육적 피드백
   - (f) Yeon 이 수정 반영 → 최종 확인
3. **Claude 의 Write/Edit 예외** (위 원칙에서 직접 파일 작성이 허용되는 경우만):
   - (i) **문서류** — 세션 로그, `portfolio_draft.md`, ADR, README, `metrics/*.jsonl` 등 학습 외 산출물
   - (ii) **Boilerplate 삭제·이동** — 사전 합의된 리팩터링·이관 작업
   - (iii) Yeon 이 명시적으로 **"대신 써줘"** 요청
   - → 모호하면 항상 확인하고 Yeon 이 쓰도록 유도
4. **모호하면 질문**, 추측 코딩 금지
5. 한 번에 너무 많은 파일을 건드리지 말 것 (Phase 단위로 분할). 한 번에 1 파일 가이드 원칙
6. 변경 후 관련 테스트 실행 (`make test`)
7. 각 Phase·세션 완료 시 `metrics/run_results.jsonl` append + `docs/portfolio_draft.md` 갱신
8. **세션 로그 작성** (§9 참조)

---

## 7. 교육형 진행 원칙 (Teaching-First Workflow) ⭐

신규 코드·파일·도구·패턴·SQL·DAG 를 도입할 때마다 **5요소**를 함께 제공합니다 (간결하게):

| 요소 | 내용 | 분량 가이드 |
|---|---|---|
| **① Concept** | 무엇이고, 왜 이게 필요한가 | 3~5문장 |
| **② Structure** | 프로젝트 어디에 어떻게 끼는가 (디렉토리·의존성·호출 관계) | 표·다이어그램·짧은 트리 |
| **③ Code Walkthrough** | 핵심 로직 5~10줄 라인별 짧은 해설 | 인라인 주석 또는 bullet |
| **④ References** | 신뢰할 만한 외부 링크 1~2개 (공식 문서 우선) | URL 1~2개 |
| **⑤ Verify** | 사용자가 진행을 확인할 한 줄 명령 | `make ...` / `psql ...` 한 줄 |

### 큰 흐름
- **한 번에 신규 개념 ≤ 3개** (인지 부하 관리). 더 필요하면 단계 분할.
- **첫 등장 약어/용어는 풀어 쓰기** (예: BRIN = *Block Range INdex*; SCD2 = *Slowly Changing Dimension Type 2*).
- 사용자가 이미 안다고 표시한 것은 짧게, 처음 보는 것은 친절히.
- **"왜 이걸로 했는가"의 trade-off 1줄** (대안 vs 선택 — 예: *"DuckDB 대신 Postgres 선택 — 운영 환경 유사성 ↑, 단 OLAP 성능 ↓"*).
- 코드만 던지지 않는다. 항상 *왜·어디서·어떻게·다음에 뭘 확인* 까지.

### 예시 — Concept-Structure-Walkthrough 형태
> **Concept**: BRIN 인덱스는 시계열 데이터처럼 자연 정렬된 컬럼에 효과적인 가벼운 인덱스. B-tree 가 모든 행에 포인터를 두는 반면 BRIN 은 페이지 범위(예: 128페이지) 의 min/max 만 저장 → 인덱스 크기 1/100, 시계열 필터에 빠름.
>
> **Structure**: `dbt/models/marts/fct_post_daily.sql` 의 post-hook 으로 인덱스 생성. Superset 차트가 `WHERE date BETWEEN ...` 으로 항상 시계열 범위 조회.
>
> **Walkthrough**: `CREATE INDEX ... USING BRIN (date) WITH (pages_per_range=64)` — `pages_per_range` 작을수록 정확도 ↑·크기 ↑. 64는 일별 파티션 1주일 분량.
>
> **References**: <https://www.postgresql.org/docs/16/brin.html>
>
> **Verify**: `EXPLAIN ANALYZE SELECT ...` → `Bitmap Index Scan on idx_brin_date` 가 보이면 OK.

---

## 8. 포트폴리오 First 원칙 ⭐

모든 Phase 작업 = **코드 + 포트폴리오 자산**. 작업 끝날 때마다:

- (a) `metrics/run_results.jsonl` 에 측정값 append (`from metrics.recorder import log`)
- (b) `docs/portfolio_draft.md` 의 해당 Phase 칸 채우기
- (c) 캡처할 만한 화면이면 `docs/images/NN_topic.png` 즉시 저장
- (d) 큰 결정은 `docs/adr/00X-...md` 1~2페이지 ADR

### Phase 별 포트폴리오 적립 핵심

| Phase | 적립 핵심 메트릭 | 캡처할 시각 자료 |
|---|---|---|
| 1 | `make up` 시간, 이미지 총 크기, `.env` 변수 수 | docker compose ps 화면 |
| 2 | raw 행 수, 국가 분포, ingest 시간, idempotency 5회 검증 | DAG 그래프 스크린샷 |
| 3 | dbt 모델 수, 테스트 수, 컬럼 description 커버리지%, run 시간 | dbt docs lineage |
| 4 | ai_native 테이블 수, synonyms 언어 수, 임베딩 빌드 시간 | ERD (ai_native 중심) |
| 5 | 대시보드 수, **Before/After EXPLAIN**, 인덱스 후 쿼리 시간 | 대시보드 + EXPLAIN 콘솔 |
| 6 | Exec Acc (전체/언어별/난이도별), p50/p95, $/query, Refuse Rate | Text2SQL 데모 GIF + 평가표 |
| 7 | 리포트 생성 시간, 토큰 비용, 수치 검증 (수동 hand count) | 샘플 주간 리포트 |
| 8 | pytest 통과 / 커버리지, dbt test 수, CI 시간 | GitHub Actions 배지 |
| 9 | locust 동접 결과, singleflight dedup 비율, fallback 횟수 | locust 그래프 |

상세는 `docs/adinsight_portfolio_template.md` §7 (메트릭 카탈로그) + §8 (스크린샷 체크리스트).

---

## 9. 세션 로그 규율 (⭐)

세션 = Claude Code 한 번 실행 단위 (≈ 1~3시간).

### 세션 시작 시
1. 이 `CLAUDE.md` 읽기
2. `docs/session_log/` 의 가장 최신 1~2개 파일 읽고 **"Next session — start here"** 확인
3. 오늘 할 일을 사용자와 합의

### 세션 종료 시
1. `docs/session_log/YYYY-MM-DD_session-NN_<topic>.md` 새 파일 작성
2. 템플릿 항목:
   - **Goals / Done / Decisions / Files changed**
   - **Concepts taught** ⭐ — 이번 세션에서 사용자에게 친절히 설명한 신규 개념·도구
   - **Portfolio assets added** ⭐ — 이번 세션에서 적립된 메트릭·이미지·ADR·샘플 산출물
   - **Open questions / Metrics / Next session — start here**
3. `docs/session_log/README.md` 인덱스 한 줄 추가
4. **`docs/learning/session-NN_concepts.md` 신규 작성** ⭐ — 이번 세션에서 배운 개념·디버깅·패턴을 Yeon 이 나중에 복습할 수 있도록 정리 (예: `session-04_concepts.md`)
5. 이 `CLAUDE.md` 의 **§11 직전 세션 요약** 갱신
6. (해당 시) `docs/daily_log.md` 한 줄 append

---

## 10. 현재 Phase
**Phase 3B — campaign/payment dbt 모델 확장 중**
- 재설계 기준 문서: `docs/guides/project_redesign_master_guide.md`
- 새 피치: **인플루언서 광고 집행 → 결제 전환 분석 플랫폼 + ROAS 예측 ML 모델 + Text2SQL BI Agent**
- Phase P 포지셔닝 재정립 완료: `CLAUDE.md`, `README.md`, `docs/adinsight_project_blueprint.md`, ADR 003, redesign guide 현재 위치 표를 A+C 전략 기준으로 정렬했다.
- 전략 방향: 기존 Phase 0~3 구현은 유지하고, 부족했던 5가지 갭을 보강한다.
  - 데이터 49행 → Apify 운영 자동화 + 합성 결제 데이터로 규모 보강
  - ML 모델 없음 → LightGBM 기반 ROAS 예측 모델 추가
  - Agent 없음 → Text2SQL Agent v1/v2/v3와 Exec Acc 측정 추가
  - FastAPI 없음 → `/query`, `/predict` 데이터 서빙 API 추가
  - 핀테크 연결 약함 → payment conversion / campaign ROI / ROAS 도메인으로 확장
- 현재 구현 우선순위:
  1. **Phase 2B — Apify 운영 등급 자동화 파이프라인**: daily adaptive DAG와 backfill DAG 구현/검증 완료.
  2. **Phase 2C — 합성 결제 데이터 생성기**: 실제 Apify observed likes/comments 기반 campaign attribution/payment events 생성, raw+staging 적재, stale payment sync, dbt test 완료.
  3. **Phase 3B — dbt 모델 확장**: campaign ROI intermediate/mart 1차 구현 완료. 다음은 ai_native/feature mart 확장.

### 유지되는 기존 완료 상태
- 데이터 소싱 결정: **Apify 실수집 + SDV 합성** 하이브리드
- Round 1 시드 3개 합의: `#뷰티` (광역) / `#올리브영` (브랜드) / `#다이소화장품` (니치)
- Stage 0: `collect_hashtag()` 함수 + smoke DAG → 로컬·Airflow 양쪽 20건 수집 검증 ✅
- Stage 1: `raw.ig_posts` + `raw.ig_post_sources` 설계, psycopg loader, Airflow collect→load DAG, 멱등 5회 검증 ✅
- Stage 2 Round 1: `dags/dag_ig_collect_round1.py` 실행 성공. XCom에 큰 payload를 넘기지 않고 seed별 task 내부에서 collect→load 후 metrics dict만 반환하며, 최종 metrics를 `metrics/run_results.jsonl`에 자동 기록.
- Round 1 결과: 요청 2,000건 대비 실제 수집 49건, 신규 insert 29건, 최종 `raw.ig_posts=49` / `raw.ig_post_sources=49`.
- Stage 3 시작: `staging.stg_ig_posts` dbt view 생성, raw source YAML + staging schema YAML 작성.
- Stage 3 intermediate: `intermediate.int_ig_post_source_quality`, `intermediate.int_ig_sponsored_candidates`, `intermediate.int_ig_owner_activity` view 생성.
- Stage 3 mart: `marts.mart_creator_sponsored_summary` table 생성. creator rows 46건, review 대상 24명, sponsored 후보 게시물 21건.
- Superset: `marts.mart_creator_sponsored_summary` dataset, `Creator Sponsored Review Table` chart, `AdInsight Creator Review` dashboard 생성. 스크린샷과 export ZIP 저장.
- Stage 4 AI-Native mart: `ai_native.ai_creator_sponsored_summary` table 생성. creator rows 46건, `creator_username` grain, model-level `meta.grain`/`meta.synonyms`/`meta.example_questions`와 column-level semantic metadata 작성.
- Stage 4 Text2SQL eval draft: `agent/eval/text2sql_questions.yml`에 10개 bilingual 평가 질문과 expected SQL 작성. 현재 데이터 기준 expected SQL row count 검증 완료.
- 최신 검증: `dbt run` 0.18s / 6 models, `dbt test` 0.42s / 50 tests pass.
- Phase 3 포트폴리오 자산: dbt lineage screenshot `docs/images/03_dbt_lineage.png`, Superset screenshot `docs/images/phase3_creator_review_table.jpg`, Superset export `dashboards/superset_exports/adinsight_creator_review_export.zip`, ADR 002 `docs/adr/002-layered-mart-vs-obt.md`.
- 보류된 기존 다음 작업: `agent/eval/text2sql_questions.yml` 기반 evaluator는 Phase 5B Text2SQL Agent 구현 때 다시 이어간다.
- Phase 2B 최신 결과: `ig_collect_daily` adaptive run 성공(`items_collected_total=1725`, `inserted_total=1410`, freshness ok, watermark `2026-06-16`), `ig_collect_backfill` smoke/idempotency 검증 성공(2회차 `inserted_total=0`, `updated_total=25`).
- Phase 2C 최신 결과: `raw.syn_campaigns=30`, `raw.syn_post_campaign_attributions=500`, `raw.syn_payment_events=498`, gross payment KRW `6,644,169.81`, net payment KRW `6,329,923.59`.
- Phase 3B 최신 결과: `intermediate.int_campaign_payment_performance` view와 `marts.mart_campaign_roi_summary` table 생성. mart grain은 `campaign_id`, rows `30`, payment events `498`, max ROAS `0.5969`, full `dbt test` `124/124 PASS`.
- 다음: campaign ROI mart를 `ai_native` 또는 ML feature layer로 확장하고, Superset/portfolio 자산을 추가한다.

## 11. 직전 세션 요약
- (Session 16 — 2026-06-19) **Phase 3B campaign ROI handoff**: Phase 2C 데이터를 `raw.syn_post_campaign_attributions=500`, `raw.syn_payment_events=498`로 확장하고 payment event stale sync/deterministic RNG를 보강했다. `intermediate.int_campaign_payment_performance`와 `marts.mart_campaign_roi_summary`를 추가해 campaign grain ROI mart를 만들었다. mart rows `30`, payment events `498`, gross payment KRW `6,644,169.81`, net payment KRW `6,329,923.59`, max ROAS `0.5969`. 새 모델 test `29/29 PASS`, full `dbt test` `124/124 PASS`. 커밋 `f1b291f Add campaign payment analytics pipeline`을 `origin/main`에 push했다. 다음은 `ai_native.ai_campaign_roi_summary`, Superset ROI dashboard, 또는 ML feature layer 중 하나로 이어간다.
- (Session 15 — 2026-06-19) **Phase 2C synthetic payment events**: 실제 Apify 수집 데이터의 field availability를 확인해 views/impressions/clicks를 임의 생성하지 않고, likes/comments 기반 `observed_engagement_count/tier`로 campaign attribution과 payment simulation을 구성했다. `raw.syn_campaigns`, `raw.syn_post_campaign_attributions`, `raw.syn_payment_events`와 staging 모델 3개를 추가했고, payment generator는 attribution별 deterministic RNG와 stale event sync를 적용했다. 500 attribution 기준 `raw.syn_payment_events=498`, gross payment KRW `6,644,169.81`, net payment KRW `6,329,923.59`, full `dbt test` `95/95 PASS`. 다음은 Phase 3B campaign ROI/payment conversion dbt 모델 확장.
- (Session 14 — 2026-06-16) **Phase 2B daily/backfill pipeline**: `dags/common/ig_collect_utils.py`, `dags/dag_ig_collect_daily.py`, `dags/dag_ig_backfill.py`를 통해 watermark/freshness, adaptive k, 수동 backfill을 구현/검증했다. daily run은 29개 seed에서 1,725건 수집, 신규 1,410건 insert, freshness ok, watermark `2026-06-16`을 기록했다. backfill은 `#뷰티 k=25` smoke에서 신규 18건 insert 후 같은 실행 반복 시 `inserted_total=0`, `updated_total=25`, `source_links_inserted_total=0`으로 멱등성을 확인했다. 다음은 scheduled daily run 관찰 후 Phase 2B 완료 처리와 Phase 2C 합성 결제 데이터 생성기로 이동.
- (Session 13 — 2026-06-16) **A+C 전략 재설계 반영**: `docs/guides/project_redesign_master_guide.md`를 기준으로 프로젝트 피치를 “인플루언서 광고 집행 → 결제 전환 분석 + ROAS 예측 ML + Text2SQL BI Agent”로 재정렬한다. 기존 Phase 0~3 산출물과 Phase 4 ai_native/eval 초안은 보존하고, 다음 우선순위를 Phase 2B Apify 운영 자동화, Phase 2C 합성 결제 데이터, Phase 3B dbt 확장으로 바꾼다. ADR 003으로 재설계 근거를 남긴다.
- (Session 12 — 2026-06-11) **Phase 4 Text2SQL eval draft**: `dbt run/test` 기준선 6 models / 50 tests 재검증, `dbt docs generate` 실행, manifest에서 `ai_native.ai_creator_sponsored_summary -> marts.mart_creator_sponsored_summary` dependency와 dbt `meta` artifact 적재 확인. `docs/analysis/stage4_text2sql_eval_questions.md`와 `agent/eval/text2sql_questions.yml`에 bilingual Text2SQL 질문 10개, expected columns, required SQL features, expected SQL, current row counts를 작성. expected SQL 10개 모두 Postgres에서 실행 확인. 다음은 YAML 기반 evaluator 구현.
- (Session 11 — 2026-06-11) **Phase 4 AI-Native mart first model**: baseline dbt run/test 재검증 후 `ai_native.ai_creator_sponsored_summary`를 추가. `owner_*`를 자연어 친화적인 `creator_*` 컬럼으로 rename하고, dbt YAML에 model-level `meta.grain`, `meta.synonyms`, `meta.example_questions`와 column-level semantic descriptions/synonyms를 작성. `dbt_project.yml`에 `ai_native` schema/table 설정 추가. 전체 dbt run 0.18s / 6 models, dbt test 0.42s / 50 tests 통과. 설계 노트: `docs/analysis/stage4_ai_creator_sponsored_summary_design.md`
- (Session 10 — 2026-06-09) **Phase 3 creator mart + Superset asset**: `int_ig_sponsored_candidates`, `int_ig_owner_activity`, `mart_creator_sponsored_summary`를 추가하고 schema tests를 연결. 전체 dbt run 0.18s / 5 models, dbt test 44/44 통과. Superset admin 초기화 후 `marts.mart_creator_sponsored_summary` dataset, `Creator Sponsored Review Table` chart, `AdInsight Creator Review` dashboard를 만들고 screenshot/export를 포트폴리오 자산으로 저장. 이후 dbt lineage screenshot과 ADR 002(`Layered mart vs OBT`)까지 추가해 Phase 3 마감 자산을 보강. 다음은 Phase 4 AI-Native mart 설계 시작. 상세: `docs/session_log/2026-06-09_session-10_phase3-creator-mart-superset.md`
- (Session 09 — 2026-06-05) **Phase 3 dbt staging + first intermediate**: Round 1 raw 49건을 SQL로 프로파일링하고, `staging.stg_ig_posts` dbt view를 작성해 `likes_hidden`, `likes_count_clean`, `is_sponsored_candidate`, `source_hashtags` 등 raw→staging 변환 컬럼을 설계. 이어서 `intermediate.int_ig_post_source_quality`로 seed별 수집 품질을 요약해 `#다이소화장품`만 현재 sponsored 분석 후보로 분류. `dbt-core 1.8.8` / `dbt-postgres 1.8.2` 환경에서 전체 dbt test 24/24 통과. 다음은 `int_ig_sponsored_candidates` 또는 `int_ig_owner_activity` 중 하나 선택. 상세: `docs/session_log/2026-06-05_session-09_phase3-dbt-staging-intermediate.md`
- (Session 08 — 2026-05-27) **Phase 2 Stage 2 Round 1 DAG 작성 및 첫 실행**: `dags/dag_ig_collect_round1.py` 신규 작성, seed 3개(`뷰티` K=600 / `올리브영` K=1000 / `다이소화장품` K=400)를 task 내부 collect-and-load 구조로 설계, metrics recorder task 추가, Airflow manual run 성공. 결과는 요청 2,000건 대비 실제 수집 49건, 신규 insert 29건, 최종 `raw.ig_posts=49` / `raw.ig_post_sources=49`. 파이프라인은 성공했지만 데이터 충분성은 부족하므로, 추가 수집 전 Actor 입력 옵션 또는 seed 확장 전략을 별도 판단. 상세: `docs/session_log/2026-05-27_session-08_phase2-stage2-round1-setup.md`
- (Session 07 — 2026-05-26) **Phase 2 Stage 1 raw loader 완료**: `raw.ig_posts` 원본 게시물 테이블과 `raw.ig_post_sources` source lineage 테이블 설계, psycopg 기반 `INSERT ... ON CONFLICT` loader 작성, Airflow `ig_collect_smoke` DAG를 collect→load 구조로 확장, worker 환경변수/psycopg 이미지 재빌드/paused DAG/APIFY_TOKEN 인증 오류 디버깅, `#다이소화장품` 20건 기준 DAG 5회 success 및 row count 20/20 유지로 멱등성 검증. 상세: `docs/session_log/2026-05-26_session-07_phase2-stage1-raw-loader.md`
- (Session 06 — 2026-05-07) **Codex 세션 로그 규칙 정비**: 기존 raw 대화 로그 위치 (`logs/session_YYYYMMDD_HHMMSS.log`) 와 Codex 내부 원본 로그 위치 (`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`) 확인, Codex 전용 프로젝트 지침 `AGENTS.md` 추가, `docs/session_log/README.md` 를 Claude Code/Codex 공통 세션 로그 규칙으로 확장, 현재 세션 로그 작성. 상세: `docs/session_log/2026-05-07_session-06_codex-session-logging.md`
- (Session 05 — 2026-04-28) **Phase 2 Stage 0 완료**: Apify 가입($29) + 토큰 셋업, 데이터 소싱·시드·K·스노우볼 알고리즘 합의, 가이드 모드로 5개 코드 파일 작성 (collect_hashtag/`__main__.py`/smoke DAG/`__init__.py` 2개), `docker-compose.yml` PYTHONPATH+APIFY_TOKEN+볼륨 마운트 추가, `requirements.txt` apify-client 추가, Airflow 이미지 재빌드, 로컬·DAG 양쪽 smoke 성공 (20건), PYTHONPATH 함정 디버깅, 응답 스키마 적립 (`docs/notes/instagram_post_schema_sample.json`), 시크릿 운용 3단계 마이그 계획 메모리화. 상세: `docs/session_log/2026-04-28_session-05_phase2-stage0.md`
- (Session 04 — 2026-04-20) **Phase 1 스택 기동 완료**: `make up` 실행, 버그 3개 디버깅 (ARG 스코프·pgvector 버전·chmod), Smoke DAG 성공, 스크린샷 2장, GitHub 푸시. 상세: `docs/session_log/2026-04-20_session-04_phase1-live.md`

---

## 12. 핵심 참조 문서

| 문서 | 위치 | 언제 보나 |
|---|---|---|
| **재설계 마스터 가이드** | `docs/guides/project_redesign_master_guide.md` | 현재 Phase/다음 작업을 정할 때 최우선 확인 |
| **마스터 설계서** | `docs/adinsight_project_blueprint.md` | 원본 설계와 도메인/JD 매핑을 확인할 때. 최신 실행 순서는 재설계 마스터 가이드 우선 |
| **SK AX 적용안** | `docs/lecture/SK AX/adinsight_application_plan.md` | Phase 설계·포트폴리오 스토리 정리 시 (L0/L1/L2, 메타데이터, Self-Service, 운영 모니터링) |
| **포트폴리오 템플릿** | `docs/adinsight_portfolio_template.md` | 포트폴리오 산출물 정리할 때 (§7 메트릭 / §8 스크린샷 체크리스트) |
| **포트폴리오 작업장** | `docs/portfolio_draft.md` | 매 Phase 끝에서 빈 자리 채움 |
| **일일 적립 로그** | `docs/daily_log.md` | 매 작업일 한 줄 append |
| **도메인 용어집** | `docs/glossary_deep_dive.md` | 비즈 용어가 등장할 때 |
| **학습 자료** | `docs/01_beginner.md` / `02_intermediate.md` / `03_complete.md` | 개념 깊게 파야 할 때 |
| **세션 로그** | `docs/session_log/` | 매 세션 시작·종료 |
