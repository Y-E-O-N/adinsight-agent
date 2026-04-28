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
    def collect_one_hashtag(hashtag: str = "다이소화장품", k: int=20) -> int:
        """해시태그 1개 수집 후 처음 3건의 핵심 필드를 로그로 출력.

        Returns:
            수집된 게시물 개수 (Airflow UI에 task return으로 표시)
        """
        # import는 task함수 내부에 두는 편이 안전
        # DAG파싱 단계에서 무거운 import가 일어나면 scheduler가 느려진다.
        from data_generation.collectors.apify_hashtag import collect_hashtag

        items = collect_hashtag(hashtag, k)
        print(f"[smoke] hashtag={hashtag} k={k} -> {len(items)}건 수집")

        for i, item in enumerate(items[:3], start=1):
            print(
                f"  [{i}] @{item.get('ownerUsername')} "
                f"likes={item.get('likesCount')} "
                f"caption={(item.get('caption') or '')[:40]!r} "
            )

        return len(items)

    collect_one_hashtag()

# DAG 객체를 모듈 네임스페이스에 노출.
# Airflow scheduler 가 이 줄을 실행해 DAG 인스턴스를 발견한다.
ig_collect_smoke_dag()