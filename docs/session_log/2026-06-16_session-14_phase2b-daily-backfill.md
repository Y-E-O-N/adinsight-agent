# Session 14 — Phase 2B Daily + Backfill Pipeline (2026-06-16)

**Phase**: Phase 2B — Apify 운영 등급 자동화 파이프라인
**Duration**: ~2h
**Operator**: Yeon (with Codex)

## Goals
- Apify Instagram 수집을 일회성 실행이 아니라 매일 반복 가능한 Airflow DAG로 전환한다.
- 해시태그별 `k`를 고정값이 아니라 직전 실행 결과에 따라 25 단위로 조정한다.
- 수동 보정용 backfill DAG를 만들고, 동일 실행 반복 시 raw 테이블이 중복 폭증하지 않는지 검증한다.

## Done
- [x] `dags/common/ig_collect_utils.py` 작성: watermark, freshness check, daily count/weekly average helper 추가
- [x] `dags/dag_ig_collect_daily.py` 작성 및 Airflow 등록
- [x] daily DAG schedule 설정: `0 21 * * *` UTC, 한국시간 매일 06:00 실행
- [x] 후보 해시태그 30개로 확장
- [x] 해시태그별 adaptive `k` 정책 구현
  - 직전 실행에서 `items_collected >= k_requested`이면 `k + 25`
  - `k_requested - items_collected > 25`이면 `k - 25`
  - 그 외에는 유지
  - 신규 해시태그는 `k=50`
  - 해시태그별 범위는 `1~200`이 아니라 daily 기준 `25~200`
- [x] daily 전체 예산을 `100 * len(CANDIDATE_HASHTAGS)`로 계산하도록 변경
- [x] daily DAG 수동 실행 성공 및 freshness/watermark/metrics 기록 확인
- [x] `dags/dag_ig_backfill.py` 작성 및 Airflow 등록
- [x] backfill DAG를 `schedule=None` 수동 실행 전용으로 구성
- [x] `dag_run.conf`/Params로 `target_date`, `hashtags`, `k`, `reason`을 받도록 구성
- [x] backfill smoke run 성공: `#뷰티`, `k=25`
- [x] 같은 backfill을 2회 실행해 raw upsert/source link 멱등성 확인

## Decisions
- **daily와 backfill은 역할을 분리한다**: daily는 최신 수집과 운영 freshness/watermark를 관리하고, backfill은 실패/누락 보정을 위한 수동 실행 도구로 둔다.
- **adaptive k는 누적 row 수가 아니라 직전 실행 성과를 기준으로 한다**: 꽉 채워 수집되는 seed는 다음 실행에서 25 늘리고, 충분히 못 채우는 seed는 25 줄인다.
- **daily 총량 제한은 해시태그 수에 비례한다**: 현재 `DAILY_K_BUDGET = 100 * len(CANDIDATE_HASHTAGS)`라서 seed 수를 조정해도 평균 예산이 유지된다.
- **현재 backfill의 `target_date`는 메타데이터다**: 현재 `collect_hashtag(hashtag, k)` collector는 날짜 필터를 지원하지 않으므로, `target_date`는 어떤 날짜 보정 실행인지 기록하는 용도로 남긴다.
- **학습/구현 방식은 Guided-Coding으로 복귀한다**: 사용자가 직접 작성하는 흐름을 기본으로 하고, 세션 로그와 문서 정리는 Codex가 직접 작성한다.

## Files changed
- `dags/common/ig_collect_utils.py` — watermark/freshness helper 추가
- `dags/dag_ig_collect_daily.py` — daily collect DAG, adaptive k, freshness, watermark, metrics 기록
- `dags/dag_ig_backfill.py` — 수동 backfill DAG 신규 작성
- `metrics/run_results.jsonl` — daily/backfill 실행 결과 append
- `docs/session_log/2026-06-16_session-14_phase2b-daily-backfill.md` — 본 세션 요약
- `docs/session_log/README.md` — Session 14 인덱스 추가
- `CLAUDE.md` — 현재 Phase와 직전 세션 요약 갱신

## Concepts taught (학습 강화)
- **Airflow pause/unpause** — DAG가 paused면 manual trigger로 run은 생기지만 task가 시작되지 않을 수 있다.
- **Dynamic task mapping** — 해시태그 계획 리스트를 `expand_kwargs()`로 seed별 task instance에 매핑한다.
- **XCom LazyXComAccess** — mapped task 결과는 바로 JSON 직렬화되지 않으므로 `list(seed_metrics)`로 변환 후 기록한다.
- **Idempotent upsert** — `raw.ig_posts`는 `ON CONFLICT (id) DO UPDATE`, `raw.ig_post_sources`는 `ON CONFLICT DO NOTHING`으로 재실행 안전성을 만든다.
- **Backfill** — 자동 스케줄이 아니라 운영자가 의도적으로 실행하는 누락/실패 보정 파이프라인이다.
- **로컬 ↔ AWS 대응** — 로컬 Airflow DAG는 Amazon MWAA/Step Functions, `metrics/run_results.jsonl`은 CloudWatch/S3 audit log, Postgres raw schema는 RDS/Aurora raw zone에 대응한다.

## Portfolio assets added
- 운영형 수집 파이프라인 증거: `ig_collect_daily`, `ig_collect_backfill`
- 실행 메트릭:
  - daily adaptive run: `seed_count=29`, `items_collected_total=1725`, `inserted_total=1410`, `updated_total=315`
  - backfill smoke: `items_collected_total=25`, `inserted_total=18`, `updated_total=7`
  - backfill idempotency: `items_collected_total=25`, `inserted_total=0`, `updated_total=25`
- raw count 검증: `raw.ig_posts=1627`, `last_collected_at=2026-06-16 05:56:44.627509+00`

## Open questions
- Apify Actor가 날짜 필터를 안정적으로 지원하는지 확인하고, 가능하면 `target_date`를 실제 수집 조건으로 승격할지 결정한다.
- daily adaptive k 정책에 `inserted/source_links_inserted` 비율을 추가할지, 당분간 `items_collected` 기준으로만 운영할지 결정한다.
- Phase 2B 완료 처리 전에 며칠간 scheduled run을 관찰해 자동 실행 안정성을 확인할지 결정한다.

## Metrics
- `ig_collect_daily` import 검증: `airflow dags list-import-errors` → `No data found`
- `ig_collect_daily` adaptive run:
  - `seed_count=29`
  - `k_requested_total=1725`
  - `items_collected_total=1725`
  - `inserted_total=1410`
  - `updated_total=315`
  - `source_links_inserted_total=1575`
  - `freshness.status=ok`
  - `watermark=2026-06-16`
- `ig_collect_backfill` import 검증: `airflow dags list-import-errors` → `No data found`
- `ig_collect_backfill` smoke:
  - `k_requested_total=25`
  - `items_collected_total=25`
  - `inserted_total=18`
  - `updated_total=7`
  - `source_links_inserted_total=20`
- `ig_collect_backfill` idempotency rerun:
  - `k_requested_total=25`
  - `items_collected_total=25`
  - `inserted_total=0`
  - `updated_total=25`
  - `source_links_inserted_total=0`

## Next session — start here
1. `ig_collect_daily`의 다음 자동 실행 결과를 확인한다.
   - Airflow UI: `http://localhost:8081` → `ig_collect_daily` Grid
   - CLI: `make airflow-cli cmd='tasks states-for-dag-run ig_collect_daily <RUN_ID>'`
   - Metrics: `tail -n 5 metrics/run_results.jsonl`
2. 자동 실행 결과에서 adaptive k가 의도대로 바뀌었는지 확인한다.
   - 꽉 찬 seed는 `+25`
   - `k`보다 25 초과로 덜 수집된 seed는 `-25`
   - 총합은 `100 * 해시태그 수` 이하
3. Phase 2B 완료 조건을 점검한다.
   - daily DAG 자동 실행 성공
   - freshness/watermark 정상
   - backfill smoke + idempotency 검증 완료
4. 다음 구현 후보는 Phase 2C 합성 결제 데이터 생성기다.
