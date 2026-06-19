# ADR 003 — A+C 전략 재설계: 광고 성과 분석에서 결제 전환·ML·Agent 플랫폼으로 확장

**날짜**: 2026-06-16
**상태**: 수용(Accepted)
**결정자**: Yeon (with Codex, Session 13)

---

## 배경

Phase 4까지 진행한 결과, 프로젝트는 Airflow 수집, Postgres raw 보존, dbt layered mart, Superset 자산, ai_native mart, Text2SQL 평가 질문 초안까지 갖췄다.

하지만 최종 지원 포지션 관점에서는 아래 갭이 남았다.

| 갭 | 현재 상태 | 포트폴리오 영향 |
|---|---|---|
| 데이터 규모 | Instagram Round 1 기준 49 posts | 대규모 ETL·쿼리 최적화 수치가 약함 |
| 핀테크 도메인 | 인플루언서 광고 후보 분석 중심 | LINE Pay 결제/ROAS 맥락과 거리가 있음 |
| ML 모델 | 없음 | Data Scientist 역량 증명이 약함 |
| Agent | eval YAML 초안만 있음 | Text2SQL 실행 정확도 수치가 없음 |
| API 서빙 | 없음 | 데이터 서빙/API 연동 경험 증명이 약함 |

---

## 결정

기존 구현을 폐기하지 않고, **A+C 전략**으로 확장한다.

- **A: 기존 데이터 플랫폼 축 유지**
  - Apify Instagram 수집
  - raw → staging → intermediate → marts → ai_native dbt 5레이어
  - Superset과 Text2SQL Agent가 읽는 분석 마트
- **C: 결제 전환·ML·Agent 축 추가**
  - 가설 기반 합성 결제 이벤트 생성
  - campaign ROI / payment conversion mart 확장
  - LightGBM ROAS 예측 모델
  - Text2SQL Agent v1/v2/v3와 Execution Accuracy 비교
  - FastAPI `/query`, `/predict` 엔드포인트

새 프로젝트 피치는 다음으로 고정한다.

> "인플루언서 광고 집행부터 결제 전환까지 추적하는 멀티도메인 AI-Native 분석 플랫폼. 운영 등급 Apify 자동화 파이프라인, dbt 5레이어 데이터 마트, ROAS 예측 LightGBM 모델, Text2SQL BI Agent를 포함."

---

## 실행 순서

| Phase | 목적 | 핵심 산출물 |
|---|---|---|
| P | 방향 재정렬 | `CLAUDE.md`, `README.md`, blueprint, ADR 003 |
| 2B | 운영 등급 Apify 자동화 | watermark, freshness check, backfill DAG |
| 2C | 합성 결제 데이터 | creators/campaigns/post metrics/payment events |
| 3B | dbt 확장 | campaign ROI, payment conversion, ML feature store |
| 4B | ROAS 예측 ML | LightGBM, Walk-forward CV, RMSE/MAE |
| 5B | Text2SQL Agent | v1/v2/v3 Exec Acc 비교 |
| 6B | API 서빙 | FastAPI `/query`, `/predict` |
| 7B | BI + 성능 | Superset 3종, EXPLAIN Before/After |
| 8B | CI/CD | dbt CI, ruff/sqlfluff |
| 9B | 데모 준비 | 토크포인트, 데모 영상, README 최종화 |

---

## 근거

| 선택 | 이유 |
|---|---|
| 기존 Phase 0~3 유지 | 이미 dbt lineage, Superset export, ai_native metadata가 포트폴리오 자산으로 쌓였고 재사용 가능하다. |
| 결제 전환 합성 데이터 추가 | 실제 결제 데이터는 없지만, 도메인 가설 기반 시뮬레이션으로 핀테크 분석 질문을 만들 수 있다. |
| ROAS 예측 ML 추가 | 단순 BI 프로젝트에서 벗어나 feature engineering, model evaluation, limitation 설명까지 가능해진다. |
| Text2SQL v1/v2/v3 비교 | AI-Native layer와 schema retrieval이 실제로 성능을 개선하는지 Exec Acc 수치로 설명할 수 있다. |
| FastAPI 추가 | 분석 결과를 서비스/API로 노출하는 데이터 플랫폼 엔지니어링 경험을 보여준다. |

---

## 트레이드오프

| 장점 | 단점 |
|---|---|
| LINE Pay 결제·광고 맥락과 연결이 강해짐 | 범위가 커져 7~8주 추가 작업이 필요 |
| ML/Agent/API/BI를 하나의 스토리로 묶을 수 있음 | 작은 단위로 세션 로그와 ADR을 남기지 않으면 흐름이 흩어질 수 있음 |
| 쿼리 최적화와 Exec Acc를 실측 수치로 만들 수 있음 | 합성 데이터의 가정과 한계를 문서화해야 함 |

---

## AWS 대응 관계

로컬 구현은 아래 AWS managed service와 대응된다.

| 로컬 구현 | AWS 대응 | 차이 |
|---|---|---|
| Airflow Docker | MWAA | 로컬은 운영형 SLA/알림/권한 분리가 없음 |
| Postgres + pgvector | Aurora PostgreSQL + pgvector 또는 Redshift | 로컬은 단일 노드라 대용량 분산 처리 경험은 제한적 |
| dbt-postgres | dbt on ECS/GitHub Actions + Redshift/Aurora | 로컬은 배포 승인/환경 분리 자동화가 약함 |
| Superset | Amazon QuickSight 또는 self-hosted Superset on ECS | 로컬은 사용자 권한/캐시/알림 운영이 단순화됨 |
| FastAPI | ECS/Fargate 또는 Lambda + API Gateway | 로컬은 오토스케일링과 인증 계층이 없음 |
| LightGBM script | SageMaker Training/Batch Transform | 로컬은 모델 레지스트리와 배포 관리가 없음 |

---

## 결과

Phase P 이후의 공식 다음 작업은 기존 “Phase 4 evaluator 구현”이 아니라, 아래 순서로 변경한다.

1. Phase 2B Apify 운영 등급 자동화 파이프라인
2. Phase 2C 합성 결제 데이터 생성기
3. Phase 3B campaign/payment dbt 모델 확장

기존 `agent/eval/text2sql_questions.yml` 기반 evaluator는 폐기하지 않고 Phase 5B Text2SQL Agent 구현에서 재사용한다.

---

## Known Limitations

- 합성 payment conversion은 실제 LINE Pay 데이터가 아니므로 분포 가정과 한계를 `data_generation/README.md`와 ML 문서에 명시해야 한다.
- 목표 수치(예: Exec Acc 72%, 쿼리 개선율)는 계획값이며 README 최종본에는 실측값만 써야 한다.
- Apify 수집량은 Actor 제한, 비용, Instagram 응답 품질에 따라 달라질 수 있다.
