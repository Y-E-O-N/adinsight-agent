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
LINE Pay AI Insight Engineer JD 타깃 포트폴리오. 글로벌 인플루언서 광고 성과 분석 + AI-Native data mart + Text2SQL BI Agent.

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
**Phase 1 — 완료 ✅**
- 8개 컨테이너 전부 healthy (`make up` 10.7s)
- Smoke DAG 성공 (1s), 스크린샷 2장 적립, GitHub 푸시 완료
- 다음: **Phase 2** — 합성 데이터 생성 (`data_generation/generators/`) + Airflow ingest DAG

## 11. 직전 세션 요약
- (Session 04 — 2026-04-20) **Phase 1 스택 기동 완료**: `make up` 실행, 버그 3개 디버깅 (ARG 스코프·pgvector 버전·chmod), Smoke DAG 성공, 스크린샷 2장, GitHub 푸시. 상세: `docs/session_log/2026-04-20_session-04_phase1-live.md`
- (Session 03 — 2026-04-19) **Phase 1 코드 완료 + 가이드 모드 전환**: Yeon 이 8개 파일 직접 타이핑, CLAUDE.md §6 가이드 모드 규칙 추가, ADR 001, README Quick Start. 상세: `docs/session_log/2026-04-19_session-03_phase1-compose.md`

---

## 12. 핵심 참조 문서

| 문서 | 위치 | 언제 보나 |
|---|---|---|
| **마스터 설계서** | `docs/adinsight_project_blueprint.md` | Phase 시작 시 (§5 의 Claude Code 프롬프트 그대로 사용) |
| **포트폴리오 템플릿** | `docs/adinsight_portfolio_template.md` | 포트폴리오 산출물 정리할 때 (§7 메트릭 / §8 스크린샷 체크리스트) |
| **포트폴리오 작업장** | `docs/portfolio_draft.md` | 매 Phase 끝에서 빈 자리 채움 |
| **일일 적립 로그** | `docs/daily_log.md` | 매 작업일 한 줄 append |
| **도메인 용어집** | `docs/glossary_deep_dive.md` | 비즈 용어가 등장할 때 |
| **학습 자료** | `docs/01_beginner.md` / `02_intermediate.md` / `03_complete.md` | 개념 깊게 파야 할 때 |
| **세션 로그** | `docs/session_log/` | 매 세션 시작·종료 |
