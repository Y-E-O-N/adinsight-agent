# Phase 2B 구현 가이드 — Apify 운영 등급 자동화 파이프라인

> **이 문서의 목적**: Codex 세션에서 직접 타이핑하며 따라갈 수 있는 단계별 구현 가이드.
> 각 단계마다 "왜 이렇게 하는가"를 함께 설명합니다.
>
> **작업 도구**: Codex (터미널)
> **예상 세션 수**: 2~3 세션
> **전제 조건**: `make up` 으로 스택이 기동된 상태

---

## 이번에 만드는 것 (전체 그림)

```
dags/
├── common/
│   └── ig_collect_utils.py      ← 1단계: watermark + freshness 공통 함수
├── dag_ig_collect_daily.py      ← 2단계: 매일 오전 6시 자동 수집 DAG
└── dag_ig_backfill.py           ← 3단계: 특정 날짜 재수집 DAG
```

**기존 파일은 건드리지 않습니다.** `dag_ig_collect_round1.py`와 `dag_ig_collect_smoke.py`는 그대로 유지합니다.

---

## 핵심 개념 (먼저 읽기)

### watermark란?
파이프라인이 "어디까지 처리했는지"를 기억하는 마커입니다.
- 예: `last_collected_at = "2026-06-15"` → "어제까지 수집 완료"
- Airflow Variable에 저장 → UI에서 직접 확인/수정 가능
- 없으면 매번 전체 재수집, 중복이 생김

### freshness check란?
"오늘 데이터가 제대로 도착했는가"를 감시하는 로직입니다.
- 수집 0건 → `ERROR` (파이프라인 완전 실패 또는 Instagram 차단)
- 평소보다 70% 이상 감소 → `WARNING` (차단 의심 신호)
- 이게 없으면 파이프라인이 조용히 실패해도 아무도 모름

### backfill이란?
"어제 파이프라인이 실패했는데 데이터를 다시 채워넣고 싶다"는 상황에 쓰입니다.
- `target_date` 파라미터로 특정 날짜 지정 → 그날 데이터 재수집
- idempotent이므로 여러 번 실행해도 중복 없음

---

## 1단계: `raw.ig_posts`에 `collected_at` 컬럼 추가

freshness check가 "오늘 수집 건수"를 세려면 수집 시점 컬럼이 필요합니다.
현재 `raw.ig_posts`에 이 컬럼이 있는지 먼저 확인합니다.

### 1-1. 현재 스키마 확인

```bash
# Postgres에 접속
make psql

# 컬럼 목록 확인
\d raw.ig_posts
```

`collected_at` 컬럼이 없으면 다음 단계로, 있으면 1단계 건너뜁니다.

### 1-2. 컬럼 추가 (없을 때만)

```sql
-- Postgres 터미널에서 실행
ALTER TABLE raw.ig_posts
    ADD COLUMN IF NOT EXISTS collected_at TIMESTAMPTZ DEFAULT now();

-- 기존 행에 현재 시각 채우기
UPDATE raw.ig_posts SET collected_at = now() WHERE collected_at IS NULL;

-- 확인
SELECT COUNT(*), MIN(collected_at), MAX(collected_at) FROM raw.ig_posts;
```

예상 결과: `49 | 2026-06-16 ... | 2026-06-16 ...`

```bash
# Postgres 종료
\q
```

### 1-3. `postgres_loader.py`에 `collected_at` 반영

기존 `upsert_posts()` 함수에서 INSERT 시 `collected_at = now()`를 추가해야 합니다.

**Codex에게 이렇게 요청하세요**:
```
data_generation/collectors/loaders/postgres_loader.py 를 읽고,
raw.ig_posts upsert 쿼리에서 collected_at = now() 를 추가해줘.
collected_at이 이미 있으면 ON CONFLICT 시 업데이트하지 않는다.
변경 전에 현재 코드를 보여주고, 바꿀 부분만 설명해줘.
```

---

## 2단계: `dags/common/ig_collect_utils.py` 작성

### 2-1. 파일 생성

```bash
# common 폴더에 __init__.py 확인 (없으면 생성)
ls dags/common/
# .gitkeep 만 있으면 __init__.py 없음 → 생성 필요
touch dags/common/__init__.py
```

### 2-2. 파일 작성 (Codex 가이드 모드)

**Codex에게 이렇게 요청하세요**:
```
CLAUDE.md와 docs/analysis/phase2b_apify_pipeline_design.md 를 읽어줘.

dags/common/ig_collect_utils.py 를 만들 거야.
이 파일에 들어갈 함수는 4개야:

1. get_watermark() → Airflow Variable에서 마지막 수집 날짜 읽기
2. set_watermark(date_str) → Variable 업데이트
3. get_today_collected_count() → 오늘 raw.ig_posts 건수 조회
4. get_weekly_avg_count() → 최근 7일 일평균 건수 조회
5. check_freshness() → 위 두 함수로 이상치 탐지

각 함수를 한 번에 하나씩 가르쳐줘.
함수 시그니처, 왜 이게 필요한지, 핵심 로직 설명을 먼저 해줘.
그 다음에 내가 직접 타이핑할 수 있게 스니펫을 보여줘.
```

### 2-3. 완성 후 로컬 테스트

```bash
# 가상환경 활성화 (uv)
source .venv/bin/activate  # 또는 프로젝트 방식에 맞게

# 함수별 smoke test (Postgres 직접 연결)
POSTGRES_HOST=localhost \
POSTGRES_PORT=5432 \
POSTGRES_DB=adinsight \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=<비밀번호> \
python -c "
from dags.common.ig_collect_utils import get_today_collected_count, get_weekly_avg_count
print('today:', get_today_collected_count())
print('weekly_avg:', get_weekly_avg_count())
"
```

예상 결과:
```
today: 0      ← 오늘 아직 수집 안 함
weekly_avg: 0.0  ← 일별 수집 기록 없음 (정상)
```

---

## 3단계: `dags/dag_ig_collect_daily.py` 작성

### 3-1. 설계 이해 (작성 전 필독)

```
dag_ig_collect_daily
│
├── task: log_watermark          ← watermark 읽고 로그
│
├── task: collect_beauty (200건)
├── task: collect_oliveyoung (200건)   ← 3개 병렬 실행
├── task: collect_daiso (200건)
│
├── task: check_freshness        ← 수집 건수 이상치 확인
│                                   0건이면 DAG FAIL
│                                   급감이면 WARNING
├── task: update_watermark       ← 오늘 날짜로 업데이트
│
└── task: record_metrics         ← run_results.jsonl 기록
```

### 3-2. 파일 작성 (Codex 가이드 모드)

**Codex에게 이렇게 요청하세요**:
```
CLAUDE.md를 먼저 읽어줘.
다음으로 dags/dag_ig_collect_round1.py 를 읽어줘.
마지막으로 dags/common/ig_collect_utils.py 를 읽어줘.

dags/dag_ig_collect_daily.py 를 만들 거야.
round1 DAG 구조를 참고해서, 아래 조건으로 만들어줘:

- dag_id: "ig_collect_daily"
- schedule: 매일 오전 6시 (Asia/Seoul) → UTC 변환
- seed: 뷰티 200건 / 올리브영 200건 / 다이소화장품 200건
- 추가 tasks: log_watermark, check_freshness, update_watermark
- check_freshness는 dags/common/ig_collect_utils.py의 함수를 쓴다

한 번에 전체 코드를 주지 말고,
DAG 선언부 → seed collect tasks → freshness check task → watermark tasks 순서로
하나씩 설명하고 스니펫 보여줘.
```

### 3-3. 스케줄 설정 주의사항

오전 6시 KST = UTC 21시 (전날) 입니다.

```python
# dags/dag_ig_collect_daily.py 안에서
from airflow.timetables.interval import CronDataIntervalTimetable

# UTC 기준으로 설정
schedule="0 21 * * *",  # UTC 21:00 = KST 06:00

# 또는 pendulum 사용
import pendulum
schedule=pendulum.duration(days=1),
start_date=pendulum.datetime(2026, 6, 16, 21, 0, tz="UTC"),
```

**Codex에게 물어볼 것**:
```
cron 표현식 "0 21 * * *" 이 무슨 의미인지 설명해줘.
Asia/Seoul 오전 6시를 UTC로 변환하면 왜 전날 21시가 되는지도 설명해줘.
```

### 3-4. Airflow에서 DAG 확인

```bash
# DAG 파싱 오류 확인
make airflow-cli cmd='dags list'
# ig_collect_daily 가 목록에 나와야 함

# DAG import 오류 확인
make airflow-cli cmd='dags report'

# 수동 실행 테스트
make airflow-cli cmd='dags trigger ig_collect_daily'

# Airflow UI에서 확인
# http://localhost:8080 → DAGs → ig_collect_daily
```

### 3-5. Variable 확인

```bash
# Airflow UI → Admin → Variables
# ig_collect_last_watermark 가 생성되었는지 확인

# 또는 CLI로
make airflow-cli cmd='variables get ig_collect_last_watermark'
```

---

## 4단계: `dags/dag_ig_backfill.py` 작성

### 4-1. backfill DAG 목적

```
언제 쓰는가:
- "어제 파이프라인이 실패해서 데이터가 비었어. 다시 채워줘."
- "3일 전 데이터가 잘못 들어왔어. 다시 수집해서 덮어써."

어떻게 쓰는가:
Airflow UI → DAGs → ig_collect_backfill
→ Trigger w/ config
→ {"target_date": "2026-06-14", "seeds": ["뷰티"]}
```

### 4-2. 파일 작성 (Codex 가이드 모드)

**Codex에게 이렇게 요청하세요**:
```
dags/dag_ig_collect_daily.py 를 참고해서
dags/dag_ig_backfill.py 를 만들 거야.

차이점:
- schedule=None (수동 trigger 전용)
- Airflow Params로 target_date, seeds 받기
- watermark 업데이트 안 함 (backfill은 과거 채우기라 watermark 변경 불필요)
- 수집 후 idempotency 확인용 로그 추가

Params 사용법과 수동 trigger 시 config JSON 입력하는 법을 먼저 설명해줘.
```

### 4-3. backfill 테스트

```bash
# 과거 날짜로 backfill 실행
make airflow-cli cmd='dags trigger ig_collect_backfill --conf "{\"target_date\": \"2026-06-15\"}"'

# idempotency 검증: 같은 날짜로 2번 실행 후 row count 확인
make psql
```

```sql
-- backfill 전/후 row count 비교
SELECT COUNT(*) FROM raw.ig_posts;
-- 2번 실행해도 숫자가 같아야 함 (idempotent)
```

---

## 5단계: 전체 검증

### 5-1. daily DAG 첫 자동 실행 대기

스케줄에 따라 다음 날 오전 6시에 자동 실행됩니다.
바로 확인하고 싶으면:

```bash
# 수동 trigger
make airflow-cli cmd='dags trigger ig_collect_daily'

# 실행 상태 확인
make airflow-cli cmd='dags state ig_collect_daily $(date +%Y-%m-%dT%H:%M:%S) utc'
```

### 5-2. 메트릭 확인

```bash
# 수집 결과 확인
make psql
```

```sql
-- 오늘 수집 건수
SELECT
    collected_at::date AS day,
    COUNT(*) AS count
FROM raw.ig_posts
WHERE collected_at >= now() - INTERVAL '7 days'
GROUP BY day
ORDER BY day DESC;

-- watermark 확인
-- (Airflow UI → Admin → Variables → ig_collect_last_watermark)
```

```bash
# run_results.jsonl 확인
tail -5 metrics/run_results.jsonl
```

### 5-3. freshness check 강제 테스트 (선택)

```bash
# raw.ig_posts를 비워서 freshness FAIL을 의도적으로 발생시킴 (테스트용)
# ⚠️  실제 데이터가 삭제되므로 개발 환경에서만!
make psql
```

```sql
-- 오늘 수집 데이터를 임시로 숨기기 (삭제 아님)
-- (실제 테스트가 필요하면 Codex에게 mock 방법 물어볼 것)
```

---

## 완성 기준 체크리스트

다음 항목을 모두 확인하면 Phase 2B 완료입니다:

- [ ] `raw.ig_posts`에 `collected_at` 컬럼 있음
- [ ] `dags/common/ig_collect_utils.py` 작성 완료
  - [ ] `get_watermark()` 동작 확인
  - [ ] `set_watermark()` 동작 확인
  - [ ] `get_today_collected_count()` 동작 확인
  - [ ] `check_freshness()` 동작 확인
- [ ] `dags/dag_ig_collect_daily.py` 작성 완료
  - [ ] `make airflow-cli cmd='dags list'` 에서 `ig_collect_daily` 보임
  - [ ] 수동 trigger 성공
  - [ ] Airflow Variable `ig_collect_last_watermark` 생성됨
  - [ ] `run_results.jsonl`에 메트릭 기록됨
- [ ] `dags/dag_ig_backfill.py` 작성 완료
  - [ ] 과거 날짜로 backfill 실행 성공
  - [ ] 2회 실행 후 row count 동일 (idempotency 검증)
- [ ] `metrics/run_results.jsonl`에 `dag_id: ig_collect_daily` 항목 있음

---

## 포트폴리오 메트릭 기록 (완료 시)

`docs/portfolio_draft.md` Phase 2 섹션에 아래 내용을 채우세요:

```markdown
| 메트릭 | 값 |
|---|---|
| 자동화 스케줄 | 매일 오전 6시 KST |
| seed 수 | 3개 (뷰티 / 올리브영 / 다이소화장품) |
| 요청 건수/일 | 600건 |
| 실수집 건수/일 (초기) | [실측값 채우기] |
| watermark 방식 | Airflow Variable |
| freshness check | 0건 = FAIL / 주간평균 30% 미만 = WARN |
| backfill 검증 | 동일 날짜 2회 실행 → row count 동일 |
```

---

## Codex 세션 시작 템플릿

새 Codex 세션을 열 때 이 프롬프트를 복사해서 시작하세요:

```
CLAUDE.md와 AGENTS.md를 먼저 읽어줘.
docs/session_log/ 의 최신 로그도 읽고 Next session — start here 확인해줘.

오늘 할 일:
docs/guides/phase2b_apify_daily_pipeline_guide.md 가이드 문서를 따라
Apify 자동화 파이프라인을 단계별로 구현할 거야.

[1단계 / 2단계 / 3단계] 부터 시작할게.
가이드 문서의 해당 단계를 읽고, 무엇을 만들지 설명해준 다음
Guided-Coding 원칙대로 진행해줘.
```

---

## 참고 문서

- `docs/analysis/phase2b_apify_pipeline_design.md` — 설계 결정 + 아키텍처 다이어그램
- `docs/adr/003-redesign-ac-strategy.md` — 왜 A+C 전략을 채택했는가
- `dags/dag_ig_collect_round1.py` — 재사용할 기존 패턴
- `data_generation/collectors/apify_hashtag.py` — 재사용할 수집 함수
- `data_generation/collectors/loaders/postgres_loader.py` — 재사용할 upsert 함수
