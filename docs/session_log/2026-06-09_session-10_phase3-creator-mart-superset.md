# Session 10 — Phase 3 Creator Mart + Superset Asset (2026-06-09)

**Phase**: Phase 3 — dbt staging / intermediate / marts
**Duration**: ~2h
**Operator**: Yeon (with Codex)

## Goals
- `int_ig_sponsored_candidates`와 `int_ig_owner_activity` intermediate 모델을 완성한다.
- 첫 creator mart인 `mart_creator_sponsored_summary`를 만든다.
- Superset dataset/chart/dashboard를 만들고 포트폴리오 스크린샷과 export로 남긴다.
- Phase 3 메트릭을 `metrics/run_results.jsonl`과 `docs/portfolio_draft.md`에 고정한다.

## Done
- [x] `intermediate.int_ig_sponsored_candidates` view 생성 및 schema tests 8개 통과
- [x] `intermediate.int_ig_owner_activity` view 생성 및 schema tests 7개 통과
- [x] `marts.mart_creator_sponsored_summary` table 생성 및 schema tests 5개 통과
- [x] `dbt_project.yml`에 `marts` schema/table materialization 설정 추가
- [x] 전체 dbt run/test 순차 검증: `dbt run` 0.18s, `dbt test` 44/44 pass
- [x] Superset admin 계정 초기화 (`admin/admin`) 및 권한 sync
- [x] Superset database/dataset/chart/dashboard 생성
- [x] Superset chart screenshot 저장: `docs/images/phase3_creator_review_table.jpg`
- [x] Superset dashboard export 저장: `dashboards/superset_exports/adinsight_creator_review_export.zip`
- [x] `docs/analysis/`에 intermediate/mart 설계 노트 3개 추가
- [x] `metrics/run_results.jsonl`에 Phase 3 완료 메트릭 append
- [x] `docs/portfolio_draft.md` Phase 3 섹션 갱신

## Decisions
- **첫 mart는 creator 단위로 만든다**: Round 1 데이터가 49건으로 작지만, 작성자별 협찬 후보 활동은 Superset 표로 바로 설명 가능하다.
- **marts는 table로 materialize한다**: staging/intermediate는 view, BI가 직접 읽는 mart는 table로 두어 최종 분석 테이블의 경계를 명확히 한다.
- **광고/협찬은 확정값이 아니라 후보값으로 유지한다**: caption 키워드 기반이므로 `sponsored_candidate` 명명과 Known Limitations를 계속 유지한다.
- **Superset export도 남긴다**: 스크린샷만으로는 재현성이 낮으므로 dashboard/chart/dataset/database YAML이 들어 있는 ZIP을 함께 보관한다.

## Files changed
- `dbt/dbt_project.yml` — `marts` schema와 table materialization 설정 추가
- `dbt/models/intermediate/int_ig_sponsored_candidates.sql` — 광고/협찬 후보 게시물 intermediate 모델
- `dbt/models/intermediate/int_ig_owner_activity.sql` — 작성자별 활동 intermediate 모델
- `dbt/models/intermediate/schema.yml` — intermediate 모델 descriptions + data tests
- `dbt/models/marts/creator/mart_creator_sponsored_summary.sql` — 첫 creator mart table
- `dbt/models/marts/creator/schema.yml` — creator mart descriptions + data tests
- `docs/analysis/stage3_int_ig_sponsored_candidates_design.md` — sponsored 후보 모델 설계 노트
- `docs/analysis/stage3_int_ig_owner_activity_design.md` — owner activity 모델 설계 노트
- `docs/analysis/stage3_mart_creator_sponsored_summary_design.md` — creator mart 설계 노트
- `docs/images/phase3_creator_review_table.jpg` — Superset creator review table screenshot
- `dashboards/superset_exports/adinsight_creator_review_export.zip` — Superset dashboard/chart/dataset export
- `docs/portfolio_draft.md` — Phase 3 메트릭, 스크린샷, BI export 기록
- `metrics/run_results.jsonl` — `p3.creator_mart_superset_complete` 메트릭 append

## Concepts taught (학습 강화)
- **dbt model contract** — `schema.yml`의 모델명/컬럼명이 실제 SQL 결과와 맞아야 test가 연결된다.
- **YAML indentation** — 들여쓰기는 보기용이 아니라 구조 자체이며, sibling/child 관계가 틀리면 dbt parser가 실패한다.
- **staging vs intermediate vs mart** — staging은 row-level 정제, intermediate는 재사용 계산 단위, mart는 BI가 읽는 최종 분석 테이블이다.
- **Superset Docker host** — Superset 컨테이너에서 Postgres를 볼 때 host는 `localhost`가 아니라 Docker Compose service name인 `postgres`다.
- **dbt run/test 순서** — view 재생성 중 test가 병렬로 먼저 실행되면 relation missing이 날 수 있으므로 검증은 `dbt run && dbt test` 순차 실행이 안전하다.
- **portfolio asset lifecycle** — 모델 → test → Superset chart → screenshot/export → metrics/portfolio draft까지 이어져야 포트폴리오 증거가 된다.

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl`에 `p3.creator_mart_superset_complete` append
- ADR: `docs/adr/002-layered-mart-vs-obt.md`
- 이미지: `docs/images/03_dbt_lineage.png`
- 이미지: `docs/images/phase3_creator_review_table.jpg`
- BI export: `dashboards/superset_exports/adinsight_creator_review_export.zip`
- 작업장 갱신: `docs/portfolio_draft.md` Phase 3 섹션
- 분석 설계 노트:
  - `docs/analysis/stage3_int_ig_sponsored_candidates_design.md`
  - `docs/analysis/stage3_int_ig_owner_activity_design.md`
  - `docs/analysis/stage3_mart_creator_sponsored_summary_design.md`

## Open questions
- Round 1 데이터 49건으로 Phase 4 AI-Native mart를 시작할지, 추가 수집을 먼저 할지 결정 필요
- Phase 4 전에 `ai_native` layer의 meta/synonyms/example_questions 설계 범위를 정해야 한다.

## Metrics
- dbt models: 5 (`staging=1`, `intermediate=3`, `marts=1`)
- dbt run: 5/5 pass, 0.18s
- dbt test: 44/44 pass, 0.37s
- raw posts: 49
- creator mart rows: 46
- included creator review rows: 24
- sponsored candidate posts: 21
- Superset dataset: `marts.mart_creator_sponsored_summary`
- Superset chart: `Creator Sponsored Review Table`
- Superset dashboard: `AdInsight Creator Review`

## Next session — start here
1. 현재 상태를 확인한다.
   ```bash
   docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"
   ```
2. Phase 4 AI-Native mart 설계를 시작한다.
   - 입력 모델: `marts.mart_creator_sponsored_summary`
   - 첫 후보 모델: `ai_native.ai_creator_sponsored_summary`
   - 설계할 YAML metadata: `meta.grain`, `meta.synonyms`, `meta.example_questions`, 컬럼별 semantic description
3. 먼저 아래 질문에 답한다.
   - Text2SQL Agent가 어떤 자연어 질문을 이 mart에 던질 것인가?
   - `creator`, `influencer`, `작성자`, `크리에이터` 같은 동의어를 어디에 둘 것인가?
   - 현재 49건 데이터로 AI-Native layer를 시작할지, 추가 수집을 먼저 할지 결정할 것인가?
4. 참고 자산:
   - dbt lineage screenshot: `docs/images/03_dbt_lineage.png`
   - Superset screenshot: `docs/images/phase3_creator_review_table.jpg`
   - Superset export: `dashboards/superset_exports/adinsight_creator_review_export.zip`
   - ADR 002: `docs/adr/002-layered-mart-vs-obt.md`
