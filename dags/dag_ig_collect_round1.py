"""
Phase 2 Stage 2 - Instagram Round 1 본수집 DAG

목적:
    - 합의된 seed 3개를 Apify로 수집한다
    - 수집 결과를 즉시 raw.ig_posts / raw.ig_post_sources에 적재한다.
    - 큰 payload를 XCom에 저장하지 않고 seed별 metrics만 반환한다
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task

ROUND1_SEEDS = (
    {"hashtag": "뷰티", "k": 600},
    {"hashtag": "올리브영", "k": 1000},
    {"hashtag": "다이소화장품", "k": 400},
)

@dag(
    dag_id="ig_collect_round1",
    description="Phase 2 Stage 2: Instagram Round 1 collect and raw load",
    schedule=None,
    start_date=datetime(2026, 5, 27),
    catchup=False,
    tags=["phase2", "stage2", "apify", "raw"],
)
def ig_collect_round1_dag() -> None:
    """Round 1 seed 3개를 수집하고 raw 테이블에 멱등 적재한다. """

    @task
    def collect_and_load_seed(hashtag: str, k: int) -> dict[str, int | str]:
        """해시태그 1개를 수집하고 raw 테이블에 바로 적재한다."""
        from data_generation.collectors.apify_hashtag import collect_hashtag
        from data_generation.collectors.loaders.postgres_loader import upsert_posts

        print(f"[round1] collecting hashtag={hashtag!r} k={k}")
        items = collect_hashtag(hashtag, k)

        print(f"[round1] collected hashtag={hashtag!r} items={len(items)}")
        load_metrics = upsert_posts(items, source_hashtag=hashtag)

        metrics = {
            "hashtag": hashtag,
            "k_requested": k,
            "items_collected": len(items),
            **load_metrics,
        }
            #   **load_metrics는 dict를 펼쳐 넣는 문법입니다.
            #   즉 아래와 같습니다.
            # metrics = {
            #     "hashtag": hashtag,
            #     "k_requested": k,
            #     "items_collected": len(items),
            #     "inserted": 20,
            #     "updated": 0,
            #     "source_links_inserted": 20,
            #     "total": 20,
            # }
        print(f"[round1] metrics={metrics}")
        return metrics

    @task
    def record_round1_metrics(seed_metrics: list[dict[str, int | str]]) -> dict[str, int | str]:
        """seed별 수집/적재 결과를 포트폴리오용 JSONL 메트릭으로 남긴다."""
        metrics_path = Path("/opt/airflow/metrics/run_results.jsonl")
        metrics_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "phase": "p2",
            "step": "stage2_round1_collect",
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dag_id": "ig_collect_round1",
            "seed_count": len(seed_metrics),
            "k_requested_total": sum(int(m["k_requested"]) for m in seed_metrics),
            "items_collected_total": sum(int(m["items_collected"]) for m in seed_metrics),
            "inserted_total": sum(int(m["inserted"]) for m in seed_metrics),
            "updated_total": sum(int(m["updated"]) for m in seed_metrics),
            "source_links_inserted_total": sum(
                int(m["source_links_inserted"]) for m in seed_metrics
            ),
            "seeds": seed_metrics,
        }

        with metrics_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[round1] recorded metrics={record}")
        return {
            "seed_count": record["seed_count"],
            "items_collected_total": record["items_collected_total"],
            "inserted_total": record["inserted_total"],
            "updated_total": record["updated_total"],
        }

    seed_results = []
    for seed in ROUND1_SEEDS:
        seed_results.append(
            collect_and_load_seed(
                hashtag=seed["hashtag"],
                k=seed["k"],
            )
        )
#     TaskFlow API에서는 이 반복문이 DAG 파싱 시점에 task 3개를 만듭니다. 실행 시점에
#       for문이 도는 게 아니라, Airflow가 “seed별 task 3개”를 등록합니다.

    record_round1_metrics(seed_results)

ig_collect_round1_dag()



# ---------------------------------------------------

#   1. 큰 payload는 XCom으로 넘기지 않는다
#   2. Airflow task는 실패 단위가 되므로 seed별로 나눈다
#   3. 본수집 전 비용 상한과 metrics 기록 방식을 정한다

#  목표 구조:

#   ig_collect_round1
#   ├── collect_and_load_seed("뷰티", 600)
#   ├── collect_and_load_seed("올리브영", 1000)
#   └── collect_and_load_seed("다이소화장품", 400)

#   이번에는 XCom으로 게시물 리스트를 넘기지 않습니다. 각 task 안에서 바로:

#   collect_hashtag()
#   -> upsert_posts()
#   -> metrics dict 반환

#   즉 XCom에는 큰 원본 payload가 아니라 이런 작은 dict만 저장됩니다.

#   {
#       "hashtag": "뷰티",
#       "k_requested": 600,
#       "items_collected": 600,
#       "inserted": 580,
#       "updated": 20,
#       "source_links_inserted": 590,
#       "total": 600,
#   }
