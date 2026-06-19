# Session 09 — Phase 3 dbt Staging + First Intermediate (2026-06-05)

**Phase**: Phase 3 — dbt staging / intermediate 시작
**Duration**: ~1h
**Operator**: Yeon (with Codex)

## Goals
- Round 1 수집 결과를 raw 데이터 프로파일링으로 해석한다.
- raw → staging 변환 컬럼을 학습하고 실제 dbt 모델로 만든다.
- 첫 intermediate 모델을 만들어 staging과 intermediate의 역할 차이를 이해한다.
- 새 세션에서 바로 이어갈 수 있게 다음 모델링 후보를 남긴다.

## Done
- [x] `docs/analysis/stage2_round1_raw_profile.md` 작성
- [x] `staging.stg_ig_posts` dbt view 작성
- [x] raw source YAML과 staging schema YAML 작성
- [x] `dbt-core~=1.8.0`, `dbt-postgres~=1.8.0` Airflow 이미지 의존성 추가
- [x] Airflow worker 이미지 재빌드 후 `dbt-core 1.8.8`, `dbt-postgres 1.8.2` 확인
- [x] `staging.stg_ig_posts` dbt run/test 통과
- [x] `docs/analysis/stage3_stg_ig_posts_design.md` 작성
- [x] `intermediate.int_ig_post_source_quality` dbt view 작성
- [x] `intermediate.int_ig_post_source_quality` dbt run/test 통과
- [x] `docs/analysis/stage3_int_ig_post_source_quality_design.md` 작성

## Decisions
- **raw는 그대로 두고 staging에서 clean/flag 컬럼을 만든다**: `likes_count=-1`은 raw에서 보존하고, staging에서 `likes_hidden`, `likes_count_clean`으로 분리한다.
- **광고/협찬은 확정값이 아니라 후보값으로 둔다**: 키워드 기반 규칙은 오탐 가능성이 있어 `is_sponsored_candidate`로 이름 붙인다.
- **intermediate 첫 모델은 seed 품질 요약으로 선택**: 현재 데이터가 작기 때문에 marts로 바로 가지 않고, source별 품질 판단 모델을 먼저 만든다.
- **현재 추가 수집은 보류**: 당장 자료 수집이 목표가 아니므로, 49건으로 모델링/개념 학습을 우선한다.

## Files changed
- `dbt/dbt_project.yml` — dbt 프로젝트 설정, staging/intermediate schema 설정
- `dbt/macros/generate_schema_name.sql` — custom schema 이름을 그대로 쓰기 위한 macro
- `dbt/models/staging/_sources.yml` — raw source 선언과 source data tests
- `dbt/models/staging/schema.yml` — `stg_ig_posts` 컬럼 설명과 data tests
- `dbt/models/staging/stg_ig_posts.sql` — Instagram 게시물 staging view
- `dbt/models/intermediate/schema.yml` — intermediate 모델 설명과 data tests
- `dbt/models/intermediate/int_ig_post_source_quality.sql` — seed별 수집 품질 요약 view
- `dbt/profiles.example.yml` — dbt profile 예시
- `infra/airflow/requirements.txt` — dbt 의존성 추가
- `.gitignore` — `dbt/.user.yml` ignore 추가
- `docs/analysis/stage2_round1_raw_profile.md` — Round 1 raw profile
- `docs/analysis/stage3_stg_ig_posts_design.md` — staging 모델 설계 노트
- `docs/analysis/stage3_int_ig_post_source_quality_design.md` — intermediate 모델 설계 노트
- `CLAUDE.md`, `docs/session_log/README.md` — 현재 상태와 인덱스 갱신

## Concepts taught
- **데이터 프로파일링**: raw row count, source 분포, null/hidden likes/광고 키워드/작성자 반복을 SQL로 확인한다.
- **raw vs staging**: raw는 원본 보존, staging은 분석 가능한 이름/flag/clean 컬럼 제공.
- **dbt source**: raw 테이블을 dbt lineage와 test 대상으로 선언한다.
- **dbt model**: SELECT 파일 하나가 warehouse view/table 하나가 된다.
- **dbt data tests**: `not_null`, `unique`, `relationships`로 모델 계약을 검증한다.
- **`COUNT(*) FILTER`**: 조건부 count를 만드는 PostgreSQL 집계 패턴.
- **`CASE WHEN`**: sentinel value를 분석용 clean 값으로 바꾸는 SQL if문.
- **`unnest()`**: 배열 컬럼을 row로 펼쳐 seed별 집계를 가능하게 한다.
- **staging vs intermediate**: staging은 row-level 정제, intermediate는 반복 가능한 분석 계산 단위.

## Portfolio assets added
- `staging.stg_ig_posts` dbt view + 15개 data tests 통과
- `intermediate.int_ig_post_source_quality` dbt view + 9개 data tests 통과
- 전체 dbt tests 24/24 통과
- Round 1 데이터 충분성 리스크를 seed별 품질 모델로 구조화

## Metrics
- raw 기준: `raw.ig_posts=49`, `raw.ig_post_sources=49`
- staging 기준: `staging.stg_ig_posts=49`
- intermediate 기준: `intermediate.int_ig_post_source_quality=3`
- staging profile:
  - `likes_hidden=16`
  - `is_sponsored_candidate=21`
  - `caption_is_empty=2`
  - `missing_source=0`
- source quality:
  - `#다이소화장품`: `posts=30`, `hidden_likes_rate=0.4000`, `sponsored_candidate_rate=0.5667`, `useful_for_sponsored_analysis=true`
  - `#뷰티`: `posts=18`, `hidden_likes_rate=0.2222`, `sponsored_candidate_rate=0.2222`, `useful_for_sponsored_analysis=false`
  - `#올리브영`: `posts=1`, `useful_for_sponsored_analysis=false`
- dbt:
  - `dbt run --select stg_ig_posts`: pass
  - `dbt test --select stg_ig_posts source:raw`: 15/15 pass
  - `dbt run --select int_ig_post_source_quality`: pass
  - `dbt test --select int_ig_post_source_quality`: 9/9 pass
  - `dbt test`: 24/24 pass

## Open questions
- `int_ig_sponsored_candidates`를 먼저 만들지, `int_ig_owner_activity`를 먼저 만들지 결정 필요
- `is_sponsored_candidate` 키워드 규칙을 언제 확장할지 결정 필요
- `has_minimum_sample` 기준 `posts >= 20`은 학습용 임시 기준. 데이터가 늘어나면 재조정 필요
- 추가 수집을 재개할 때 Apify Actor 옵션을 먼저 볼지, seed smoke 확장을 먼저 할지 결정 필요

## Next session — start here
1. 먼저 현재 상태를 확인한다.
   ```bash
   docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt test --profiles-dir /opt/dbt"
   docker compose exec postgres psql -U postgres -d adinsight -c "SELECT * FROM intermediate.int_ig_post_source_quality ORDER BY posts DESC;"
   ```
2. 아래 문서를 순서대로 읽는다.
   - `docs/analysis/stage3_stg_ig_posts_design.md`
   - `docs/analysis/stage3_int_ig_post_source_quality_design.md`
3. 다음 모델 하나를 선택한다.
   - 추천 A: `int_ig_sponsored_candidates` — 광고/협찬 후보 게시물만 분리해서 caption/owner/source를 분석
   - 추천 B: `int_ig_owner_activity` — 작성자별 게시물 수, hidden likes 비율, sponsored 후보 비율 집계
4. 학습 방식은 계속 Yeon이 먼저 개념을 설명해보고, Codex가 교정/보완하는 방식으로 진행한다.
