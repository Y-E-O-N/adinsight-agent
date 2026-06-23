# Session 18 — Text2SQL Campaign Eval Expansion (2026-06-23)

**Phase**: Phase 5/6 — Text2SQL evaluation expansion for campaign ROI and prediction monitor  
**Duration**: ~45m  
**Operator**: Yeon (with Codex)

## Goals
- Session 17의 campaign ROI / ROAS prediction monitor 산출물을 Text2SQL 평가셋에 연결한다.
- 기존 creator-only expected SQL 평가셋을 campaign ROI와 prediction monitoring 질문까지 확장한다.
- daily Apify collection 이후 stale해진 creator row count baseline을 현재 DB 기준으로 갱신한다.
- 다음 세션이 ML model v1 또는 API skeleton으로 바로 이어갈 수 있게 handoff를 남긴다.

## Done
- [x] `agent/eval/text2sql_questions.yml`의 metadata를 Phase 4/5 통합 평가셋으로 갱신했다.
- [x] `p5_q001`~`p5_q008` Text2SQL 질문을 추가했다.
  - campaign ROI 질문 4개
  - prediction monitor 질문 4개
  - KO 4개 / EN 4개
- [x] prediction monitor 질문은 daily snapshot 누적을 고려해 최신 snapshot만 보도록 `max(scoring_snapshot_date)` 필터를 사용했다.
- [x] daily collection으로 바뀐 기존 p4 creator expected row count를 현재 DB 기준으로 갱신했다.
- [x] `docs/analysis/stage4_text2sql_eval_questions.md`에 Stage 5 확장 섹션을 추가했다.
- [x] 전체 expected-SQL evaluator를 재실행해 18개 질문 모두 통과를 확인했다.
- [x] Phase 6 portfolio draft의 평가셋 크기와 증거를 갱신했다.

## Decisions
- **prediction monitor 질문은 최신 snapshot으로 고정한다**: `marts.mart_campaign_roas_prediction_monitor`는 daily DAG가 실행될수록 snapshot rows가 누적된다. 평가 row count가 매일 흔들리지 않게 `scoring_snapshot_date = max(scoring_snapshot_date)` 조건을 expected SQL에 넣었다.
- **현재 평가는 LLM 생성 SQL이 아니라 expected SQL 기준선 검증으로 유지한다**: 아직 Agent runtime이 없으므로 이번 checkpoint는 “질문셋과 정답 SQL이 실행 가능한가”를 검증하는 단계다.
- **stale p4 row count는 현재 DB 기준으로 refresh한다**: daily Apify collection으로 `ai_native.ai_creator_sponsored_summary` row count가 늘었기 때문에 기존 2026-06-11 기준값을 그대로 두면 evaluator가 실패한다.

## Files changed
- `agent/eval/text2sql_questions.yml` — campaign ROI / prediction monitor 질문 8개 추가, p4 row count baseline refresh
- `docs/analysis/stage4_text2sql_eval_questions.md` — Stage 5 Text2SQL 평가 확장 의도, SQL 패턴, row count, limitation 추가
- `docs/portfolio_draft.md` — Phase 6 평가셋 크기와 expected-SQL 검증 결과 갱신
- `metrics/run_results.jsonl` — Airflow scheduled run 메트릭과 Text2SQL expected-SQL checkpoint metric 누적
- `docs/learning/session-18_concepts.md` — snapshot-aware evaluation, stale baseline, expected SQL benchmark 복습 노트
- `docs/session_log/README.md` — Session 18 index 추가
- `CLAUDE.md` — 현재 Phase와 직전 세션 요약 갱신

## Concepts taught
- **Expected SQL benchmark** — Agent가 아직 없을 때 자연어 질문마다 “정답 SQL”을 먼저 고정해 schema/table/column 선택 기준선을 만든다.
- **Snapshot-aware evaluation** — 누적형 snapshot table은 최신 snapshot 필터를 넣지 않으면 daily run마다 row count가 바뀐다.
- **Stale baseline** — 데이터가 늘어난 뒤에도 과거 row count를 기대값으로 두면 코드가 맞아도 평가가 실패한다.

## Portfolio assets added
- Text2SQL 평가셋:
  - 기존 10개 creator 질문에서 18개 질문으로 확장
  - campaign ROI 4개, prediction monitor 4개 추가
- 검증 메트릭:
  - `agent/eval/run_expected_sql.py` 결과 `18/18 PASS`
  - Phase 6 draft에 expected-SQL benchmark 결과 기록
- 분석 문서:
  - `docs/analysis/stage4_text2sql_eval_questions.md` Stage 5 확장 섹션

## Open questions
- 다음 Text2SQL 단계에서 실제 LLM Agent runtime을 먼저 만들지, ROAS ML model v1을 먼저 추가할지 결정한다.
- expected SQL row count는 live data가 더 늘어날 때마다 refresh할지, evaluator fixture용 frozen snapshot을 따로 둘지 결정한다.
- negative set, SQL validator, unsafe SQL 차단 테스트는 아직 구현 전이다.

## Metrics
- Expected-SQL questions: `18`
- Existing creator questions: `10`
- New campaign/prediction questions: `8`
- Language split: KO `9`, EN `9`
- Evaluator result: `18 passed / 0 failed / 18 total`
- Latest prediction monitor snapshot used by new questions: `2026-06-22`
- Latest snapshot rows: `25`

## Next session — start here
1. 현재 상태 확인:
   ```bash
   git status --short
   git diff --stat
   set -a; source .env; set +a; POSTGRES_HOST=localhost uv run python agent/eval/run_expected_sql.py
   ```
2. 현재 checkpoint를 커밋한다.
   - 추천 메시지: `Expand Text2SQL eval for campaign ROI`
3. 다음 기능 우선순위는 **ROAS ML model v1**이다.
   - 후보 파일: `agent/eval/run_campaign_roas_model.py`
   - 목표: baseline `objective_mean_roas_baseline_v1` 대비 sklearn regression MAE/RMSE 비교
   - 기록 위치: `metrics/run_results.jsonl` 또는 `metrics/model_metrics.jsonl`
4. 이후 후보:
   - FastAPI `/predict/campaign-roas` skeleton
   - AWS target architecture / IaC skeleton

