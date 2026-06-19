"""Stage 0 smoke DAG — Apify Instagram 해시태그 수집 1회 실행.

목적:
    - apify-client 라이브러리가 worker 컨테이너에서 동작하는가
    - APIFY_TOKEN 이 컨테이너 환경변수로 주입됐는가
    - data_generation 패키지가 마운트·import 가능한가
    위 셋을 한 번에 검증.
"""

from __future__ import annotations

from datetime import datetime
from airflow.decorators import dag, task


@dag(
    dag_id="ig_collect_smoke",
    description="Stage 0: Apify Instagram hashtag collect smoke (once manual trigger)",
    schedule=None,
    start_date=datetime(2026, 4, 28),
    catchup=False,
    tags=["phase2", "smoke", "apify"],
)
def ig_collect_smoke_dag() -> None:
    """Smoke DAG 정의"""

    @task
    def collect_one_hashtag(hashtag: str = "다이소화장품", k: int=20) -> list[dict]:
        """해시태그 1개 수집하고 게시물 원본 리스트를 반환. """
        from data_generation.collectors.apify_hashtag import collect_hashtag

        items = collect_hashtag(hashtag, k)
        print(f"[collect] hashtag={hashtag} k={k} -> {len(items)}건 수집")

        for i, item in enumerate(items[:3], start=1):
            print(
                f"  [{i}] @{item.get('ownerUsername')} "
                f"likes={item.get('likesCount')} "
                f"caption={(item.get('caption') or '')[:40]!r} "
            )

        return items

    @task
    def load_posts(items: list[dict], source_hashtag: str = "다이소화장품") -> dict[str, int]:
        """수집된 게시물을 raw.ig_posts / raw.ig_post_sources에 멱등 적재. """
        from data_generation.collectors.loaders.postgres_loader import upsert_posts

        metrics = upsert_posts(items, source_hashtag=source_hashtag)
        print(f"[load] metrics={metrics}")
        return metrics

    items = collect_one_hashtag()
    load_posts(items)

# DAG 객체를 모듈 네임스페이스에 노출.
# Airflow scheduler 가 이 줄을 실행해 DAG 인스턴스를 발견한다.
ig_collect_smoke_dag()