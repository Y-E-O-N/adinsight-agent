# AdInsight Agent - 이력서 최종 Bullet

한국 데이터 엔지니어 지원서에는 아래 4개 bullet을 우선 사용합니다. 너무 많은 세부 기술을 한 줄에 넣기보다, `문제/행동/결과`가 보이도록 구성했습니다.

## 최종 4개 Bullet

- Airflow, PostgreSQL, dbt 기반으로 Instagram 수집 데이터와 합성 결제 이벤트를 `raw -> staging -> intermediate -> marts -> features -> ai_native` 레이어로 모델링하고, campaign ROI/ROAS 분석 플랫폼을 구축했습니다.
- Apify 수집, raw loader, daily/backfill DAG, dbt run/test를 연결해 수집-적재-변환 파이프라인을 구성했으며, daily adaptive run 1회에서 `1,725`건 수집과 `1,410`건 신규 적재를 기록했습니다.
- Campaign ROI mart와 ROAS prediction monitor를 구축하고, leave-one-out model comparison을 통해 baseline MAE `0.0892` 대비 linear model MAE `0.0474`의 benchmark artifact를 FastAPI로 서빙했습니다.
- Text2SQL v2에 SQL validator, statement timeout, audit log, provider cost/latency tracking, Gemini -> OpenAI fallback을 구현하고, 24개 정답형 질의와 14개 안전성 질의 기준으로 provider 평가를 수행했습니다.

## 짧은 프로젝트 설명

인플루언서 광고 수집 데이터와 합성 결제 이벤트를 Airflow, PostgreSQL, dbt, Superset, FastAPI로 연결해 campaign ROI/ROAS 분석 플랫폼을 구축했습니다. ROAS model artifact serving과 guarded Text2SQL API를 구현하고, provider fallback과 request-level cost/latency observability까지 평가했습니다.

## 기술 스택

Python, SQL, Airflow, PostgreSQL, dbt, Superset, FastAPI, GitHub Actions, ruff, pytest, OpenAI/Gemini gateway, Text2SQL validator/eval framework

## 사용 시 주의

- 이력서 본문에는 `synthetic payment benchmark`라는 표현을 남겨 실제 결제 데이터처럼 보이지 않게 합니다.
- ROAS model 수치는 production 성능이 아니라 synthetic benchmark 기반 model comparison 결과로 설명합니다.
- AWS는 실제 배포가 아니라 target architecture mapping으로 설명합니다.
