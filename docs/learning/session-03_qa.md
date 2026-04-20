# Session 03 Q&A — Phase 1 Docker Compose (2026-04-19)

> 이 세션에서 직접 질문한 것들만 모음. 질문 배경 → 답변 → 실제 적용 순서로 정리.

---

## Q1. CMD vs CMD-SHELL — healthcheck 에서 어떻게 다른가?

**배경**: docker-compose.yml 작성 중 `test:` 형태가 두 가지여서 혼란.

| 항목 | CMD | CMD-SHELL |
|---|---|---|
| 형태 | `["CMD", "curl", "-f", "http://..."]` | `["CMD-SHELL", "curl -f ..."]` |
| 실행 방식 | exec 직접 실행 (shell 없음) | `/bin/sh -c "..."` 로 감싸서 실행 |
| 환경변수 `$VAR` | ❌ 불가 | ✅ 가능 |
| Compose 이스케이프 | 불필요 | `$$VAR` (달러 두 개) |
| 속도 | 약간 빠름 (fork 없음) | 약간 느림 |

```yaml
# CMD — 배열, shell 없이 직접 실행
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 5

# CMD-SHELL — 문자열, shell 변수나 파이프 쓸 때
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:$${PORT}/health || exit 1"]
```

**언제 어떤 걸 쓰나?**
- 단순 URL 체크 → CMD (명확하고 빠름)
- `&&`, `||`, `$VAR` 필요 → CMD-SHELL

**이 프로젝트 적용**: airflow-webserver → CMD, flower → CMD-SHELL 사용.

---

## Q2. Celery의 역할과 Airflow와의 관계

**배경**: docker-compose.yml 에 airflow-worker, flower 서비스가 나오면서 "이게 다 뭔데?"

**핵심 흐름**:

```
[Airflow Scheduler]
       │ "task A를 지금 실행해야 해" (직접 실행 안 함 — 명령만 내림)
       ▼
    [Redis]               ← 메시지 큐 (우편함)
       │ task A 꺼내서 실행
       ▼
[Celery Worker]           ← 실제 파이썬 코드를 실행하는 프로세스
       │ 결과 저장
       ▼
[Postgres airflow_meta]   ← 실행 이력·상태 기록
```

**각 컴포넌트 역할**:

| 컴포넌트 | 역할 | 비유 |
|---|---|---|
| Scheduler | "언제, 어떤 task 실행" 결정 | 관리자 |
| Redis | task 명령 임시 보관 | 우편함 |
| Celery Worker | Redis 에서 task 꺼내 실제 실행 | 실무자 |
| Flower | Worker 상태 웹 모니터링 (`localhost:5555`) | 현황판 |

**왜 Celery?**
- Worker 를 여러 머신에 분산 가능 (수평 확장)
- Scheduler 와 Worker 분리 → Worker crash 해도 Scheduler 멀쩡
- 로컬에선 Worker 1개, 운영에서는 필요한 만큼 추가

---

## Q3. Celery랑 Thread랑 무슨 관계?

**배경**: "Celery Worker 도 결국 병렬 실행 아닌가? Thread 랑 뭐가 달라?"

완전히 **다른 레이어**의 개념. 대체재가 아니라 적용 범위가 다름.

```
Thread:  [하나의 프로세스] ──► [Thread1]
                          └──► [Thread2]   ← 같은 집 안, 방 나누기 (메모리 공유)
                          └──► [Thread3]

Celery:  [Scheduler] ──► [Redis] ──► [Worker1 (다른 서버도 OK)]
                                 └──► [Worker2]   ← 다른 집에 일 맡기기 (메시지로만 통신)
                                 └──► [Worker3]
```

| 비교 항목 | Thread | Celery Worker |
|---|---|---|
| 범위 | 하나의 프로세스 안 | 별도 프로세스 (다른 서버도 가능) |
| 통신 방식 | 메모리 직접 공유 | 메시지 큐(Redis) 경유 |
| 장애 격리 | Thread crash → 프로세스 전체 위험 | Worker crash → Scheduler 영향 없음 |
| 확장성 | 같은 머신 코어 수 한계 | 다른 머신에 Worker 추가 가능 |
| 적합한 작업 | I/O 대기 많은 빠른 작업 | 오래 걸리는 독립 task |

**결론**: Celery Worker 내부에서도 Thread 를 쓸 수 있음 — 레이어가 다름.
Airflow CeleryExecutor = "작업 배분은 Celery, 각 Worker 내 실행은 프로세스/스레드."

---

## Q4. Superset이 뭔가?

**배경**: Phase 1 에 superset 서비스가 있는데 정확히 어떤 도구인지 모름.

**한 줄 정의**: SQL 쿼리 결과를 차트·대시보드로 시각화하는 Apache 오픈소스 BI(Business Intelligence) 도구.

**비유**: 엑셀 피벗 테이블의 웹 버전 + SQL 쿼리 GUI

**데이터 흐름**:
```
Postgres (데이터 저장)
    │  SQL 쿼리 실행
    ▼
Superset (쿼리 + 차트 렌더링)
    │  HTTP
    ▼
브라우저 (대시보드 표시)
```

**유사 도구와 비교**:

| 도구 | 특징 | 비고 |
|---|---|---|
| Tableau | 유료, 드래그&드롭 강력 | 상용, 오픈소스 아님 |
| Grafana | 시계열·모니터링 특화 | 데이터 분석 대시보드엔 Superset 적합 |
| Metabase | 간단하지만 기능 제한 | Superset 이 SQL Lab 등 더 강력 |
| **Superset** | 오픈소스, SQL Lab, dbt 연동 가능 | ✅ 이 프로젝트 선택 |

**이 프로젝트에서의 역할**: Phase 5 에서 광고주 ROI · 인플루언서 랭크 · 캠페인 현황 대시보드 3종 구축.

```bash
make superset-init    # 최초 1회 — admin 계정 생성 + DB 마이그레이션
# 브라우저 → http://localhost:8088  (admin / admin)
```

---

## Q5. `redis:` 를 왜 두 줄 쓰나?

**배경**: 설명 중 혼란이 생겨 `redis:` 를 중첩해서 작성함.

**잘못 작성한 형태**:
```yaml
redis:
  redis:           ← ❌ 서비스명을 두 번 쓰면 안 됨
    image: redis:7.2-alpine
```

**올바른 형태**:
```yaml
services:
  redis:           ← 서비스 이름 (한 번만)
    image: redis:7.2-alpine
```

**핵심 구분**:

| 구분 | 예시 | 설명 |
|---|---|---|
| 서비스 이름 | `redis:` | 내가 붙이는 이름. Compose 내부에서 hostname 역할 |
| 이미지 이름:태그 | `redis:7.2-alpine` | Docker Hub 에 등록된 이미지 |

> `redis:` 가 두 번 나오는 것처럼 보이는 이유: 서비스 이름을 이미지와 같은 이름(`redis`)으로 붙였기 때문. 서비스 이름을 `my-cache:` 로 붙이면 혼란이 없었을 것.
