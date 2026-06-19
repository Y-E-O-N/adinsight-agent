# Session 08 — 학습 개념 정리 (2026-05-27)

Phase 2 Stage 2 본수집 DAG를 준비하면서 배운 개념을 정리한다.

---

## 1. `k`의 의미

`k`는 해당 해시태그에서 Apify에 요청할 게시물 수다.

```python
{"hashtag": "뷰티", "k": 600}
```

의미:

```text
#뷰티 해시태그로 최근 게시물 600건을 요청한다.
```

실제로는 `collect_hashtag()` 안에서 Apify Actor 입력값 `resultsLimit`에 들어간다.

```python
run_input = {
    "hashtags": [hashtag],
    "resultsLimit": k,
}
```

주의:

```text
k_requested != items_collected 일 수 있다.
```

예를 들어 `k=400`을 요청해도 해시태그 풀이 부족하거나 Apify가 가져올 수 있는 결과가 적으면 실제 수집은 400보다 적을 수 있다.

---

## 2. `load_metrics`

`load_metrics`는 `upsert_posts()`가 Postgres에 적재한 결과 요약이다.

```python
load_metrics = upsert_posts(items, source_hashtag=hashtag)
```

반환 예시:

```python
{
    "inserted": 20,
    "updated": 0,
    "source_links_inserted": 20,
    "total": 20,
}
```

의미:

| key | 의미 |
|---|---|
| `inserted` | `raw.ig_posts`에 새로 들어간 게시물 수 |
| `updated` | 이미 있던 게시물이라 `ON CONFLICT`로 갱신된 수 |
| `source_links_inserted` | `raw.ig_post_sources`에 새로 추가된 lineage 수 |
| `total` | loader가 처리한 item 수 |

---

## 3. `**load_metrics`

`**load_metrics`는 dict를 다른 dict 안에 펼쳐 넣는 Python 문법이다.

```python
metrics = {
    "hashtag": hashtag,
    "k_requested": k,
    "items_collected": len(items),
    **load_metrics,
}
```

결과적으로 아래와 같은 dict가 된다.

```python
{
    "hashtag": "뷰티",
    "k_requested": 600,
    "items_collected": 600,
    "inserted": 580,
    "updated": 20,
    "source_links_inserted": 590,
    "total": 600,
}
```

---

## 4. 왜 Stage 2는 XCom으로 items를 넘기지 않나

Stage 1 smoke는 20건이라 XCom으로 `list[dict]`를 넘겨도 괜찮았다.

Stage 2는 약 2,000건이므로 원본 payload를 XCom에 넣으면 Airflow metadata DB가 불필요하게 커진다.

그래서 이번 DAG는 task 내부에서 바로 처리한다.

```text
collect_and_load_seed
-> collect_hashtag()
-> upsert_posts()
-> metrics dict 반환
```

XCom에는 원본 게시물이 아니라 작은 metrics dict만 저장된다.

---

## 5. 다음 세션 시작 체크

본수집은 아직 실행하지 않았다. 다음 세션에서는 먼저 DAG 등록과 기준 row count를 확인한다.

```bash
docker compose exec airflow-webserver airflow dags list | grep ig_collect_round1
docker compose exec postgres psql -U postgres -d adinsight -c "SELECT COUNT(*) FROM raw.ig_posts;"
```

그 다음 비용 상한을 확인하고 `ig_collect_round1` 실행 여부를 결정한다.
