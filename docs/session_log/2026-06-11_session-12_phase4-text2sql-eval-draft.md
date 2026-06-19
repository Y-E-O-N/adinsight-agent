# Session 12 — Phase 4 Text2SQL Eval Draft (2026-06-11)

**Phase**: Phase 4 — AI-Native Mart + Text2SQL Evaluation
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- Session 11 기준선에서 전체 dbt run/test를 재검증한다.
- dbt docs artifact에서 `marts -> ai_native` lineage와 semantic metadata 적재를 확인한다.
- 첫 Text2SQL 평가 질문셋 초안을 만든다.

## Done
- [x] `dbt run --profiles-dir /opt/dbt` 6/6 pass
- [x] `dbt test --profiles-dir /opt/dbt` 50/50 pass
- [x] `dbt docs generate --profiles-dir /opt/dbt` 성공
- [x] `dbt/target/manifest.json`에서 `ai_creator_sponsored_summary` dependency와 `meta` 확인
- [x] `docs/analysis/stage4_text2sql_eval_questions.md` 작성
- [x] `agent/eval/text2sql_questions.yml` 작성
- [x] expected SQL 10개 실행 및 current row count 기록

## Decisions
- **평가셋은 docs + YAML 두 층으로 둔다**: `docs/analysis/`는 사람이 읽는 설계 문서, `agent/eval/`은 이후 evaluator가 읽는 구조화 입력으로 둔다.
- **첫 평가 범위는 schema retrieval과 column selection**: 아직 generated SQL accuracy를 측정하기 전이므로, expected SQL과 row count 기준선을 먼저 만든다.
- **복합 조건 질문은 현재 데이터에 결과가 있는 조건으로 조정**: `total_posts >= 2 and sponsored_candidate_posts >= 1`은 0건이라 `total_posts >= 2 and sponsored_candidate_posts = 0` 질문으로 바꿨다.

## Files changed
- `docs/analysis/stage4_text2sql_eval_questions.md` — Text2SQL 평가 질문셋 설계 문서
- `agent/eval/text2sql_questions.yml` — evaluator 입력용 질문 10개, expected columns, required features, expected SQL, current row counts
- `docs/daily_log.md` — 2026-06-11 Text2SQL 평가셋 작업 기록 추가
- `metrics/run_results.jsonl` — Phase 4 eval draft 메트릭 append
- `CLAUDE.md` — 현재 Phase와 직전 세션 요약 갱신
- `docs/session_log/README.md` — Session 12 인덱스 추가

## Concepts taught (학습 강화)
- **Text2SQL eval question** — 자연어 질문, expected table, expected columns, required SQL feature, expected SQL을 분리해 평가 기준을 만든다.
- **dbt docs artifact** — `manifest.json`에서 model dependency와 dbt YAML `meta`가 실제 artifact에 들어갔는지 확인했다.
- **Data-dependent eval** — 평가 SQL이 0건만 반환하면 디버깅 신호가 약하므로 현재 데이터 분포에 맞춰 질문 조건을 조정했다.

## Portfolio assets added
- 문서: `docs/analysis/stage4_text2sql_eval_questions.md`
- 구조화 평가셋: `agent/eval/text2sql_questions.yml`
- 메트릭: `metrics/run_results.jsonl`에 `p4.text2sql_eval_questions_draft` append

## Open questions
- evaluator를 `uv run` 로컬 스크립트로 만들지, Airflow/dbt task와 연결할지 결정 필요
- generated SQL 평가에서 exact match, required feature match, result equivalence 중 무엇을 1차 기준으로 삼을지 결정 필요
- dbt docs lineage screenshot을 Phase 4 포트폴리오 이미지로 새로 캡처할지 결정 필요

## Metrics
- `dbt run`: 6/6 pass
- `dbt test`: 50/50 pass
- Text2SQL eval questions: 10
- Korean questions: 5
- English questions: 5
- Expected SQL validation: 10/10 executable
- Current row count range: 3~44 rows

## Next session — start here
1. 현재 상태를 확인한다.
   ```bash
   docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"
   ```
2. `agent/eval/text2sql_questions.yml`을 읽는 evaluator를 만든다.
   - 후보 파일: `agent/eval/run_expected_sql.py`
   - 입력: YAML 질문셋
   - 출력: question id, expected row count, actual row count, pass/fail
3. evaluator 실행 결과를 `metrics/run_results.jsonl` 또는 별도 `agent/eval/results/`에 저장할지 결정한다.
4. 그다음 generated SQL 평가로 확장한다.
