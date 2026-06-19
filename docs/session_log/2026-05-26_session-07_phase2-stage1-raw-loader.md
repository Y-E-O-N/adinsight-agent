# Session 07 — Phase 2 Stage 1 Raw Loader (2026-05-26)

**Phase**: Phase 2 — 데이터 수집 (Stage 1: raw Postgres loading)
**Duration**: ~2h
**Operator**: Yeon (with Codex)

## Goals
- `raw.ig_posts` 테이블을 설계하고 Apify 응답 원본을 보존한다.
- 같은 게시물이 여러 해시태그에서 발견되는 source lineage를 보존한다.
- Airflow DAG에서 `collect -> load -> Postgres` 흐름을 끝까지 검증한다.
- 같은 입력을 5회 실행해 멱등성을 확인한다.

## Done
- [x] `raw.ig_posts`에서 게시물 엔티티와 `raw_payload JSONB`를 보존하도록 DDL 작성
- [x] `raw.ig_post_sources` 테이블을 추가해 `(post_id, source_hashtag)` lineage 분리
- [x] `postgres_loader.py`에서 `raw.ig_posts` upsert와 `raw.ig_post_sources` `DO NOTHING` insert 분리
- [x] Airflow worker에 `POSTGRES_*` 환경변수 주입
- [x] Airflow 이미지에 `psycopg[binary]` 반영 후 import 검증
- [x] `ig_collect_smoke` DAG를 TaskFlow `collect_one_hashtag -> load_posts` 구조로 확장
- [x] DAG paused 상태, APIFY_TOKEN 인증 오류, XCom 반환값 오류를 디버깅
- [x] `#다이소화장품` 20건 기준 DAG 5회 success 및 row count 유지 검증

## Decisions
- **게시물과 수집 경로를 테이블 분리**: `raw.ig_posts`는 게시물 원본, `raw.ig_post_sources`는 어느 해시태그에서 발견됐는지 저장한다. Why: 같은 게시물이 여러 seed에서 발견될 때 `source_hashtag`가 덮어써지는 것을 막기 위해.
- **source lineage는 `ON CONFLICT DO NOTHING`**: 같은 `(post_id, source_hashtag)`는 중복 저장하지 않는다. Why: 재실행 안전성과 lineage 중복 방지를 동시에 만족한다.
- **Stage 1 smoke는 XCom으로 items 전달**: 20건 규모에서는 학습과 디버깅이 쉽다. Why: task 간 데이터 전달을 명확히 볼 수 있다. 단, Stage 2 본수집에서는 큰 payload를 XCom으로 넘기지 않는다.

## Files changed
- `infra/postgres/init/03_raw_schema.sql` — `raw.ig_posts`, `raw.ig_post_sources`, BRIN/B-tree 인덱스 정의
- `data_generation/collectors/loaders/postgres_loader.py` — psycopg 기반 raw upsert loader
- `dags/dag_ig_collect_smoke.py` — collect task와 load task 연결
- `docker-compose.yml` — Airflow 공통 환경변수에 `POSTGRES_*` 추가
- `infra/airflow/requirements.txt` — Airflow 이미지에 `psycopg[binary]` 추가
- `metrics/run_results.jsonl` — Stage 1 idempotency 검증 메트릭 append
- `docs/portfolio_draft.md` — Phase 2 Stage 1 결과 반영
- `docs/learning/session-07_concepts.md` — 이번 세션 학습 개념 정리
- `CLAUDE.md`, `docs/session_log/README.md` — 현재 Phase와 세션 인덱스 갱신

## Concepts taught (학습 강화)
- **L0 raw layer** — 외부 API 응답을 변환하지 않고 원본 보존하는 계층. 로컬 Postgres raw schema는 AWS 기준 S3 lake + Glue Catalog에 가까운 역할.
- **JSONB 원본 보존** — 자주 쓰는 컬럼은 평면화하되 전체 API 응답은 `raw_payload`에 저장해 재처리 가능성을 남긴다.
- **Upsert** — `INSERT ... ON CONFLICT DO UPDATE`로 insert와 update를 한 SQL 패턴에 묶어 멱등 적재를 구현한다.
- **Source lineage** — 데이터가 어느 seed/경로로 수집됐는지 별도 테이블에 남겨 분석과 디버깅 근거로 사용한다.
- **XCom** — Airflow task 간 작은 반환값을 metadata DB로 전달하는 메커니즘. smoke에는 적합하지만 대량 payload에는 부적합하다.
- **Airflow 디버깅** — paused DAG, task log, `upstream_failed`, 외부 API 인증 실패를 구분했다.

## Portfolio assets added
- 메트릭: `metrics/run_results.jsonl` 에 `stage1_raw_loader_idempotency` append
- 작업장 갱신: `docs/portfolio_draft.md` Phase 2에 Stage 1 raw loader와 멱등성 수치 반영
- 학습 노트: `docs/learning/session-07_concepts.md`

## Open questions
- Stage 2 본수집에서 XCom 대신 어떤 적재 패턴을 쓸지 결정 필요: task 내부 collect-and-load vs 임시 landing 파일 vs raw landing table
- `#뷰티`, `#올리브영`, `#다이소화장품` 본수집을 한 DAG에서 dynamic task mapping으로 나눌지, 명시 task 3개로 둘지 결정 필요
- Apify 비용과 actor run metadata를 loader metrics에 같이 남길지 결정 필요

## Metrics
- DAG success: 5회
- 첫 실행: `inserted=20`, `updated=0`, `source_links_inserted=20`, `total=20`
- 반복 실행 4회: 매회 `inserted=0`, `updated=20`, `source_links_inserted=0`, `total=20`
- 최종 row count: `raw.ig_posts=20`, `raw.ig_post_sources=20`
- 실패 후 해결: APIFY_TOKEN 인증 오류 1회, DAG paused 상태 1회, Airflow worker env/import 문제 2건

## Next session — start here
1. Stage 2 본수집 설계: XCom을 쓰지 않는 수집+적재 패턴 선택
2. Round 1 seed 3개 실행 계획 확정: `#뷰티` K=600 / `#올리브영` K=1000 / `#다이소화장품` K=400
3. 본수집 전 Apify 비용 상한과 actor run metadata 기록 방식 정하기
4. 본수집 DAG를 만들고 `raw.ig_posts`, `raw.ig_post_sources` row count와 국가/계정 분포를 포트폴리오 메트릭으로 남기기
