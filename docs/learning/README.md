# Learning Notes — AdInsight Agent

> 세션마다 배운 개념·질문·관계도를 정리한 폴더.
> 면접 답변 준비 + 개념 복습용.

## 파일 구조

각 세션마다 2개 파일:
- `session-NN_qa.md` — 직접 질문한 것들 Q&A
- `session-NN_concepts.md` — 파일별 개념, 컴포넌트 관계도, 오타 패턴, 용어집

---

## 파일 목록

### Session 03 — Phase 1 Docker Compose (2026-04-19)

| 파일 | 내용 |
|---|---|
| [session-03_qa.md](session-03_qa.md) | CMD vs CMD-SHELL / Celery와 Airflow 관계 / Celery vs Thread / Superset이란 / redis: 두 줄 문제 |
| [session-03_concepts.md](session-03_concepts.md) | 8개 파일별 핵심 개념 + 전체 스택 관계도 + task 실행 흐름 + 오타 패턴 + 용어집 |

### Session 04 — Phase 1 Live Debugging (2026-04-20)

| 파일 | 내용 |
|---|---|
| [session-04_concepts.md](session-04_concepts.md) | Docker Compose 기동 디버깅 / Airflow·Postgres·Superset live 검증 |

### Session 05 — Phase 2 Stage 0 Apify Smoke (2026-04-28)

| 파일 | 내용 |
|---|---|
| [session-05_concepts.md](session-05_concepts.md) | Apify 수집 / TaskFlow API / PYTHONPATH / 스노우볼 샘플링 / Stage 0 디버깅 |

### Session 07 — Phase 2 Stage 1 Raw Loader (2026-05-26)

| 파일 | 내용 |
|---|---|
| [session-07_concepts.md](session-07_concepts.md) | L0 raw layer / JSONB 원본 보존 / upsert / source lineage / XCom / 멱등성 검증 |

### Session 08 — Phase 2 Stage 2 Round 1 Setup (2026-05-27)

| 파일 | 내용 |
|---|---|
| [session-08_concepts.md](session-08_concepts.md) | 본수집 DAG 설계 / `k` 의미 / `load_metrics` / XCom payload 회피 / 실행 전 체크 |

### Session 09 — Phase 3 dbt Staging + Intermediate (2026-06-05)

| 파일 | 내용 |
|---|---|
| [session-09_concepts.md](session-09_concepts.md) | raw vs staging / dbt source·model·data tests / `CASE WHEN` / `unnest()` / `COUNT(*) FILTER` / staging vs intermediate |
