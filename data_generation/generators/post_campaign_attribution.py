"""Attach synthetic campaigns to real Apify posts using observed engagement."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from data_generation.generators.campaigns import generate_campaigns
from data_generation.generators.generation_profile import (
    SEED,
    SOURCE_HASHTAG_CATEGORY_HINTS,
)

DEFAULT_APIFY_PROFILE_PATH = (
    Path(__file__).resolve().parents[1] / "profiles" / "apify_profile_latest.json"
)


def load_apify_profile(profile_path: Path = DEFAULT_APIFY_PROFILE_PATH) -> dict[str, Any]:
    """Apify 관측 profile JSON을 읽는다."""
    return json.loads(profile_path.read_text(encoding="utf-8"))


def _postgres_dsn() -> str:
    """환경변수로 Postgres 접속 문자열을 만든다."""
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'adinsight')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', 'postgres')}"
    )


def load_recent_apify_posts(limit: int) -> list[dict[str, Any]]:
    """Postgres raw 테이블에서 최근 Apify post를 attribution 입력 형태로 읽는다."""
    import psycopg
    from psycopg.rows import dict_row

    sql = """
        SELECT
            p.id AS post_id,
            p.owner_username AS creator_username,
            p.posted_at,
            p.likes_count,
            p.comments_count,
            s.source_hashtag,
            COALESCE((p.raw_payload->>'paidPartnership')::boolean, false)
                AS paid_partnership_observed
        FROM raw.ig_posts AS p
        LEFT JOIN LATERAL (
            SELECT source_hashtag
            FROM raw.ig_post_sources AS source
            WHERE source.post_id = p.id
            ORDER BY source.collected_at DESC, source.source_hashtag
            LIMIT 1
        ) AS s ON true
        WHERE p.owner_username IS NOT NULL
          AND p.posted_at IS NOT NULL
          AND s.source_hashtag IS NOT NULL
        ORDER BY p.collected_at DESC, p.id
        LIMIT %s
    """

    with psycopg.connect(_postgres_dsn(), row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(row) for row in cur.fetchall()]


def infer_category_from_hashtag(source_hashtag: str) -> str:
    """수집 해시태그에서 synthetic campaign category를 추정한다."""
    return SOURCE_HASHTAG_CATEGORY_HINTS.get(source_hashtag, "beauty")


def clean_likes_count(value: Any) -> tuple[int, bool]:
    """Apify likes_count의 hidden marker(-1)를 0과 flag로 분리한다."""
    if value is None:
        return 0, False

    likes_count = int(value)
    if likes_count < 0:
        return 0, True

    return likes_count, False


def safe_comments_count(value: Any) -> int:
    """댓글 수를 0 이상 정수로 보정한다."""
    if value is None:
        return 0
    return max(0, int(value))


def engagement_thresholds_from_profile(profile: dict[str, Any]) -> dict[str, int]:
    """Apify profile의 engagement_count percentiles를 tier 기준으로 변환한다."""
    labels = profile["percentiles"]["percentile_labels"]
    values = profile["percentiles"]["engagement_count_percentiles"]
    percentile_map = dict(zip(labels, values, strict=True))

    return {
        "medium_min": int(percentile_map["p50"]),
        "high_min": int(percentile_map["p75"]),
        "viral_min": int(percentile_map["p90"]),
    }


def classify_engagement_tier(
    engagement_count: int,
    thresholds: dict[str, int],
) -> str:
    """관측 engagement_count를 low/medium/high/viral tier로 분류한다."""
    if engagement_count >= thresholds["viral_min"]:
        return "viral"
    if engagement_count >= thresholds["high_min"]:
        return "high"
    if engagement_count >= thresholds["medium_min"]:
        return "medium"
    return "low"


def _choose_campaign(
    rng: np.random.Generator,
    campaigns: list[dict[str, Any]],
    category: str,
) -> dict[str, Any]:
    matching_campaigns = [
        campaign for campaign in campaigns if campaign["category"] == category
    ]
    return dict(rng.choice(matching_campaigns or campaigns))


def enrich_posts_with_campaign_attribution(
    rng: np.random.Generator,
    posts: list[dict[str, Any]],
    campaigns: list[dict[str, Any]],
    apify_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """실제 Apify post에 synthetic campaign attribution을 붙인다."""
    thresholds = engagement_thresholds_from_profile(apify_profile)
    attributed_posts = []

    for index, post in enumerate(posts):
        source_hashtag = str(post["source_hashtag"])
        category = infer_category_from_hashtag(source_hashtag)
        campaign = _choose_campaign(rng=rng, campaigns=campaigns, category=category)

        likes_count_clean, likes_hidden = clean_likes_count(post.get("likes_count"))
        comments_count = safe_comments_count(post.get("comments_count"))
        engagement_count = likes_count_clean + comments_count
        engagement_tier = classify_engagement_tier(
            engagement_count=engagement_count,
            thresholds=thresholds,
        )

        attributed_posts.append(
            {
                "post_campaign_attribution_id": f"postattr_{index:07d}",
                "post_id": post["post_id"],
                "creator_username": post["creator_username"],
                "campaign_id": campaign["campaign_id"],
                "post_date": str(post["posted_at"])[:10],
                "source_hashtag": source_hashtag,
                "category": category,
                "likes_count_clean": likes_count_clean,
                "likes_hidden": likes_hidden,
                "comments_count": comments_count,
                "observed_engagement_count": engagement_count,
                "observed_engagement_tier": engagement_tier,
                "paid_partnership_observed": bool(
                    post.get("paid_partnership_observed", False)
                ),
                "metric_policy": "observed_likes_comments_only_v1",
                "synthetic_source": "real_post_campaign_attribution_v1",
            }
        )

    return attributed_posts


def _sample_posts() -> list[dict[str, Any]]:
    return [
        {
            "post_id": "3921832188514966508",
            "creator_username": "bruce_naver",
            "posted_at": "2026-06-17T23:27:35+00:00",
            "likes_count": 12,
            "comments_count": 0,
            "source_hashtag": "네이버쇼핑",
            "paid_partnership_observed": False,
        },
        {
            "post_id": "3914805038690812663",
            "creator_username": "l._.star",
            "posted_at": "2026-06-05T12:00:00+00:00",
            "likes_count": -1,
            "comments_count": 37,
            "source_hashtag": "뷰티",
            "paid_partnership_observed": True,
        },
        {
            "post_id": "3903059314819618546",
            "creator_username": "yeti__st",
            "posted_at": "2026-05-20T12:00:00+00:00",
            "likes_count": 741,
            "comments_count": 47,
            "source_hashtag": "다이소화장품",
            "paid_partnership_observed": True,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attach synthetic campaign attribution to observed Apify posts."
    )
    parser.add_argument(
        "--from-postgres",
        action="store_true",
        help="Read observed posts from raw.ig_posts instead of built-in samples.",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--campaign-count", type=int, default=20)
    parser.add_argument(
        "--write-postgres",
        action="store_true",
        help="Persist generated attribution rows into raw.syn_post_campaign_attributions.",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)
    profile = load_apify_profile()
    campaigns = generate_campaigns(
        rng=rng,
        count=args.campaign_count,
        base_date=date(2026, 6, 16),
    )
    posts = load_recent_apify_posts(limit=args.limit) if args.from_postgres else _sample_posts()

    attributed = enrich_posts_with_campaign_attribution(
        rng=rng,
        posts=posts,
        campaigns=campaigns,
        apify_profile=profile,
    )
    load_metrics = None
    if args.write_postgres:
        from data_generation.collectors.loaders.synthetic_loader import (
            upsert_post_campaign_attributions,
        )

        load_metrics = upsert_post_campaign_attributions(attributed)

    print(
        json.dumps(
            {
                "attribution_count": len(attributed),
                "input_mode": "postgres" if args.from_postgres else "sample",
                "load_metrics": load_metrics,
                "engagement_thresholds": engagement_thresholds_from_profile(profile),
                "attributed_posts": attributed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
