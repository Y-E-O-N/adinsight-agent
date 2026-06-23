# Session 18 Concepts — Text2SQL Campaign Eval Expansion

## 1. Expected SQL benchmark

Text2SQL Agent를 만들기 전에 자연어 질문과 “정답 SQL”을 먼저 묶어두는 평가 방식이다.

이번 프로젝트에서는 `agent/eval/text2sql_questions.yml`이 benchmark input이고, `agent/eval/run_expected_sql.py`가 각 expected SQL을 실행해 row count가 문서화된 기준선과 맞는지 확인한다.

이 단계의 목적은 LLM 성능 측정이 아니라 아래를 먼저 고정하는 것이다.

- 어떤 자연어 질문을 지원할 것인가
- 어떤 table을 선택해야 하는가
- 어떤 column과 filter/order/group by가 정답에 가까운가
- 현재 데이터에서 정답 SQL이 실행 가능한가

## 2. Snapshot-aware evaluation

`marts.mart_campaign_roas_prediction_monitor`는 daily DAG가 실행될 때마다 prediction snapshot이 누적되는 table이다.

그래서 아래처럼 그냥 전체 table을 세면 날짜가 지날수록 row count가 증가한다.

```sql
select count(*)
from marts.mart_campaign_roas_prediction_monitor;
```

Text2SQL 평가셋에서는 row count가 안정적이어야 하므로 “최신 예측” 질문에 아래 조건을 넣었다.

```sql
where scoring_snapshot_date = (
    select max(scoring_snapshot_date)
    from marts.mart_campaign_roas_prediction_monitor
)
```

이렇게 하면 snapshot이 여러 날 쌓여도 evaluator는 항상 최신 snapshot 1일치만 기준으로 본다.

## 3. Stale baseline

baseline은 “기준선”이라는 뜻이다. 이번 세션에서는 `current_result_rows`가 expected SQL의 row count baseline 역할을 한다.

기존 p4 creator 질문은 2026-06-11 데이터 기준으로 작성되었다. 이후 daily Apify collection이 계속 실행되면서 creator mart rows가 늘었고, 일부 질문의 row count가 크게 바뀌었다.

따라서 아래 현상은 코드 오류가 아니라 기준선이 오래된 문제였다.

- `p4_q002`: 21 rows에서 758 rows로 증가
- `p4_q006`: 24 rows에서 1159 rows로 증가
- `p4_q009`: 44 rows에서 2694 rows로 증가

운영 데이터가 계속 바뀌는 프로젝트에서는 “테스트가 실패했다”와 “테스트 기준선이 stale하다”를 구분해야 한다.

## 4. Next concept to learn

다음 단계가 ROAS ML model v1이면 아래 개념을 이어서 보면 된다.

- train/test split
- baseline model vs regression model
- MAE/RMSE/bias
- feature leakage
- model run metadata

