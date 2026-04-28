# Session 05 — Phase 2 Stage 0: Apify Smoke + Airflow DAG (2026-04-28)

**Phase**: Phase 2 — 데이터 수집 (Stage 0: smoke)
**Duration**: ~3h
**Operator**: Yeon (with Claude Code)

## Goals
- 데이터 소싱 전략 결정 (실데이터 + 합성 하이브리드)
- 시드 해시태그 3개 + 수집 알고리즘 (스노우볼 1-hop) 합의
- Apify 가입·결제·토큰 셋업
- Stage 0 smoke: 로컬 + Airflow DAG 양쪽에서 1회 수집 검증
- 응답 스키마·발견 이슈 문서화

## Done
- [x] 지난 세션 (Session 04 후 04-23~04-27 비공식 대화) 의 데이터 전략 토론 정리
- [x] 데이터 소싱 결정: **Apify (실수집)** + **SDV (합성 확장)** 하이브리드
- [x] Round 1 시드 3개 합의: `#뷰티` (광역) / `#올리브영` (브랜드) / `#다이소화장품` (니치)
- [x] 볼륨 기반 K 추정 (옵션 X 권장: 600 / 1000 / 400 ≈ 2,000 posts ≈ $4.6)
- [x] 스노우볼 확장 알고리즘 (1-hop, 빈도/블랙리스트/카테고리 3종 필터, 사람 confirm 단계 포함)
- [x] Apify Personal $29 구독 + APIFY_TOKEN `.env` 등록
- [x] **시크릿 운용 로드맵** 적립 — env_file → Variable → Connection 단계별 마이그 (포트폴리오 메모리)
- [x] `apify-client` 의존성 추가 (`uv add`)
- [x] **Stage 0 코드 (가이드 모드, Yeon 직접 타이핑)**
  - [x] `data_generation/__init__.py`, `data_generation/collectors/__init__.py` (빈 패키지 마커)
  - [x] `data_generation/collectors/apify_hashtag.py` — `collect_hashtag(hashtag, k)` 순수 함수
  - [x] `data_generation/collectors/__main__.py` — argparse 로컬 진입점
  - [x] `dags/dag_ig_collect_smoke.py` — TaskFlow API @dag/@task 1개
- [x] `infra/airflow/requirements.txt` — `apify-client` 추가
- [x] `docker-compose.yml` — `APIFY_TOKEN: ${APIFY_TOKEN}`, `PYTHONPATH: /opt/airflow`, `./data_generation` 볼륨 마운트
- [x] Airflow 이미지 재빌드 + 컨테이너 재기동
- [x] **로컬 smoke 성공**: `python -m data_generation.collectors --hashtag 다이소화장품 --k 20` → 20건
- [x] **Airflow DAG smoke 성공**: 3차 trigger 중 2/3 success (1차 PYTHONPATH 미설정으로 fail → 수정 후 성공)
- [x] 응답 스키마 샘플 저장: `docs/notes/instagram_post_schema_sample.json` (필드 인벤토리 + 후처리 규칙)
- [x] 메트릭 2건 append: `metrics/run_results.jsonl` (로컬 smoke + DAG smoke)

## Decisions
- **데이터 소싱: Apify + SDV 하이브리드** — Apify 로 한국 마이크로 인플루언서 ER·카테고리 분포 학습, 합성으로 캠페인·결제 (비공개) 확장. Why: Apify 단독은 광고비·ROAS 데이터 못 얻음, SDV 단독은 한국 도메인 어휘 없음.
- **Round 1 시드 3개 (3 layer 다양성)**: `#뷰티` (광역) / `#올리브영` (브랜드, 핵심) / `#다이소화장품` (니치, 한국 특유). Why: layer 분포가 면접에서 *"왜 이 시드?"* 답변 차별화.
- **K 차등**: #뷰티 K=600 (노이즈 多, 적게) / #올리브영 K=1000 (핵심) / #다이소화장품 K=400 (가용 최대). Why: 시간 윈도·표본비율·풀 크기 균형.
- **스노우볼 1-hop 만 허용** + 빈도≥1% + 블랙리스트 + LLM 카테고리 분류 + 사람 confirm 1회. Why: 2-hop 부터 주제 드리프트 폭주.
- **Airflow 처음부터 도입** + 함수/DAG 하이브리드 구조 (collect_hashtag 함수 = 로컬·DAG 양쪽 재사용). Why: 버릴 smoke 코드 없음 + 디버깅 사이클 짧게 유지.
- **시크릿 옵션 A (docker-compose env_file) 시작** + Phase 5/8 에서 Variable / Connection 으로 마이그. Why: 단순성부터 시작 + 단계별 trade-off 포트폴리오 자산화.
- **`PYTHONPATH=/opt/airflow`** 로 사용자 패키지 import 경로 확보 (dags/ 폴더 오염 안 시킴). Why: dags/ 는 DAG 전용 관례 준수.

## Files changed
- `pyproject.toml`, `uv.lock` — `apify-client==2.5.0` 추가
- `data_generation/__init__.py` — 패키지 마커 (신규, 빈 파일)
- `data_generation/collectors/__init__.py` — 패키지 마커 (신규, 빈 파일)
- `data_generation/collectors/apify_hashtag.py` — `collect_hashtag()` 함수 (신규, ≈40줄)
- `data_generation/collectors/__main__.py` — 로컬 진입점 (신규, ≈50줄)
- `dags/dag_ig_collect_smoke.py` — TaskFlow API smoke DAG (신규, ≈55줄)
- `infra/airflow/requirements.txt` — `apify-client` 한 줄 추가
- `docker-compose.yml` — `environment` 에 `APIFY_TOKEN`, `PYTHONPATH` 추가 / `volumes` 에 `./data_generation:/opt/airflow/data_generation` 마운트 추가
- `docs/notes/instagram_post_schema_sample.json` — 응답 1건 + 필드 인벤토리 + 후처리 규칙 (신규)
- `metrics/run_results.jsonl` — Stage 0 로컬·DAG smoke 2건 append
- `docs/session_log/2026-04-28_session-05_phase2-stage0.md` — 이 파일

## Concepts taught (학습 강화)
- **스노우볼 샘플링** — 학술적 기법. 1-hop 안전, 2-hop+ 주제 드리프트 폭주. 빈도/블랙리스트/카테고리 3종 필터 + 사람 confirm 1회 필수.
- **Apify Python SDK** — `client.actor(id).call(run_input=...)` 동기 패턴. dataset.iterate_items() 자동 페이징. 비용 모니터링 가능 (`run.usageTotalUsd`).
- **`__init__.py` 패키지 마커** — 빈 파일이지만 *"이 폴더는 패키지"* 신호. import 가능해짐.
- **`__main__.py` 진입점** — `python -m <package>` 실행시 자동 호출. argparse 와 묶어 CLI 도구화.
- **f-string `!r` 변환** — `repr()` 호출 등가. 디버깅 출력에서 빈 문자열·줄바꿈·따옴표 명시.
- **`if __name__ == "__main__":`** — 직접 실행 vs import 구분 가드.
- **Airflow TaskFlow API** (`@dag`, `@task`) — 함수 스타일 DAG. classic `PythonOperator` 보다 짧음.
- **`schedule=None` + `catchup=False`** — 수동 트리거 전용 + 과거 backfill 안 함. smoke 용 안전 조합.
- **Task 함수 내부 import 패턴** — DAG 파싱 부담 줄이는 관례. scheduler 가 자주 파싱하므로 무거운 import 는 task 실행 시점으로.
- **Docker bind mount 슬래시 함정** — `./host:container` 형식, 컨테이너 쪽 `/` 빠지면 named volume 으로 오해. 사일런트 버그.
- **PYTHONPATH 와 사용자 패키지** — Airflow 컨테이너에서 dags/ 외 폴더 import 하려면 PYTHONPATH 명시. dags/ 안에 두는 대안보다 깔끔.

## Portfolio assets added
- **메트릭** (`metrics/run_results.jsonl`):
  - `stage0_apify_smoke` — actor_run_id, items_returned: 20, runtime: 17.4s, 발견 이슈 4개
  - `stage0_airflow_dag_smoke` — DAG run, runtime: 20s, 해결 이슈 3개, 관찰 3건
- **문서** (`docs/notes/instagram_post_schema_sample.json`):
  - 응답 1건 + 필드 인벤토리 (20+ 필드, 타입·노트)
  - 후처리 규칙 (정규식, NULL 변환, 광고 라벨 키워드, 브랜드 계정 패턴)
- **메모리** (`~/.claude/projects/.../memory/project_secret_management_progression.md`):
  - 시크릿 운용 3단계 마이그 계획 (env_file → Variable → Connection)
- **이미지** (Yeon 캡처 예정):
  - `docs/images/02_apify_smoke_dag_grid.png` — Airflow Grid view 성공
  - `docs/images/02_apify_smoke_dag_log.png` — Logs 화면 (20건 수집 출력)

## Open questions
- **Stage 1 (Postgres 적재)**: `raw.ig_posts` 테이블 스키마 — `id` UNIQUE 키 / JSONB 컬럼으로 raw 보존 vs 평면화? (다음 세션 첫 결정)
- **idempotency 패턴**: `INSERT ... ON CONFLICT DO UPDATE` (PostgreSQL MERGE 대안). 멱등 5회 검증 절차 설계 필요.
- **광고 라벨 컬럼**: dbt staging 단계에서 정규식 파싱 vs 수집 단계에서 미리 추출? (Phase 2 끝 / Phase 3 시작 사이 결정)
- **#다이소화장품 풀 부족 가능성**: 본 수집 K=400 잡았을 때 실제로 몇 건 들어오는지. 부족 시 `#다이소뷰티` `#다이소템` 으로 확장 (Round 2 자동 처리될 가능성).

## Metrics (이번 세션 측정값)
- Stage 0 로컬 smoke: 20 items / 17.4s actor runtime
- Stage 0 DAG smoke: 20 items / 20s total run / 10s actor runtime
- 디버깅 사이클: PYTHONPATH 함정 1건 (1차 fail → 2/3차 success)
- Apify 비용: $0.05 미만 (smoke 2회 합산 추정)
- 작성한 코드 파일: 5개 (가이드 모드, ≈150줄 합)
- 수정한 인프라 파일: 2개 (compose, requirements)

## Next session — start here

1. **이번 세션 git commit + push** (포트폴리오 GitHub 동기화)
2. **Stage 1 진입**: `raw.ig_posts` 테이블 설계
   - `docs/notes/instagram_post_schema_sample.json` 의 field_inventory 기반
   - 후보 컬럼 ≈ 18개 + JSONB `raw_payload` 컬럼 (보존용)
   - PRIMARY KEY: `id` (Instagram 게시물 ID, UNIQUE)
   - `INSERT ... ON CONFLICT (id) DO UPDATE` 멱등 패턴
3. **Stage 1 의 파일 목록 (예상)**:
   - `infra/postgres/init/03_raw_schema.sql` — raw 스키마 + ig_posts 테이블 DDL
   - `data_generation/collectors/loaders/postgres_loader.py` — items → ON CONFLICT INSERT
   - `dags/dag_ig_collect_smoke.py` 수정 — load task 추가
4. **멱등 5회 검증** — 같은 입력 5회 trigger → row count 변화 없음 확인 (불변규칙 #4)
5. **(Stage 1 끝) Stage 2 본수집** — 옵션 X (#뷰티 K=600 / #올리브영 K=1000 / #다이소화장품 K=400)
