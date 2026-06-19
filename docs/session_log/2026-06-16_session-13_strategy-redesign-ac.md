# Session 13 — Strategy Redesign A+C (2026-06-16)

**Phase**: Phase P — 포지셔닝 재정립 / A+C 재설계 반영
**Duration**: ~30m
**Operator**: Yeon (with Codex)

## Goals
- `docs/guides/project_redesign_master_guide.md`를 기준으로 프로젝트 진행 방향을 최신화한다.
- 기존 Phase 0~3 산출물과 Phase 4 ai_native/eval 초안은 보존한다.
- 다음 구현 우선순위를 Phase 2B/2C/3B로 재정렬한다.

## Done
- [x] `CLAUDE.md` 프로젝트 한 줄 목표를 결제 전환·ROAS 예측·Text2SQL Agent 중심으로 교체
- [x] `CLAUDE.md` 현재 Phase를 Phase 2B 착수 지점으로 갱신하고 다음 우선순위를 Phase 2B → 2C → 3B로 변경
- [x] `README.md` TL;DR, JD 매핑, Phase 진행 상황을 A+C 전략에 맞게 수정
- [x] `docs/adinsight_project_blueprint.md` 상단 피치와 도메인 브릿지를 최신화
- [x] `docs/adinsight_project_blueprint.md` 원본 Phase 1~9 섹션에 재설계 우선순위 메모 추가
- [x] `docs/adr/003-redesign-ac-strategy.md` 작성
- [x] `docs/guides/project_redesign_master_guide.md` 현재 위치 표에서 Phase P 완료 처리

## Decisions
- **기존 구현은 폐기하지 않는다**: Airflow/dbt/Superset/ai_native/eval YAML은 이후 확장의 기반으로 재사용한다.
- **공식 다음 작업은 Phase 2B다**: 기존 “Phase 4 evaluator 구현”은 Phase 5B Text2SQL Agent 구현 시점으로 미룬다.
- **핀테크 연결은 합성 결제 전환 데이터로 만든다**: 실제 결제 데이터가 없으므로, 분포 가정과 한계를 문서화한 시뮬레이션으로 payment conversion/ROAS 분석을 구성한다.

## Files changed
- `CLAUDE.md` — 프로젝트 목표, 현재 Phase, 직전 세션 요약, 참조 문서 우선순위 갱신
- `README.md` — 새 피치, TL;DR, JD 매핑, Phase 진행 상황 갱신
- `docs/adinsight_project_blueprint.md` — 새 피치와 최신 실행 순서 안내 추가
- `docs/adr/003-redesign-ac-strategy.md` — A+C 전략 결정 기록 신규 작성
- `docs/guides/project_redesign_master_guide.md` — Phase P 상태를 완료로 갱신
- `docs/session_log/README.md` — Session 13 인덱스 추가

## Concepts taught (학습 강화)
- **A+C 전략** — 기존 데이터 플랫폼 축은 유지하고, 결제 전환·ML·Agent 축을 추가해 JD 갭을 메우는 재설계 방식.
- **ADR** — 방향 전환처럼 나중에 이유를 설명해야 하는 결정을 별도 문서로 남기는 기록 방식.
- **실측 vs 목표 수치** — README 최종본에는 목표값이 아니라 실제 측정값만 넣어야 한다는 포트폴리오 원칙을 재확인.

## Portfolio assets added
- ADR: `docs/adr/003-redesign-ac-strategy.md`
- 문서 정렬: `CLAUDE.md`, `README.md`, `docs/adinsight_project_blueprint.md`, `docs/guides/project_redesign_master_guide.md`

## Open questions
- Phase 2B에서 daily DAG를 실제 매일 돌릴지, 포트폴리오용 manual run + Airflow schedule 정의까지만 할지 결정 필요
- Phase 2C 합성 데이터 규모를 로컬 안정성 기준으로 116만 행에서 시작할지, 더 작은 smoke profile을 먼저 둘지 결정 필요

## Metrics
- 신규 ADR: 1개
- Phase P 문서 정렬 파일: 5개
- 코드 변경: 없음

## Next session — start here
1. `CLAUDE.md`, `docs/guides/project_redesign_master_guide.md`, `docs/guides/phase2b_apify_daily_pipeline_guide.md`를 읽는다.
2. Phase 2B 범위를 작은 단위로 시작한다.
   - 첫 파일 후보: `dags/common/ig_collect_utils.py`
   - 첫 기능 후보: Airflow Variable 기반 watermark 읽기/쓰기 helper
3. 기존 `dags/dag_ig_collect_round1.py`와 loader 패턴을 재사용해 daily DAG 설계를 만든다.
