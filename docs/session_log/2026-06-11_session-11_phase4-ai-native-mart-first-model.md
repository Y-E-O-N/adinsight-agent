# Session 11 — Phase 4 AI-Native Mart First Model (2026-06-11)

**Phase**: Phase 4 — AI-Native Mart
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- Phase 3 종료 기준선에서 전체 dbt run/test를 재검증한다.
- 첫 AI-Native mart인 `ai_native.ai_creator_sponsored_summary`를 설계하고 구현한다.
- `meta.grain`, `meta.synonyms`, `meta.example_questions`의 1차 배치 기준을 정한다.

## Done
- [x] `docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"` 기준선 통과 확인
- [x] `dbt/models/ai_native/ai_creator_sponsored_summary.sql` 추가
- [x] `dbt/models/ai_native/schema.yml`에 model-level semantic metadata와 column-level descriptions/synonyms 추가
- [x] `dbt/dbt_project.yml`에 `ai_native` schema/table 설정 추가
- [x] `docs/analysis/stage4_ai_creator_sponsored_summary_design.md` 설계 노트 추가
- [x] targeted dbt run/test와 전체 dbt run/test 재검증

## Decisions
- **첫 AI-Native mart는 mart 복제 + 자연어 친화 rename으로 시작**: 새 집계 로직을 추가하지 않고 `marts.mart_creator_sponsored_summary`의 row grain을 유지해 lineage와 검증 범위를 작게 유지했다.
- **`owner_*`를 `creator_*`로 rename**: Text2SQL 사용자가 `creator`, `influencer`, `작성자`, `크리에이터`라고 질문할 가능성이 높기 때문에 schema matching을 쉽게 만든다.
- **metadata는 model-level과 column-level에 나눠 배치**: model-level `synonyms`는 테이블 검색, column-level `synonyms`는 컬럼 선택을 돕는다.
- **현재 49건 데이터로 Phase 4를 시작**: 이번 목표는 정확도 평가가 아니라 semantic metadata 설계와 lineage 확장이므로 추가 수집은 뒤로 미뤘다.

## Files changed
- `dbt/dbt_project.yml` — `ai_native` model group을 `ai_native` schema/table materialization으로 설정
- `dbt/models/ai_native/ai_creator_sponsored_summary.sql` — creator-level AI-Native mart 추가
- `dbt/models/ai_native/schema.yml` — `meta.grain`, `meta.synonyms`, `meta.example_questions`, 컬럼별 semantic metadata와 tests 추가
- `docs/analysis/stage4_ai_creator_sponsored_summary_design.md` — Phase 4 첫 모델 설계 결정과 AWS 대응 관계 정리
- `docs/daily_log.md` — 2026-06-11 Phase 4 진행 기록 추가
- `metrics/run_results.jsonl` — Phase 4 첫 모델 검증 메트릭 append
- `CLAUDE.md` — 현재 Phase와 최신 검증 수치 갱신
- `docs/session_log/README.md` — Session 11 인덱스 추가

## Concepts taught (학습 강화)
- **AI-Native mart** — 사람이 읽는 BI mart와 LLM/Text2SQL Agent가 schema retrieval에 쓰기 쉬운 mart의 차이를 구분했다.
- **dbt `meta`** — `grain`, `synonyms`, `example_questions`를 dbt YAML에 넣어 semantic layer의 source of truth로 쓰는 방식을 정리했다.
- **Local-to-AWS mapping** — 로컬 dbt/Postgres/YAML metadata가 AWS의 dbt on ECS/MWAA, Redshift/Aurora, Glue Catalog 또는 Bedrock Agent schema hints로 확장되는 구조를 정리했다.

## Portfolio assets added
- 문서: `docs/analysis/stage4_ai_creator_sponsored_summary_design.md`
- 메트릭: `metrics/run_results.jsonl`에 `p4.ai_native_creator_summary_first_model` append
- dbt 검증: 6 models / 50 data tests pass

## Open questions
- Text2SQL 평가 질문셋을 `docs/analysis/`에 먼저 둘지, `agent/eval/` 구조를 먼저 만들지 결정 필요
- `ai_native` 두 번째 모델을 creator 중심으로 확장할지, sponsored post detail 중심으로 만들지 결정 필요
- dbt docs lineage screenshot을 Phase 4 자산으로 새로 캡처할지 결정 필요

## Metrics
- `dbt run`: 0.18s / 6 models pass
- `dbt test`: 0.42s / 50 tests pass
- `ai_native.ai_creator_sponsored_summary`: 46 rows
- 추가 tests: 6개

## Next session — start here
1. 현재 상태를 확인한다.
   ```bash
   docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"
   ```
2. dbt docs lineage를 생성/확인해 `marts.mart_creator_sponsored_summary -> ai_native.ai_creator_sponsored_summary` 연결을 캡처할지 결정한다.
3. Text2SQL 평가 질문셋 초안을 작성한다.
   - 후보 파일: `docs/analysis/stage4_text2sql_eval_questions.md` 또는 `agent/eval/questions.yml`
   - 시작 질문: `schema.yml`의 `meta.example_questions`
4. 다음 AI-Native 모델 후보를 결정한다.
   - 후보 A: `ai_native.ai_sponsored_post_candidates`
   - 후보 B: `ai_native.ai_creator_review_priority`
