# AdInsight Agent

> **글로벌 인플루언서 광고 성과 분석 플랫폼 + AI-Native Data Mart + Text2SQL BI Agent**
> A multi-region influencer ad performance analytics platform with an AI-Native data mart and a Text2SQL BI agent — built on Airflow, dbt, Superset, LangChain, pgvector.

대만·태국·한국·일본 4개 지역의 TikTok / Instagram / YouTube Shorts 인플루언서 광고 데이터를 수집·정제·모델링하고, LLM Agent가 자연어로 질의할 수 있는 데이터 플랫폼.

---

## TL;DR
- **도메인**: 멀티 플랫폼 인플루언서 광고 (TikTok / Instagram / YouTube Shorts), 다국가 (TW · TH · KR · JP)
- **스택**: Airflow 2.9 · Postgres 16 + pgvector · dbt-postgres 1.8 · Superset 4.x · LangChain · Gemini / Claude
- **차별점**: AI-Native 마트 레이어 (LLM 친화 비정규화 + dbt meta synonyms · example_questions) + Text2SQL 평가 프레임워크
- **로컬 실행**: MacBook Apple Silicon, Docker Compose 한 방에 기동

---

## JD ↔ 산출물 매핑

| JD 항목 | 프로젝트 산출물 |
|---|---|
| AI Native 데이터 마트 설계·운영 | `dbt/models/ai_native/` (LLM 친화 비정규화 + dbt YAML semantic metadata) |
| 대규모 ETL 파이프라인 (Airflow) | `dags/` (수집 / 정제 / 집계 / 품질 / 리포트 DAG) + 백필 |
| AI 학습용 데이터 전처리 | 캡션·해시태그·댓글 정제 + multilingual embedding + pgvector |
| Tableau / Superset 대시보드 | `dashboards/` (Advertiser ROI / Creator Rank / Campaign Ops) |
| LLM 연동 자동 분석 리포트 | `dags/weekly_llm_report.py` + `reports/{YYYY-WW}/` |
| Text2SQL BI Agent | `agent/` (LangChain schema-aware SQL Agent + 평가 프레임워크) |
| 데이터 리터러시 교육 | `docs/` 아키텍처·요청 플로우·동시성·면접 토크포인트 |
| 대용량 쿼리 최적화 | `metrics/query_optimization_log.md` (Before/After 기록) |
| Pandas + API 연동 | `data_generation/`, `dags/ingest_*.py` |
| LangChain · Vector DB 우대 | LangChain SQL Agent + pgvector |
| Superset 오픈소스 기여 우대 | `docs/superset_contribution_plan.md` |
| 글로벌 협업 경험 우대 | 다국가 모델링 (timezone · i18n · currency) + 영문 README 병행 |

---

## 빠른 시작 (Quick Start)

### 전제 조건
- Docker Desktop (메모리 12GB 할당 권장: Settings → Resources → Memory)
- Python 3.11, [uv](https://docs.astral.sh/uv/) 패키지 매니저

### 1단계 — 환경 변수 준비
```bash
cp .env.example .env
# .env 파일을 열어 비밀번호·시크릿 키 변경 (POSTGRES_PASSWORD, SUPERSET_SECRET_KEY 등)
```

### 2단계 — Python 의존성 설치 (개발 도구)
```bash
uv sync
```

### 3단계 — 포트 충돌 확인
```bash
# 아래 포트가 비어있어야 함: 5432 / 6379 / 8080 / 8088 / 5555
lsof -i :5432,6379,8080,8088,5555
```

### 4단계 — 스택 기동
```bash
time make up   # 최초 실행 시 이미지 pull 로 5~15분 소요
```

### 5단계 — 기동 확인
```bash
make ps        # 모든 서비스 STATUS = healthy 확인

# 각 UI 접속
#   Airflow  → http://localhost:8080  (admin / admin)
#   Superset → http://localhost:8088  (make superset-init 후 admin / admin)
#   Flower   → http://localhost:5555  (Celery 모니터링)
#   Postgres → localhost:5432         (make psql)
```

### 6단계 — Superset 초기화 (최초 1회)
```bash
make superset-init
```

### 7단계 — Smoke Test DAG 실행
```bash
# Airflow UI → DAGs → sample_smoke_test → Toggle ON → Trigger DAG
# Graph view 에서 select_one task 초록색 = 스택 정상
make airflow-cli cmd='dags trigger sample_smoke_test'
```

### 종료
```bash
make down          # 컨테이너 중지 (볼륨 유지)
make clean-confirm # 컨테이너 + 볼륨 삭제 (데이터 초기화)
```

---

## 아키텍처 (요약)

```
[Ingestion]   Kaggle CSV / 공개 API / SDV 합성  ─┐
                                                   ▼
[Storage]     Postgres schemas: raw → staging → intermediate → marts → ai_native
                                                   │
                                  ┌────────────────┼─────────────────────┐
                                  ▼                ▼                     ▼
[Consumption] Superset 대시보드   Text2SQL Agent   Weekly LLM Report DAG
                                       │
                                       ▼
                               pgvector (schema embedding store)
```

상세 다이어그램: `docs/adinsight_project_blueprint.md` (섹션 3-3)

---

## 폴더 구조 (요약)

```
adinsight-agent/
├── CLAUDE.md                  # Claude Code 컨텍스트
├── Makefile
├── pyproject.toml             # uv
├── docker-compose.yml         # (Phase 1)
├── infra/{airflow,superset,postgres}
├── data_generation/           # SDV / Faker 합성 데이터
├── dags/                      # Airflow DAG
├── dbt/                       # dbt-postgres
│   └── models/{staging,intermediate,marts,ai_native}
├── agent/                     # Text2SQL BI Agent
├── dashboards/                # Superset YAML export
├── metrics/                   # 포트폴리오 지표 자동 기록
├── reports/                   # 주간 LLM 리포트 (gitignore)
├── docs/
│   ├── adinsight_project_blueprint.md   # ⭐ 마스터 설계서
│   └── session_log/                      # 세션별 작업 로그
└── tests/{unit,integration}
```

전체 트리: 블루프린트 섹션 4

---

## Phase 진행 상황

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | Repo Bootstrap (스켈레톤·CLAUDE.md·세션 로그) | ✅ |
| 1 | docker-compose · Postgres · Airflow · Superset · pgvector | 🟡 코드 완료, `make up` 대기 |
| 2 | 합성 + 공개 데이터 적재 (raw 레이어) | ⬜ |
| 3 | dbt staging / intermediate / marts (Kimball star schema) | ⬜ |
| 4 | **AI-Native data mart** (⭐ JD 핵심) | ⬜ |
| 5 | Superset 대시보드 + 쿼리 최적화 | ⬜ |
| 6 | **Text2SQL BI Agent** (⭐ JD 가장 핵심) | ⬜ |
| 7 | 주간 LLM 자동 리포트 DAG | ⬜ |
| 8 | 데이터 품질 · 관측성 · CI | ⬜ |
| 9 | 문서화 · 데모 영상 · 면접 준비 | ⬜ |

---

## 포트폴리오 메트릭 (자동 기록)

`metrics/portfolio_metrics.md` 참조. Phase별 행 수·dbt 테스트 커버리지·쿼리 최적화 비율·Text2SQL Execution Accuracy 등이 자동 누적됩니다.

---

## 세션 로그
모든 작업 세션은 `docs/session_log/`에 기록됩니다. 세션 시작 시 가장 최신 로그를 확인하세요.

---

## References
- Airflow: <https://airflow.apache.org/docs/>
- dbt: <https://docs.getdbt.com/>
- Superset: <https://superset.apache.org/docs/intro/>
- LangChain SQL: <https://python.langchain.com/docs/use_cases/sql/>
- pgvector: <https://github.com/pgvector/pgvector>
- SDV: <https://sdv.dev/>

---

## License
MIT (see `LICENSE`). 공개 데이터셋 출처·라이선스는 각 적재 DAG 코드 헤더에 명시.
