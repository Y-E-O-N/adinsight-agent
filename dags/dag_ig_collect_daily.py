"""
Phase 2B - Instagram daily collection DAG

목적:
    - 합의된 seed 3개를 매일 정기 수집한다.
    - 수집 결과를 raw.ig_posts / raw.ig_post_sources에 멱등 적재한다.
    - freshness check로 오늘 수집량 이상 여부를 확인한다.
    - Airflow Variable에 마지막 수집 완료 날짜(watermark)를 기록한다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task

CANDIDATE_HASHTAGS = (
    "뷰티",
    "올리브영",
    "다이소화장품",
    "올영세일",
    "올영",
    "올영추천템",
    "올영세일추천템",
    "k뷰티",
    "뷰티팁",
    "뷰티꿀팁",
    "기초화장품",
    "메이크업",
    "꾸안꾸",
    "grwm",
    "ootd",
    "코덕",
    "뷰티릴스",
    "여자공감",
    "일상공감",
    "제품리뷰",
    "솔직리뷰",
    "화장품추천",
    "요즘유행",
    "요즘대세",
    "요즘취미",
    "유행",
    "네이버쇼핑",
    "요즘패션",
    "소확행",
    "트렌드",
)

# 운영 비용/Apify 사용량 제어를 위해 daily DAG는 전체 후보 중 일부만 활성화한다.
ACTIVE_CANDIDATE_HASHTAGS = (
    "뷰티",
    "올리브영",
)

MIN_K = 25
DEFAULT_K = 50
MAX_K_PER_HASHTAG = 200
K_STEP = 25
DAILY_K_BUDGET_PER_HASHTAG = 100
DAILY_K_BUDGET = DAILY_K_BUDGET_PER_HASHTAG * len(ACTIVE_CANDIDATE_HASHTAGS)

@dag(
    dag_id="ig_collect_daily",
    description="Phase 2B: Instagram daily collect with freshness and watermark",
    schedule="0 21 * * *",
    start_date=datetime(2026, 6, 16),
    catchup=False,
    tags=["phase2", "stage2b", "apify", "daily", "raw"],
)
def ig_collect_daily_dag() -> None:
    """Daily seed를 수집하고 운영 체크를 수행한다"""

    @task
    def log_watermark() -> str | None:
        """현재 watermark를 로그로 남긴다"""
        from dags.common.ig_collect_utils import get_watermark

        watermark = get_watermark(default=None)
        print(f"[daily] current watermark={watermark}")
        return watermark

    @task
    def build_seed_plan() -> list[dict[str, int | str]]:
        """직전 수집 결과를 보고 해시태그별 요청량 k를 조절한다."""
        import os

        import psycopg

        dsn = (
            f"host={os.environ.get('POSTGRES_HOST', 'postgres')} "
            f"port={os.environ.get('POSTGRES_PORT', '5432')} "
            f"dbname={os.environ['POSTGRES_DB']} "
            f"user={os.environ['POSTGRES_USER']} "
            f"password={os.environ['POSTGRES_PASSWORD']}"
        )
        sql = """
            SELECT source_hashtag, COUNT(*) AS source_rows
            FROM raw.ig_post_sources
            WHERE source_hashtag = ANY(%s)
            GROUP BY source_hashtag
        """

        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (list(ACTIVE_CANDIDATE_HASHTAGS),))
                rows = cur.fetchall()

        source_rows_by_hashtag = {row[0]: int(row[1]) for row in rows}
        latest_seed_metrics_by_hashtag: dict[str, dict[str, int | str]] = {}
        metrics_path = Path("/opt/airflow/metrics/run_results.jsonl")

        if metrics_path.exists():
            with metrics_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if (
                        record.get("dag_id") != "ig_collect_daily"
                        or record.get("step") != "daily_collect_with_freshness"
                    ):
                        continue

                    latest_seed_metrics_by_hashtag = {
                        seed["hashtag"]: seed
                        for seed in record.get("seeds", [])
                        if "hashtag" in seed
                    }

        plan = []

        for hashtag in ACTIVE_CANDIDATE_HASHTAGS:
            source_rows = source_rows_by_hashtag.get(hashtag, 0)
            previous_metrics = latest_seed_metrics_by_hashtag.get(hashtag)

            if previous_metrics is None:
                k = DEFAULT_K
                strategy = "explore_new_seed"
            else:
                previous_k = int(previous_metrics["k_requested"])
                previous_items = int(previous_metrics["items_collected"])

                if previous_items >= previous_k:
                    k = min(MAX_K_PER_HASHTAG, previous_k + K_STEP)
                    strategy = "scale_up_full_collection"
                elif previous_k - previous_items > K_STEP:
                    k = max(MIN_K, previous_k - K_STEP)
                    strategy = "scale_down_underfilled_collection"
                else:
                    k = previous_k
                    strategy = "keep_near_full_collection"

            plan.append(
                {
                    "hashtag": hashtag,
                    "k": k,
                    "observed_source_rows": source_rows,
                    "strategy": strategy,
                }
            )

        total_k = sum(int(seed["k"]) for seed in plan)
        while total_k > DAILY_K_BUDGET:
            adjustable_seeds = [seed for seed in plan if int(seed["k"]) > MIN_K]
            if not adjustable_seeds:
                break

            seed_to_reduce = max(
                adjustable_seeds,
                key=lambda seed: (
                    "scale_down" in str(seed["strategy"]),
                    int(seed["k"]),
                    int(seed["observed_source_rows"]),
                ),
            )
            seed_to_reduce["k"] = int(seed_to_reduce["k"]) - K_STEP
            seed_to_reduce["strategy"] = f"{seed_to_reduce['strategy']}_budget_scaled"
            total_k -= K_STEP

        print(f"[daily] seed_plan={plan}")
        return plan

    @task
    def collect_and_load_seed(
        hashtag: str,
        k: int,
        observed_source_rows: int,
        strategy: str,
    ) -> dict[str, int | str]:
        """해시태그 1개를 수집하고 raw 테이블에 바로 적재한다"""
        from data_generation.collectors.apify_hashtag import collect_hashtag
        from data_generation.collectors.loaders.postgres_loader import upsert_posts

        print(
            "[daily] collecting "
            f"hashtag={hashtag!r} k={k} "
            f"observed_source_rows={observed_source_rows} strategy={strategy}"
        )
        items = collect_hashtag(hashtag, k)

        print(f"[daily] collected hashtag={hashtag!r} items={len(items)}")
        load_metrics = upsert_posts(items, source_hashtag=hashtag)

        metrics = {
            "hashtag": hashtag,
            "k_requested": k,
            "items_collected": len(items),
            "observed_source_rows": observed_source_rows,
            "strategy": strategy,
            **load_metrics,
        }

        print(f"[daily] metrics={metrics}")
        return metrics

    @task
    def run_freshness_check() -> dict[str, float | int | str]:
        """오늘 수집량이 운영 기준을 만족하는지 확인한다."""
        from dags.common.ig_collect_utils import check_freshness

        result = check_freshness()
        print(f"[daily] freshness={result}")
        return result

    @task
    def update_watermark() -> str:
        """daily 수집 성공 후 오늘 날짜를 watermark로 기록한다."""
        from datetime import date

        from dags.common.ig_collect_utils import set_watermark

        watermark = set_watermark(date.today())
        print(f"[daily] updated watermark={watermark}")
        return watermark

    @task
    def record_daily_metrics(
        seed_metrics: list[dict[str, int | str]],
        freshness: dict[str, float | int | str],
        watermark: str,
    ) -> dict[str, int | str]:
        """daily 수집/품질 결과를 포트폴리오용 JSONL 메트릭으로 남긴다."""
        seed_metrics = list(seed_metrics)
        metrics_path = Path("/opt/airflow/metrics/run_results.jsonl")
        metrics_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "phase": "p2b",
            "step": "daily_collect_with_freshness",
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dag_id": "ig_collect_daily",
            "seed_count": len(seed_metrics),
            "k_requested_total": sum(int(m["k_requested"]) for m in seed_metrics),
            "items_collected_total": sum(int(m["items_collected"]) for m in seed_metrics),
            "inserted_total": sum(int(m["inserted"]) for m in seed_metrics),
            "updated_total": sum(int(m["updated"]) for m in seed_metrics),
            "source_links_inserted_total": sum(
                int(m["source_links_inserted"]) for m in seed_metrics
            ),
            "freshness": freshness,
            "watermark": watermark,
            "seeds": seed_metrics,
        }

        with metrics_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[daily] recorded metrics={record}")
        return {
            "seed_count": record["seed_count"],
            "items_collected_total": record["items_collected_total"],
            "inserted_total": record["inserted_total"],
            "updated_total": record["updated_total"],
            "watermark": watermark,
        }

    watermark_task = log_watermark()
    seed_plan = build_seed_plan()
    seed_results = collect_and_load_seed.expand_kwargs(seed_plan)

    watermark_task >> seed_plan >> seed_results
    freshness_result = run_freshness_check()
    updated_watermark = update_watermark()
    record_daily_metrics(seed_results, freshness_result, updated_watermark)

    seed_results >> freshness_result >> updated_watermark

ig_collect_daily_dag()
