# Session 05 — 학습 개념 정리 (2026-04-28)

이 세션에서 새로 배우거나 깊이 다룬 개념을 Yeon 본인이 나중에 복습할 수 있도록 정리.

---

## 1. 데이터 수집 전략

### 1.1 스노우볼 샘플링 (Snowball Sampling)
- **개념**: 시드(초기 샘플) 에서 시작 → 그 결과에서 새 후보 추출 → 다음 라운드 시드로 확장하는 그래프 기반 표본 수집.
- **장점**: 시드 편향 보정, 새로운 niche 발굴.
- **함정**:
  - **조합 폭발**: 한 게시물당 평균 10~30개 해시태그 → 라운드마다 후보가 기하급수.
  - **주제 드리프트**: 인접 토픽으로 점점 멀어짐 (뷰티 → 일상 → vanity).
  - **빈도 노이즈**: 1번 등장한 해시태그까지 다음 라운드에 넣으면 무의미.
- **안전 규칙** (이 프로젝트 채택):
  1. **1-hop 만** (Round 2 까지). 더 필요하면 사람이 판단.
  2. 빈도 ≥ 1% 필터.
  3. 블랙리스트 (vanity·lifestyle·location ≈ 50개).
  4. LLM 카테고리 분류 1회 (Gemini Flash, "beauty domain == Y").
  5. **사람 confirm** 1단계 (자동화 X, 정직성 ↑).

### 1.2 시드 다양성 — 3 Layer
| 레이어 | 예시 | 잡히는 크리에이터 |
|---|---|---|
| 광역 | `#뷰티스타그램` `#데일리뷰티` | 종합 뷰티 인플루언서 |
| 세부 카테고리 | `#스킨케어추천` `#립스틱추천` | 제품 카테고리 전문 마이크로 |
| 브랜드/리테일 | `#올리브영추천` `#다이소화장품` | 협찬·체험단 인플루언서 |

→ 이번 시드 (`#뷰티` / `#올리브영` / `#다이소화장품`) 는 광역+브랜드+니치 자연 분포.

### 1.3 K (수집량) 추정
- 단일 K 가 아닌 **해시태그 볼륨에 따라 차등** 적용.
- 두 관점:
  - **샘플링 비율**: 작은 풀일수록 같은 K 가 더 큰 비율 → 통계적 대표성 ↑.
  - **시간 윈도**: 큰 풀에서 K 가 작으면 *수 시간 분량* 만 찍힘 (시점 편향). 작은 풀에서 같은 K 는 *수 주 분량* 까지 자연 분산.

---

## 2. Apify SDK

### 2.1 호출 패턴 (Python)
```python
from apify_client import ApifyClient
client = ApifyClient(token=os.environ["APIFY_TOKEN"])
run = client.actor("apify/instagram-hashtag-scraper").call(run_input={
    "hashtags": ["다이소화장품"],
    "resultsLimit": 20,
})
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
```
- `actor(...).call(...)` = "실행 시작 + 완료 대기" 동기 처리.
- `iterate_items()` 는 제너레이터 (자동 페이징).

### 2.2 환경변수 자동 인식
- `APIFY_TOKEN` 으로 저장하면 `ApifyClient()` 만 호출해도 자동 인식.
- 다른 이름이면 `ApifyClient(token=os.environ["다른이름"])` 명시 전달.

### 2.3 비용 모니터링
```python
run_info = client.run(run["id"]).get()
print(f"Cost USD: {run_info['usageTotalUsd']}")
```

### 2.4 Actor 입력 함정
- **알려지지 않은 필드는 조용히 무시**됨. 에러 안 띄움.
- 예: `resultLimit` (오타) vs `resultsLimit` (올바름) — 오타면 기본값 (수백~수천) 으로 실행 → 비용 폭주.

---

## 3. 파이썬 패키지 구조

### 3.1 `__init__.py` 의 역할
- 빈 파일이지만 *"이 폴더는 패키지"* 라고 파이썬에 알리는 신호.
- 없어도 Python 3.3+ 에서는 동작 (namespace package) 하지만 명시 권장.

### 3.2 `__main__.py` 의 역할
- 패키지를 `python -m <패키지명>` 으로 실행 가능하게 함.
- 보통 `argparse` 와 묶어 CLI 도구화.

### 3.3 import 규칙 (PEP 8)
1. 표준 라이브러리 (`os`, `argparse`)
2. (빈 줄 1개)
3. 외부 패키지 (`apify_client`)
4. (빈 줄 1개)
5. 내부 모듈 (`data_generation.collectors...`)

### 3.4 `if __name__ == "__main__":`
- 직접 실행되면 `__name__ == "__main__"`, import 만 되면 모듈명.
- 이 가드로 *"파일 직접 실행 시만 main 호출"* 분리. import 시점엔 부수효과 없음.

### 3.5 타입 힌트 (PEP 484, 585)
- `list[dict]`, `int`, `str` — Python 3.9+ 에서 builtin generic.
- `from __future__ import annotations` = 타입 힌트 지연 평가 (런타임 평가 안 함, 더 가벼움).

### 3.6 f-string 변환 플래그
| 플래그 | 의미 |
|---|---|
| `{x}` | `str(x)` |
| `{x!r}` | `repr(x)` — 따옴표·이스케이프 포함. 디버깅용 |
| `{x!s}` | `str(x)` 명시적 |
| `{x!a}` | `ascii(x)` |

---

## 4. Airflow

### 4.1 TaskFlow API (`@dag`, `@task`)
- Airflow 2.x 의 모던 스타일.
- `@dag` 함수가 DAG 정의, `@task` 함수가 task 정의.
- classic `PythonOperator(python_callable=...)` 보다 짧고 직관적.

### 4.2 DAG 핵심 인자
```python
@dag(
    dag_id="...",
    schedule=None,        # None = 자동 트리거 끔 (수동만)
    start_date=datetime(2026, 4, 28),
    catchup=False,        # 과거 backfill 안 함
    tags=["..."],
)
```

### 4.3 모듈 최하단 DAG 호출
```python
def my_dag():
    @task
    def t1(): ...
    t1()

my_dag()   # ← 이 줄 빠지면 scheduler 가 DAG 인스턴스 못 찾음
```

### 4.4 Task 함수 내부 import
- 무거운 import 는 task 함수 내부에 두는 것이 관례.
- 이유: scheduler 가 DAG 파일을 ~30초~1분 주기로 파싱. 모듈 import 가 무거우면 scheduler 부담.

### 4.5 Task 로그 위치
- 컨테이너 안: `/opt/airflow/logs/dag_id=*/run_id=*/task_id=*/attempt=*.log`
- 호스트에서: `logs/dag_id=*/run_id=*/task_id=*/attempt=*.log`
- UI: Grid 탭 → 사각형 클릭 → Logs 탭

### 4.6 DAG 일시정지·트리거
- 신규 DAG 는 `DAGS_ARE_PAUSED_AT_CREATION=true` 설정상 paused 로 생성됨.
- UI 에서 토글 켜고 ▶ 클릭으로 trigger.
- CLI: `airflow dags unpause <id>` + `airflow dags trigger <id>`.

---

## 5. Docker / Compose

### 5.1 Bind mount 슬래시 함정
```yaml
- ./host:/container/path     ✓ 정상 bind mount
- ./host:container/path      ✗ named volume 으로 오해 (사일런트 버그)
```
- **컨테이너 쪽 경로는 반드시 `/` 시작**.
- 슬래시 빠지면 Docker 가 *"container/path"* 라는 이름의 named volume 을 만들어버림.
- 호스트 폴더가 컨테이너에 안 보임 → DAG 가 import 실패하는데 원인 모호.

### 5.2 환경변수 주입 패턴
```yaml
environment:
  APIFY_TOKEN: ${APIFY_TOKEN}     # docker-compose 가 같은 폴더의 .env 자동 읽음
```
- `.env` 의 `APIFY_TOKEN=xxx` 가 `${APIFY_TOKEN}` 자리에 끼워짐.
- 변경 후 `docker compose up -d` 로 컨테이너 재생성 (build 는 X).

### 5.3 Image rebuild vs Container restart
| 변경 항목 | 필요한 작업 |
|---|---|
| `Dockerfile`, `requirements.txt` | `docker compose build` + `up -d` |
| `docker-compose.yml` 의 `environment`, `volumes` | `docker compose up -d` (build 필요 X) |
| 코드 (마운트된 파일) | 즉시 반영 (재시작 X) |

---

## 6. PYTHONPATH 와 사용자 패키지

### 6.1 함정
- Airflow 컨테이너는 `/opt/airflow/dags` 만 자동으로 import 경로에 포함.
- `/opt/airflow/data_generation` 에 마운트해도 import 안 됨 → `ModuleNotFoundError`.

### 6.2 해결 (이 프로젝트 채택)
```yaml
environment:
  PYTHONPATH: /opt/airflow
```
- `/opt/airflow` 자체를 import 경로에 추가.
- 이후 `from data_generation.collectors... import ...` 가 동작.

### 6.3 대안과 비교
| 방법 | 장점 | 단점 |
|---|---|---|
| **PYTHONPATH 추가** (채택) | dags/ 폴더 깨끗 유지 | env 변수 1개 추가 |
| `dags/data_generation/` 로 이동 | 추가 설정 X | dags/ 폴더 오염, scheduler 파싱 부담 |
| pip install 패키지화 | 가장 정석 | 매 변경마다 rebuild 필요 |

---

## 7. 디버깅 사이클 (이번 세션 사례)

### 7.1 PYTHONPATH 누락 → fail
- 1차 trigger: `ModuleNotFoundError: No module named 'data_generation'`
- 진단: 마운트는 됐지만 import 경로에 없음 → `docker compose exec airflow-worker ls /opt/airflow/data_generation` 으로 마운트 자체는 OK 확인.
- 수정: `PYTHONPATH: /opt/airflow` 추가 → `docker compose up -d` → 2차 trigger 성공.

### 7.2 자동화된 진단 명령
```bash
# 마운트 확인
docker compose exec airflow-worker ls /opt/airflow/data_generation

# import 확인
docker compose exec airflow-worker python -c "from data_generation.collectors.apify_hashtag import collect_hashtag; print('OK')"

# 환경변수 확인
docker compose exec airflow-worker env | grep APIFY

# Task 실패 로그
docker compose exec airflow-worker bash -c 'find /opt/airflow/logs -name "*.log" -path "*ig_collect_smoke*attempt*" | sort | tail -1 | xargs cat'
```

---

## 8. 면접 답변 카드 (이번 세션에서 적립)

### Q. "Airflow 안에서 사용자 모듈은 어떻게 import 하셨나요?"
> *PYTHONPATH=/opt/airflow 환경변수로 import 경로를 명시했습니다. dags/ 폴더는 DAG 파일 전용이라는 관례를 지키되, 비즈니스 로직(collectors, dbt runners) 은 별도 패키지로 분리해 단위 테스트와 로컬 실행을 쉽게 했습니다.*

### Q. "왜 Apify 와 합성 데이터를 같이 쓰나요?"
> *Apify 만으로는 광고비·ROAS·결제 같은 비공개 데이터를 못 얻고, SDV 만으로는 한국 도메인의 어휘·분포가 안 잡힙니다. 그래서 Apify 로 한국 마이크로 인플루언서 N=300 의 ER·카테고리 분포를 학습하고, 그 위에 SDV 로 캠페인·결제를 합성해 LINE Pay 시나리오를 재현했습니다.*

### Q. "스노우볼 확장에서 비용·드리프트 어떻게 막았나요?"
> *세 가지 가드를 두었습니다. (1) 1-hop 만 자동, 더 깊으면 사람이 판단. (2) 빈도 1% 미만 + 블랙리스트 50개 + LLM 카테고리 분류로 noise 제거. (3) 라운드 사이에 사람 confirm 단계를 두어 자동화하지 않았습니다 — 정직성·재현성 트레이드오프 측면에서.*

### Q. "Docker bind mount 함정 만난 적 있나요?"
> *컨테이너 쪽 경로 앞 슬래시를 빠뜨려 named volume 으로 오해되는 사일런트 버그를 만났습니다. `./data_generation:opt/airflow/data_generation` 처럼 슬래시가 빠지면 Docker 가 'opt/airflow/data_generation' 이라는 이름의 볼륨을 만들어버려 호스트 폴더가 컨테이너에 안 보입니다. 대신 `:/opt/airflow/data_generation` 으로 절대경로 명시하면 정상 bind mount.*

---

## 9. 다음 세션에 이어갈 미해결 개념

- `INSERT ... ON CONFLICT (id) DO UPDATE SET ...` (PostgreSQL 멱등 패턴)
- JSONB 컬럼 vs 평면화된 컬럼 (스키마 진화 vs 쿼리 성능 trade-off)
- dbt staging 의 PII 해시 패턴 (불변규칙 #3)
- 정규식으로 caption 에서 hashtag·mention·광고 라벨 추출 (`re.findall`)
