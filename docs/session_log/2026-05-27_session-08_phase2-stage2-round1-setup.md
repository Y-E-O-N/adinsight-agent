# Session 08 — Phase 2 Stage 2 Round 1 Setup + First Run (2026-05-27)

**Phase**: Phase 2 — 데이터 수집 (Stage 2: Round 1 본수집 실행)
**Duration**: ~45m
**Operator**: Yeon (with Codex)

## Goals
- Stage 2 본수집 DAG 구조를 설계한다.
- Stage 1 smoke에서 사용한 XCom payload 전달 방식을 본수집에 맞게 바꾼다.
- 새 세션에서 바로 본수집 실행 전 체크부터 이어갈 수 있게 상태를 남긴다.
- 실행 전 체크가 통과하면 `ig_collect_round1`을 실제로 trigger하고 결과를 기록한다.

## Done
- [x] `dags/dag_ig_collect_round1.py` 신규 작성
- [x] Round 1 seed 3개를 상수로 정의: `뷰티` K=600, `올리브영` K=1000, `다이소화장품` K=400
- [x] task 내부에서 `collect_hashtag()` 후 즉시 `upsert_posts()`를 호출하는 collect-and-load 구조 작성
- [x] XCom에는 원본 게시물 list가 아니라 작은 metrics dict만 반환하도록 설계
- [x] `k`와 `load_metrics`의 의미를 학습
- [x] 로컬 문법 검사 통과: `uv run python -m py_compile dags/dag_ig_collect_round1.py`
- [x] Airflow 컨테이너 문법 검사 통과: `python -m py_compile /opt/airflow/dags/dag_ig_collect_round1.py`
- [x] Airflow DAG 등록 확인: `ig_collect_round1`, initially paused
- [x] `record_round1_metrics` task 추가: seed별 작은 metrics dict를 모아 `metrics/run_results.jsonl`에 자동 append
- [x] `ig_collect_round1` unpause + manual trigger 실행
- [x] DAG run success 확인: `manual__2026-05-27T07:52:48+00:00`
- [x] 최종 raw row count 확인: `raw.ig_posts=49`, `raw.ig_post_sources=49`

## Decisions
- **Stage 2는 XCom으로 items를 넘기지 않음**: seed별 task 안에서 collect와 load를 같이 수행한다. Why: 2,000건 원본 payload를 Airflow metadata DB에 저장하지 않기 위해.
- **seed별 task로 분리**: 해시태그별 수집량과 실패 지점을 분리해서 본다. Why: 한 seed의 실패가 전체 원인 분석을 흐리지 않게 하기 위해.
- **학습용 주석 유지**: DAG 파일 안의 설명 주석은 Yeon의 학습 흐름을 위해 당장은 유지한다. Why: 다음 세션에서 코드 의도를 빠르게 복구하기 위해.
- **지금 당장의 목표는 추가 수집이 아니라 실행 결과 기록**: Round 1은 파이프라인 검증 관점에서는 성공했지만, 요청량 대비 반환량이 낮아 seed/Actor 전략은 별도 후속 과제로 분리한다.

## Files changed
- `dags/dag_ig_collect_round1.py` — Stage 2 Round 1 본수집 DAG + metrics recorder task
- `CLAUDE.md` — 현재 Phase를 Stage 2 Round 1 실행 결과 정리 중으로 갱신
- `docs/session_log/README.md` — Session 08 인덱스 추가
- `docs/learning/README.md` — Session 08 학습 노트 인덱스 추가
- `docs/learning/session-08_concepts.md` — 이번 세션 학습 개념 정리
- `metrics/run_results.jsonl` — Round 1 실행 결과 append
- `docs/analysis/stage2_round1_raw_profile.md` — Round 1 raw 데이터 프로파일링 문서
- `dbt/dbt_project.yml` — Phase 3 dbt 프로젝트 최소 설정
- `dbt/models/staging/stg_ig_posts.sql` — Instagram raw 게시물 staging view
- `dbt/models/staging/_sources.yml` / `schema.yml` — raw source와 staging 모델 description/data tests
- `dbt/macros/generate_schema_name.sql` — dbt custom schema 이름을 `staging` 그대로 만들기 위한 macro
- `infra/airflow/requirements.txt` — `dbt-core~=1.8.0`, `dbt-postgres~=1.8.0` 추가
- `docs/analysis/stage3_stg_ig_posts_design.md` — staging 모델 설계/학습 문서
- `dbt/models/intermediate/int_ig_post_source_quality.sql` — seed별 수집 품질 intermediate view
- `dbt/models/intermediate/schema.yml` — intermediate 모델 description/data tests
- `docs/analysis/stage3_int_ig_post_source_quality_design.md` — intermediate 모델 설계/학습 문서

## Concepts taught (학습 강화)
- **`k`** — Apify `resultsLimit`에 대응되는 요청 게시물 수. 실제 수집 수(`items_collected`)와 다를 수 있다.
- **`load_metrics`** — `upsert_posts()`가 반환하는 적재 결과 요약. `inserted`, `updated`, `source_links_inserted`, `total`을 포함한다.
- **dict unpacking (`**load_metrics`)** — loader 결과 dict를 최종 metrics dict에 펼쳐 넣는 Python 문법.
- **XCom payload 회피** — 본수집에서는 큰 list/dict payload 대신 작은 metrics dict만 XCom에 남긴다.
- **데이터 프로파일링** — raw row count, source 분포, null/hidden likes/광고 키워드/작성자 반복을 SQL로 확인해 다음 의사결정 근거를 만든다.
- **raw → staging 변환** — 원본 값은 보존하고, 분석용 clean 컬럼과 boolean flag를 별도로 만든다.
- **dbt source/ref/test/docs 출발점** — raw table을 source로 선언하고, staging model에 description과 data tests를 붙인다.
- **staging → intermediate 변환** — staging의 row-level clean 컬럼을 재사용해 seed별 품질 요약처럼 반복 가능한 계산 단위를 만든다.
- **`unnest()`** — 배열 컬럼(`source_hashtags`)을 seed별 row로 펼쳐 집계할 때 사용한다.

## Portfolio assets added
- `metrics/run_results.jsonl`에 `stage2_round1_collect` 실행 결과 1건 추가
- 포트폴리오용 운영 메시지: **DAG/Airflow/Postgres/idempotent loader는 성공, Apify 반환량은 기대보다 낮아 데이터 충분성은 별도 이슈로 분리**
- `docs/analysis/stage2_round1_raw_profile.md`에 SQL 기반 raw profile 작성
- `staging.stg_ig_posts` dbt view 생성 및 15개 data test 통과
- `intermediate.int_ig_post_source_quality` dbt view 생성 및 9개 data test 통과

## Open questions
- Apify `instagram-hashtag-scraper`가 `resultsLimit` 대비 적은 결과만 반환한 이유 확인 필요
- seed 3개만으로 충분한 데이터셋을 만들 수 없으므로, 후속 작업에서 seed 확장 또는 Actor 입력 옵션 점검 필요
- 지금 당장은 추가 자료 수집보다 실행 결과 정리와 다음 판단 근거 축적을 우선한다.

## Metrics
- 본수집 요청량: 2,000 posts
  - `#뷰티`: 600
  - `#올리브영`: 1,000
  - `#다이소화장품`: 400
- 실행 전 row count: `raw.ig_posts=20`, `raw.ig_post_sources=20`
- 실행 후 row count: `raw.ig_posts=49`, `raw.ig_post_sources=49`
- 실제 수집/적재 결과:
  - total: `items_collected=49`, `inserted=29`, `updated=20`, `source_links_inserted=29`
  - `#뷰티`: requested 600 → collected 18 → inserted 18
  - `#올리브영`: requested 1,000 → collected 1 → inserted 1
  - `#다이소화장품`: requested 400 → collected 30 → inserted 10, updated 20
- 로컬 문법 검사: pass
- 컨테이너 문법 검사: pass
- Airflow import errors: none
- DAG run: success (`manual__2026-05-27T07:52:48+00:00`)
- dbt run: pass (`staging.stg_ig_posts`, 49 rows)
- dbt test: pass (15/15)
- staging profile: `likes_hidden=16`, `is_sponsored_candidate=21`, `caption_is_empty=2`, `missing_source=0`
- intermediate dbt run: pass (`intermediate.int_ig_post_source_quality`, 3 rows)
- intermediate dbt test: pass (9/9)
- source quality:
  - `#다이소화장품`: `posts=30`, `hidden_likes_rate=0.4000`, `sponsored_candidate_rate=0.5667`, `useful_for_sponsored_analysis=true`
  - `#뷰티`: `posts=18`, `hidden_likes_rate=0.2222`, `sponsored_candidate_rate=0.2222`, `useful_for_sponsored_analysis=false`
  - `#올리브영`: `posts=1`, `useful_for_sponsored_analysis=false`

## Next session — start here
1. Round 1은 실행 성공으로 간주한다. 다음 기준 row count는 `raw.ig_posts=49`, `raw.ig_post_sources=49`.
2. `staging.stg_ig_posts`는 dbt run/test 통과 상태다. 다음 기준 row count는 49.
3. 당장 추가 수집하지 않는다. 먼저 `docs/analysis/stage3_stg_ig_posts_design.md`를 읽고 staging 컬럼 의미를 복습한다.
4. `intermediate.int_ig_post_source_quality`는 dbt run/test 통과 상태다. 다음에는 아래 둘 중 하나를 고른다.
   - `int_ig_sponsored_candidates`: 광고/협찬 후보 게시물 분리
   - `int_ig_owner_activity`: 작성자별 활동/품질 요약
5. 후속 수집을 재개할 때는 아래 둘 중 하나를 먼저 결정한다.
   - Apify Actor 입력 옵션/제한을 확인한다.
   - seed 후보를 넓혀 작은 `k=20` smoke로 반환량 좋은 hashtag를 선별한다.
