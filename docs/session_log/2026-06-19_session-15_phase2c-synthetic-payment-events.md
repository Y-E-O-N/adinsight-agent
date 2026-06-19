# Session 15 — Phase 2C Synthetic Payment Events (2026-06-19)

**Phase**: Phase 2C — 합성 결제 데이터 생성기
**Duration**: ~2h
**Operator**: Yeon (with Codex)

## Goals
- Phase 2B에서 수집한 실제 Apify 게시물 데이터를 기반으로 합성 campaign/payment 데이터를 만든다.
- Apify 공개 수집 데이터에서 제공되지 않는 views/impressions/clicks를 임의로 만들지 않고, 관측 가능한 likes/comments 지표만 사용한다.
- `raw → staging`까지 결제 이벤트 흐름을 dbt 테스트로 검증한다.

## Done
- [x] 실제 Apify raw 데이터의 필드 가용성을 확인했다.
  - `likes_count`, `comments_count`, `source_hashtag`, `owner_username`, `posted_at`은 안정적으로 사용 가능
  - `viewCount`, `viewsCount`, `impressions`는 현재 수집 데이터에서 안정적으로 제공되지 않음
- [x] `apify_profile.py`로 실제 수집 데이터의 engagement percentile profile을 생성했다.
- [x] `generation_profile.py`로 category/region/campaign/payment 정책값을 분리했다.
- [x] `campaigns.py`로 synthetic campaign rows를 생성하고 `raw.syn_campaigns`에 적재했다.
- [x] `post_campaign_attribution.py`로 실제 Apify 게시물에 synthetic campaign attribution을 붙였다.
- [x] `payment_events.py`를 clicks 기반에서 observed engagement 기반으로 재설계했다.
- [x] `raw.syn_payment_events`와 `stg_syn_payment_events`를 추가했다.
- [x] payment event 확장 적재를 500 attribution 기준으로 검증했다.
- [x] 입력 규모가 바뀌어도 기존 attribution의 payment 결과가 흔들리지 않도록 attribution별 deterministic RNG를 적용했다.
- [x] payment event 동기화 로더를 추가해 stale event가 남지 않도록 수정했다.
- [x] 전체 dbt 테스트 `95/95 PASS`를 확인했다.

## Decisions
- **views/impressions/clicks는 만들지 않는다**: 현재 Apify 공개 수집 데이터에서 조회수/노출/클릭이 안정적으로 제공되지 않으므로, 포트폴리오 데이터에서도 임의 생성하지 않는다.
- **결제 이벤트는 observed engagement 기반으로 만든다**: `observed_engagement_count = likes_count_clean + comments_count`, `observed_engagement_tier`를 payment simulation의 핵심 입력으로 사용한다.
- **결제 건수는 Poisson 분포를 사용한다**: attribution 단위 기간 안에서 발생하는 event count로 보고, 기대 결제 건수 `lambda`를 observed engagement, campaign budget, objective, category, paid partnership flag로 계산한다.
- **결제 금액은 Lognormal 분포를 사용한다**: 결제 금액은 0보다 크고 오른쪽 꼬리가 긴 금액 데이터로 가정한다.
- **payment sync는 upsert만으로 충분하지 않다**: Poisson 결과가 0건으로 바뀌면 기존 event가 stale row로 남을 수 있으므로, 입력 attribution 범위의 stale event를 삭제한 뒤 upsert한다.
- **로컬 ↔ AWS 대응**: 로컬 `raw.syn_*` 테이블은 RDS/Aurora raw zone, `dbt staging`은 Glue/dbt transformation layer, generator scripts는 Glue job/Batch job 또는 MWAA task에 대응된다. 현재는 검증 가능성을 위해 로컬 Docker에서 수동 실행한다.

## Files changed
- `data_generation/generators/apify_profile.py` — 실제 Apify raw 데이터 기반 profile JSON 생성
- `data_generation/profiles/apify_profile_latest.json` — observed engagement percentile과 field availability 저장
- `data_generation/generators/generation_profile.py` — category/region/campaign/payment 공통 정책값 분리
- `data_generation/generators/campaigns.py` — synthetic campaign 생성 및 Postgres 적재 CLI
- `data_generation/generators/post_campaign_attribution.py` — 실제 게시물과 synthetic campaign 연결
- `data_generation/generators/payment_events.py` — observed engagement 기반 synthetic payment event 생성
- `data_generation/collectors/loaders/synthetic_loader.py` — campaign/attribution/payment raw upsert 및 payment sync
- `infra/postgres/init/04_synthetic_raw_schema.sql` — `raw.syn_campaigns`, `raw.syn_post_campaign_attributions`, `raw.syn_payment_events`
- `dbt/models/staging/stg_syn_campaigns.sql` — campaign staging model
- `dbt/models/staging/stg_syn_post_campaign_attributions.sql` — post-campaign attribution staging model
- `dbt/models/staging/stg_syn_payment_events.sql` — payment event staging model
- `dbt/models/staging/_sources.yml` — synthetic raw sources/tests 추가
- `dbt/models/staging/schema.yml` — synthetic staging model tests 추가
- `data_generation/README.md` — Phase 2C 합성 데이터 가정과 한계 최신화
- `docs/images/adinsight_execution_data_loading_flow.png` — 실행/적재 흐름도
- `docs/images/adinsight_execution_data_loading_flow_ko_notes.png` — 노드별 한국어 설명 포함 흐름도

## Concepts taught (학습 강화)
- **Synthetic benchmark** — 실제 결제 성과를 주장하는 데이터가 아니라, 분석/모델링 파이프라인을 검증하기 위한 재현 가능한 데이터다.
- **Field availability** — 만들고 싶은 지표가 아니라 실제 수집 가능한 지표를 기준으로 모델 입력을 정해야 한다.
- **Impression vs views** — 광고/인사이트 권한이 없는 공개 수집 데이터에서는 조회수/노출이 안정적으로 제공되지 않을 수 있다.
- **Poisson distribution** — 일정 입력 단위에서 발생하는 결제 event count를 샘플링하는 데 사용했다.
- **Lognormal distribution** — 결제 금액처럼 0보다 크고 오른쪽 꼬리가 긴 값을 샘플링하는 데 사용했다.
- **Idempotency vs sync** — upsert는 중복 방지에는 좋지만, 재생성 결과에서 사라진 row를 삭제하려면 sync/delete 단계가 필요하다.

## Portfolio assets added
- 데이터 흐름 이미지:
  - `docs/images/adinsight_execution_data_loading_flow.png`
  - `docs/images/adinsight_execution_data_loading_flow_ko_notes.png`
- 핵심 스토리:
  - “조회수/클릭을 임의 생성하지 않고, 실제 수집 가능한 likes/comments 기반으로 campaign-to-payment simulation을 설계했다.”
  - “raw 원본 보존, deterministic generation, stale event sync, dbt relationship tests로 재실행 안전성을 검증했다.”

## Open questions
- Phase 2C의 498 payment events는 smoke보다 크지만, redesign guide의 장기 목표인 수만 건 규모에는 아직 작다.
- Phase 3B mart를 만든 뒤, 필요한 분석 밀도에 따라 attribution/payment limit을 1,000~4,000건으로 더 늘릴지 결정한다.
- 장기적으로 실제 광고/creator insights 권한이 생기면 views/impressions/clicks를 별도 observed metric으로 도입할지 재검토한다.

## Metrics
- Apify raw posts: `raw.ig_posts=4126`
- Campaigns: `raw.syn_campaigns=30`
- Post-campaign attributions:
  - 확장 전: `25`
  - 확장 후: `500`
  - 확장 적재: `inserted=475`, `updated=25`
  - tier 분포: `low=215`, `medium=149`, `high=84`, `viral=52`
- Payment events:
  - 동기화 후: `raw.syn_payment_events=498`
  - attributed posts with payments: `211`
  - campaigns with payments: `25`
  - gross payment KRW: `6,644,169.81`
  - net payment KRW: `6,329,923.59`
  - refund events: `14`
  - tier별 gross payment KRW:
    - `low=363,598.19`
    - `medium=980,935.14`
    - `high=1,996,567.12`
    - `viral=3,303,069.36`
- dbt:
  - `dbt run --select stg_syn_campaigns stg_syn_post_campaign_attributions stg_syn_payment_events` → `PASS=3`
  - full `dbt test` → `PASS=95`, `WARN=0`, `ERROR=0`

## Next session — start here
1. Phase 3B dbt 모델 확장을 시작한다.
2. 첫 모델 후보:
   - `intermediate.int_campaign_payment_performance`
   - `marts.mart_campaign_roi_summary`
3. 핵심 계산:
   - campaign별 attributed posts, payment events, gross/net payment, refund count
   - `roas = net_payment_amount_krw / campaign_budget_krw`
   - engagement tier별 payment contribution
4. 검증:
   - `dbt run --select int_campaign_payment_performance mart_campaign_roi_summary`
   - `dbt test --select int_campaign_payment_performance mart_campaign_roi_summary`
