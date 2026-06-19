# Session 16 — Phase 3B Campaign ROI Handoff (2026-06-19)

**Phase**: Phase 3B — campaign/payment dbt 모델 확장
**Duration**: ~45m
**Operator**: Yeon (with Codex)

## Goals
- Phase 2C에서 생성한 campaign/payment 데이터를 분석 가능한 campaign ROI mart로 올린다.
- 현재 작업 상태를 새 Codex 세션에서 바로 이어갈 수 있게 문서화한다.
- 커밋과 GitHub push까지 완료해 원격 기준점을 고정한다.

## Done
- [x] Phase 2C 데이터를 smoke보다 큰 규모로 확장했다.
  - `raw.syn_post_campaign_attributions=500`
  - `raw.syn_payment_events=498`
- [x] `payment_events.py`의 재실행 안전성을 보강했다.
  - attribution별 deterministic RNG 적용
  - 입력 attribution 범위 기준 stale payment event sync/delete 추가
- [x] Phase 3B 첫 intermediate 모델을 추가했다.
  - `intermediate.int_campaign_payment_performance`
- [x] Phase 3B 첫 mart 모델을 추가했다.
  - `marts.mart_campaign_roi_summary`
- [x] 새 mart의 schema tests를 추가했다.
- [x] 전체 dbt 기준선을 `11 models / 124 tests`로 갱신했다.
- [x] 실행 및 데이터 적재 흐름도 PNG/SVG를 `docs/images/`에 저장했다.
- [x] 커밋 및 push 완료.
  - Commit: `f1b291f Add campaign payment analytics pipeline`
  - Remote: `origin/main`

## Decisions
- **다음 분석 grain은 campaign_id다**: Phase 3B 첫 mart는 campaign별 attributed posts, payment events, gross/net payment, refund, ROAS를 계산한다.
- **ROAS는 synthetic benchmark 지표다**: 실제 광고 성과 주장이 아니라, campaign-to-payment 분석 파이프라인 검증용이다.
- **현재 ROAS는 보수적으로 낮아도 괜찮다**: max ROAS가 `0.5969`이므로 1x 이상 campaign은 아직 없다. 이는 모델/데이터 캘리브레이션 전 synthetic smoke의 결과로 본다.
- **다음 확장은 ai_native 또는 ML feature layer다**: mart가 생겼으므로 Text2SQL/BI 친화 모델 또는 ROAS 예측 feature store로 이어갈 수 있다.

## Files changed
- `data_generation/generators/payment_events.py` — attribution별 deterministic RNG, observed engagement 기반 payment event 생성
- `data_generation/collectors/loaders/synthetic_loader.py` — payment event sync/delete 추가
- `dbt/models/intermediate/int_campaign_payment_performance.sql` — campaign grain payment performance intermediate
- `dbt/models/intermediate/schema.yml` — intermediate model tests 추가
- `dbt/models/marts/campaign/mart_campaign_roi_summary.sql` — campaign ROI mart
- `dbt/models/marts/campaign/schema.yml` — campaign ROI mart tests
- `CLAUDE.md` — 현재 Phase와 다음 시작점 갱신
- `docs/session_log/README.md` — Session 16 index 추가
- `docs/session_log/2026-06-19_session-16_phase3b-campaign-roi-handoff.md` — 본 핸드오프 로그

## Concepts taught (학습 강화)
- **mart grain** — `mart_campaign_roi_summary`는 `campaign_id` 1행이 grain이다.
- **ROAS** — `net_payment_amount_krw / campaign_budget_krw`로 계산한 광고비 대비 결제 성과 지표다.
- **stale event sync** — Poisson 재생성 결과에서 사라진 event row를 삭제하지 않으면 멱등성이 깨질 수 있다.
- **handoff checkpoint** — 새 세션이 바로 이어갈 수 있게 현재 DB row count, dbt 기준선, commit SHA, 다음 명령을 문서에 남긴다.

## Portfolio assets added
- 실행/적재 흐름도:
  - `docs/images/adinsight_execution_data_loading_flow.png`
  - `docs/images/adinsight_execution_data_loading_flow_ko_notes.png`
- Campaign ROI mart:
  - `marts.mart_campaign_roi_summary`
- GitHub checkpoint:
  - `f1b291f Add campaign payment analytics pipeline`

## Open questions
- `mart_campaign_roi_summary`를 `ai_native.ai_campaign_roi_summary`로 자연어 친화 컬럼/metadata와 함께 확장할지 결정한다.
- Superset에서 campaign ROI dashboard를 만들고 screenshot/export를 추가할지 결정한다.
- ROAS 예측 ML feature store를 먼저 만들지, Text2SQL semantic mart를 먼저 만들지 결정한다.
- 현재 synthetic payment 규모 498건으로 충분한지, 1,000~4,000 attribution 범위로 더 확장할지 결정한다.

## Metrics
- Raw:
  - `raw.ig_posts=4126`
  - `raw.syn_campaigns=30`
  - `raw.syn_post_campaign_attributions=500`
  - `raw.syn_payment_events=498`
- Payment:
  - attributed posts with payments: `211`
  - campaigns with payments: `25`
  - gross payment KRW: `6,644,169.81`
  - net payment KRW: `6,329,923.59`
  - refund events: `14`
- Campaign ROI mart:
  - rows: `30`
  - payment events: `498`
  - gross payment KRW: `6,644,169.81`
  - net payment KRW: `6,329,923.59`
  - max ROAS: `0.5969`
  - ROAS tier distribution: `negative_net=1`, `no_payment=5`, `under_1x=24`
- dbt:
  - `dbt run --select int_campaign_payment_performance mart_campaign_roi_summary` → `PASS=2`
  - `dbt test --select int_campaign_payment_performance mart_campaign_roi_summary` → `PASS=29`
  - full `dbt test` → `PASS=124`, `WARN=0`, `ERROR=0`
- Git:
  - branch: `main`
  - commit: `f1b291f8bd7dcfc8487c0c0b7de2bb01f10096e5`
  - push: `origin/main`

## Next session — start here
1. 시작 확인:
   ```bash
   git status --short
   git log --oneline -3
   docker compose ps
   ```
2. dbt 기준선 재검증:
   ```bash
   docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt test"
   ```
3. 다음 구현 후보 A — AI-native campaign ROI mart:
   - 파일 후보: `dbt/models/ai_native/ai_campaign_roi_summary.sql`
   - 목적: Text2SQL이 이해하기 쉬운 campaign/payment semantic layer 작성
   - 참고: `dbt/models/ai_native/ai_creator_sponsored_summary.sql`
4. 다음 구현 후보 B — Superset ROI dashboard:
   - dataset: `marts.mart_campaign_roi_summary`
   - chart 후보: campaign ROI table, ROAS tier bar, gross/net payment by objective
   - 자산 저장: `docs/images/`, `dashboards/superset_exports/`
5. 다음 구현 후보 C — ML feature layer:
   - campaign/category/objective/budget/engagement/payment summary를 ROAS prediction feature로 정리
   - 후속 LightGBM baseline의 입력으로 사용
