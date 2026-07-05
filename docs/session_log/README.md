# Session Log

세션마다 한 개의 마크다운 파일을 추가합니다. 세션 = Claude Code 또는 Codex 한 번 실행 단위 (≈ 1~3시간).

> 참고: 화면에 출력되는 사용자/assistant 대화 로그의 기본 저장 위치는 현재 작업 디렉터리의 `logs/session_YYYYMMDD_HHMMSS.log` 입니다. Codex 내부 원본 로그도 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` 에 자동 저장되지만, 프로젝트 로그에는 실제 대화만 남기고 지침, 사고 과정, 도구 호출/출력은 저장하지 않습니다. shell 설정의 `codex()` wrapper 로 Codex 를 시작하면 로그 파일이 즉시 생성되고, 이후 대화가 추가될 때마다 실시간 append 됩니다. 이미 열린 Codex 세션에서는 별도 터미널에서 `make session-log` 를 실행해 현재 세션을 미러링할 수 있습니다. 이 폴더의 마크다운 로그는 프로젝트 진행 상황을 사람이 읽기 쉽게 요약한 공식 작업 기록입니다.

## 파일명 규칙
```
YYYY-MM-DD_session-NN_<topic-kebab-case>.md
```
예) `2026-04-16_session-01_bootstrap.md`, `2026-04-23_session-03_phase1-compose.md`

## 작성 규율
- **세션 시작 시**
  1. `CLAUDE.md` 읽기 (Codex 사용 시 `AGENTS.md` 도 함께 읽기)
  2. 이 폴더의 가장 최신 1~2개 파일 읽고 **"Next session — start here"** 확인
  3. Codex 사용 시 shell wrapper 가 현재 작업 디렉터리의 `logs/session_*.log` 실시간 기록 시작
  4. 오늘 할 일을 사용자와 합의

- **세션 종료 시**
  1. 실시간 로거 프로세스 종료 후 `logs/session_YYYYMMDD_HHMMSS.log` 존재 확인 (`logs/` 는 Git 커밋 제외)
  2. 이 폴더에 새 파일 작성 (아래 템플릿)
  3. 이 `README.md` 인덱스 한 줄 추가
  4. 루트 `CLAUDE.md` 의 **§11 직전 세션 요약** 갱신
  5. (해당 시) `docs/daily_log.md` 한 줄 append + `metrics/run_results.jsonl` append

## 템플릿

```markdown
# Session NN — <Topic> (YYYY-MM-DD)

**Phase**: Phase X — <name>
**Duration**: ~XXm
**Operator**: Yeon (with Claude Code/Codex)

## Goals
- ...

## Done
- [x] ...

## Decisions
- **<무엇을>**: <왜 그렇게 결정했는가>

## Files changed
- `path/to/file` — 한 줄 설명

## Concepts taught (학습 강화)
- **<용어/도구/패턴>** — 어떤 맥락에서 어떤 식으로 설명했는지 1줄 (CLAUDE.md §7 Teaching-First 5요소 적용)

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl` 에 append 한 항목
- 이미지: `docs/images/NN_*.png` 신규 캡처
- ADR: `docs/adr/00X-...md` 신규
- 작업장 갱신: `docs/portfolio_draft.md` 어느 칸을 어떤 값으로 채웠는지

## Open questions
- ...

## Metrics
- (수치 요약 — Portfolio assets 와 중복 시 생략 가능)

## Next session — start here
- 다음 세션 시작점 / 우선순위
```

> **두 신규 항목의 의미**
> - **Concepts taught** — 이 프로젝트는 학습 프로젝트. Teaching-First 원칙(CLAUDE.md §7) 준수 여부를 추적.
> - **Portfolio assets added** — 이 프로젝트는 포트폴리오 First. 매 세션이 면접 자산을 적립했는지 추적.

---

## Index
- [2026-04-16 · Session 01 · Bootstrap](2026-04-16_session-01_bootstrap.md) — 폴더 스켈레톤 / CLAUDE.md / Makefile / 메트릭 인프라 / 세션 로그 시스템 셋업
- [2026-04-16 · Session 02 · Portfolio Workflow Setup](2026-04-16_session-02_portfolio-workflow.md) — CLAUDE.md 확장 (포트폴리오 First + Teaching-First) / portfolio_draft / daily_log / images 폴더
- [2026-04-19 · Session 03 · Phase 1 docker-compose 스택](2026-04-19_session-03_phase1-compose.md) — 가이드 모드 전환 + 8개 파일 직접 작성 (smoke DAG / postgres init / airflow / superset / compose) + YAML 검증
- [2026-04-20 · Session 04 · Phase 1 스택 기동 완료](2026-04-20_session-04_phase1-live.md) — make up 버그 3개 디버깅 + 전체 스택 healthy + Smoke DAG 성공 + 스크린샷 + GitHub 푸시
- [2026-04-28 · Session 05 · Phase 2 Stage 0 (Apify smoke + Airflow DAG)](2026-04-28_session-05_phase2-stage0.md) — 데이터 소싱 결정 (Apify+SDV) / 시드 3개 합의 / Apify 가입 / collect_hashtag 함수 + smoke DAG 가이드 모드 / 로컬·Airflow 양쪽 20건 수집 검증 / PYTHONPATH 디버깅 / 응답 스키마 적립
- [2026-05-07 · Session 06 · Codex Session Logging](2026-05-07_session-06_codex-session-logging.md) — Codex raw 로그 위치 확인 / `AGENTS.md` 추가 / 세션 로그 규칙을 Claude Code·Codex 공통으로 확장
- [2026-05-26 · Session 07 · Phase 2 Stage 1 Raw Loader](2026-05-26_session-07_phase2-stage1-raw-loader.md) — `raw.ig_posts`/`raw.ig_post_sources` 설계 / psycopg upsert loader / Airflow collect→load DAG / 멱등 5회 검증
- [2026-05-27 · Session 08 · Phase 2 Stage 2 Round 1 Setup + First Run](2026-05-27_session-08_phase2-stage2-round1-setup.md) — Round 1 본수집 DAG / 첫 manual run 성공 / 요청 2,000건 대비 실제 49건 수집 / raw profile / `staging.stg_ig_posts` / `intermediate.int_ig_post_source_quality` / dbt tests 24개 통과
- [2026-06-05 · Session 09 · Phase 3 dbt Staging + First Intermediate](2026-06-05_session-09_phase3-dbt-staging-intermediate.md) — raw profile / `stg_ig_posts` / `int_ig_post_source_quality` / dbt run/test 24개 통과 / 다음 모델 후보 정리
- [2026-06-09 · Session 10 · Phase 3 Creator Mart + Superset Asset](2026-06-09_session-10_phase3-creator-mart-superset.md) — intermediate 3개 + creator mart 1개 / dbt run 0.18s / dbt test 44개 통과 / Superset dataset·chart·dashboard·export / 포트폴리오 스크린샷
- [2026-06-11 · Session 11 · Phase 4 AI-Native Mart First Model](2026-06-11_session-11_phase4-ai-native-mart-first-model.md) — `ai_native.ai_creator_sponsored_summary` / `meta.grain`·`meta.synonyms`·`meta.example_questions` / dbt run 6개·test 50개 통과
- [2026-06-11 · Session 12 · Phase 4 Text2SQL Eval Draft](2026-06-11_session-12_phase4-text2sql-eval-draft.md) — dbt docs artifact lineage 확인 / bilingual Text2SQL 질문 10개 / expected SQL row count 검증
- [2026-06-16 · Session 13 · Strategy Redesign A+C](2026-06-16_session-13_strategy-redesign-ac.md) — A+C 전략 반영 / 프로젝트 피치 재정렬 / ADR 003 / Phase 2B 착수 지점 정리
- [2026-06-16 · Session 14 · Phase 2B Daily + Backfill Pipeline](2026-06-16_session-14_phase2b-daily-backfill.md) — daily adaptive Apify DAG / freshness·watermark / backfill DAG / 멱등성 검증
- [2026-06-19 · Session 15 · Phase 2C Synthetic Payment Events](2026-06-19_session-15_phase2c-synthetic-payment-events.md) — Apify observed engagement 기반 campaign attribution/payment events / raw+staging 적재 / payment sync / dbt test 95개 통과
- [2026-06-19 · Session 16 · Phase 3B Campaign ROI Handoff](2026-06-19_session-16_phase3b-campaign-roi-handoff.md) — campaign ROI intermediate/mart / payment sync 보강 / dbt test 124개 통과 / commit+push checkpoint
- [2026-06-19 · Session 17 · Campaign ROAS Prediction Monitoring](2026-06-19_session-17_campaign-roas-prediction-monitoring.md) — AI-native campaign ROI / feature layer / baseline ROAS prediction / Superset monitor / Airflow daily scoring DAG / LINE JD cloud tooling strategy
- [2026-06-23 · Session 18 · Text2SQL Campaign Eval Expansion](2026-06-23_session-18_text2sql-campaign-eval-expansion.md) — Text2SQL 평가셋 10→18개 확장 / campaign ROI·prediction monitor expected SQL 추가 / evaluator 18개 통과
- [2026-06-23 · Session 19 · ROAS Model and API Serving Handoff](2026-06-23_session-19_roas-model-api-serving-handoff.md) — ROAS model comparison / architecture visualization / FastAPI `/predict` skeleton / model artifact serving / push checkpoint
- [2026-06-26 · Session 20 · Deterministic Text2SQL Query API](2026-06-26_session-20_deterministic-text2sql-query-api.md) — FastAPI `/query` / expected-SQL registry matching / 영어·한국어 live smoke / commit `848bd27`
- [2026-06-29 · Session 21 · Text2SQL + Superset Demo Runbook](2026-06-29_session-21_text2sql-superset-demo-runbook.md) — Superset monitor와 `/query` demo scenario 연결 / guardrail·AWS mapping / demo GIF capture plan
- [2026-06-29 · Session 22 · Text2SQL Demo GIF Capture](2026-06-29_session-22_text2sql-demo-gif-capture.md) — `/query` live smoke 재측정 / evidence 문서 / dependency-free demo GIF 생성
- [2026-07-01 · Session 23 · AWS Target Architecture](2026-07-01_session-23_aws-target-architecture.md) — MWAA/RDS·Redshift/S3/ECS/QuickSight/CloudWatch target mapping / IaC skeleton boundary
- [2026-07-04 · Session 24 · LLM Text2SQL v2 Design + Mock Endpoint/Eval](2026-07-04_session-24_llm-text2sql-v2-design.md) — v1 fallback/eval baseline 유지 / SQL validator·mock provider·`/query/v2`·v2 eval runner 구현 / pytest 13개 통과
- [2026-07-04 · Session 25 · Full Ruff Cleanup](2026-07-04_session-25_full-ruff-cleanup.md) — 전체 ruff gate 통과 / 기존 import·context-manager·f-string lint 정리 / pytest 13개 통과
- [2026-07-04 · Session 26 · GitHub Actions CI](2026-07-04_session-26_github-actions-ci.md) — Python 3.11 + uv 기반 ruff/pytest workflow / README CI badge / Phase 8C 체크포인트
- [2026-07-04 · Session 27 · CI Remote Pass and Text2SQL Eval Comparison](2026-07-04_session-27_ci-remote-and-text2sql-comparison.md) — GitHub Actions run success 확인 / v1 18 PASS vs v2 mock 2 PASS·16 REFUSED 비교표
- [2026-07-04 · Session 28 · Text2SQL v2 Mock Coverage Expansion](2026-07-04_session-28_text2sql-v2-mock-coverage.md) — p5 campaign ROI·prediction monitor mock coverage 확장 / v2 eval 8 PASS·10 REFUSED·0 BLOCKED
- [2026-07-04 · Session 29 · Text2SQL v2 API Hardening](2026-07-04_session-29_text2sql-v2-api-hardening.md) — statement timeout / best-effort audit log / `/query/v2` 400·404·500 tests / pytest 16개 통과
- [2026-07-04 · Session 30 · Text2SQL v2 Provider Adapter](2026-07-04_session-30_text2sql-v2-provider-adapter.md) — `TEXT2SQL_PROVIDER=mock|http_json` / API·eval runner 공통 provider factory / pytest 20개 통과
- [2026-07-05 · Session 31 · Text2SQL v2 Focused Coverage Expansion](2026-07-05_session-31_text2sql-v2-focused-coverage.md) — creator-review mock coverage 추가 / v2 eval 13 PASS·5 REFUSED·0 BLOCKED / no-LIMIT failure case 문서화
- [2026-07-05 · Session 32 · Portfolio API Examples + Demo Assets](2026-07-05_session-32_portfolio-api-examples-demo-assets.md) — `/query/v2` request/response examples / 3-5분 demo script / interview talking points
- [2026-07-05 · Session 33 · Architecture Diagram Export](2026-07-05_session-33_architecture-diagram-export.md) — README용 `docs/images/00_architecture.svg` 추가 / portfolio checklist 반영
