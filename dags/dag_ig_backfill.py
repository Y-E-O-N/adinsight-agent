"""
Phase 2B - Instagram backfill collection DAG

목적:
    - daily DAG 실패나 누락이 있을 때 수동으로 해시태그 수집을 보강한다.
    - raw.ig_posts / raw.ig_post_sources에 멱등 적재한다.
    - watermark는 변경하지 않는다.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.python import get_current_context

DEFAULT_BACKFILL_HASHTAGS = ("뷰티", "올리브영", "다이소화장품")
DEFAULT_BACKFILL_K = 25
MIN_BACKFILL_K = 1
MAX_BACKFILL_K = 200


@dag(
    dag_id="ig_collect_backfill",
    description="Phase 2B: Manual Instagram backfill collect and raw load",
    schedule=None,
    start_date=datetime(2026, 6, 16),
    catchup=False,
    max_active_tasks=4,
    params={
        "target_date": Param(str(date.today()), type="string"),
        "hashtags": Param(list(DEFAULT_BACKFILL_HASHTAGS), type="array"),
        "k": Param(DEFAULT_BACKFILL_K, type="integer", minimum=MIN_BACKFILL_K),
        "reason": Param("manual_backfill", type="string"),
    },
    tags=["phase2", "stage2b", "apify", "backfill", "raw"],
)
def ig_collect_backfill_dag() -> None:
    """수동 backfill 요청을 seed별 task로 나눠 수집한다."""

    @task
    def build_backfill_plan() -> list[dict[str, int | str]]:
        """dag_run.conf 또는 Params로 받은 backfill 요청을 seed 계획으로 변환한다."""
        context = get_current_context()
        params = context["params"]
        dag_run = context.get("dag_run")
        conf: dict[str, Any] = dag_run.conf or {} if dag_run else {}

        target_date = str(conf.get("target_date", params["target_date"]))
        raw_hashtags = conf.get("hashtags", conf.get("seeds", params["hashtags"]))
        k = int(conf.get("k", params["k"]))
        reason = str(conf.get("reason", params["reason"]))

        if isinstance(raw_hashtags, str):
            hashtags = [
                hashtag.strip().lstrip("#")
                for hashtag in raw_hashtags.split(",")
                if hashtag.strip()
            ]
        else:
            hashtags = [
                str(hashtag).strip().lstrip("#")
                for hashtag in raw_hashtags
                if str(hashtag).strip()
            ]

        if not hashtags:
            raise ValueError("backfill hashtags must not be empty")

        if k < MIN_BACKFILL_K or k > MAX_BACKFILL_K:
            raise ValueError(
                f"backfill k must be between {MIN_BACKFILL_K} and {MAX_BACKFILL_K}: {k}"
            )

        plan = [
            {
                "hashtag": hashtag,
                "k": k,
                "target_date": target_date,
                "reason": reason,
            }
            for hashtag in hashtags
        ]

        print(
            "[backfill] target_date is metadata only; "
            "current collector fetches latest hashtag posts."
        )
        print(f"[backfill] seed_plan={plan}")
        return plan

    @task
    def collect_and_load_seed(
        hashtag: str,
        k: int,
        target_date: str,
        reason: str,
    ) -> dict[str, int | str]:
        """해시태그 1개를 수집하고 raw 테이블에 멱등 적재한다."""
        from data_generation.collectors.apify_hashtag import collect_hashtag
        from data_generation.collectors.loaders.postgres_loader import upsert_posts

        print(
            "[backfill] collecting "
            f"hashtag={hashtag!r} k={k} target_date={target_date} reason={reason!r}"
        )
        items = collect_hashtag(hashtag, k)

        print(f"[backfill] collected hashtag={hashtag!r} items={len(items)}")
        load_metrics = upsert_posts(items, source_hashtag=hashtag)

        metrics = {
            "hashtag": hashtag,
            "k_requested": k,
            "items_collected": len(items),
            "target_date": target_date,
            "reason": reason,
            **load_metrics,
        }

        print(f"[backfill] metrics={metrics}")
        return metrics

    @task
    def record_backfill_metrics(
        seed_metrics: list[dict[str, int | str]],
    ) -> dict[str, int | str]:
        """backfill 결과를 포트폴리오용 JSONL 메트릭으로 남긴다."""
        seed_metrics = list(seed_metrics)
        metrics_path = Path("/opt/airflow/metrics/run_results.jsonl")
        metrics_path.parent.mkdir(parents=True, exist_ok=True)

        target_dates = sorted({str(m["target_date"]) for m in seed_metrics})
        reasons = sorted({str(m["reason"]) for m in seed_metrics})
        record = {
            "phase": "p2b",
            "step": "manual_backfill_collect",
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dag_id": "ig_collect_backfill",
            "seed_count": len(seed_metrics),
            "k_requested_total": sum(int(m["k_requested"]) for m in seed_metrics),
            "items_collected_total": sum(int(m["items_collected"]) for m in seed_metrics),
            "inserted_total": sum(int(m["inserted"]) for m in seed_metrics),
            "updated_total": sum(int(m["updated"]) for m in seed_metrics),
            "source_links_inserted_total": sum(
                int(m["source_links_inserted"]) for m in seed_metrics
            ),
            "target_dates": target_dates,
            "reasons": reasons,
            "collector_date_filter": "not_supported_currently",
            "seeds": seed_metrics,
        }

        with metrics_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[backfill] recorded metrics={record}")
        return {
            "seed_count": record["seed_count"],
            "items_collected_total": record["items_collected_total"],
            "inserted_total": record["inserted_total"],
            "updated_total": record["updated_total"],
        }

    seed_plan = build_backfill_plan()
    seed_results = collect_and_load_seed.expand_kwargs(seed_plan)
    record_backfill_metrics(seed_results)


ig_collect_backfill_dag()
