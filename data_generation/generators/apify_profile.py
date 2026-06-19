"""Build an observed profile from Apify Instagram raw tables."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "profiles" / "apify_profile_latest.json"
)


def _postgres_dsn() -> str:
    """환경변수로 Postgres 접속 문자열을 만든다."""
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'adinsight')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', 'postgres')}"
    )


def _json_default(value: Any) -> str:
    if isinstance(value, datetime | date):
        return value.isoformat()
    return str(value)


def build_apify_profile() -> dict[str, Any]:
    """raw.ig_posts / raw.ig_post_sources의 관측 분포를 계산한다."""
    with psycopg.connect(_postgres_dsn(), row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT
                    COUNT(*) AS raw_posts,
                    COUNT(*) FILTER (WHERE likes_count IS NOT NULL) AS likes_present,
                    COUNT(*) FILTER (WHERE likes_count = -1) AS likes_hidden,
                    COUNT(*) FILTER (WHERE comments_count IS NOT NULL) AS comments_present,
                    MIN(posted_at) AS min_posted_at,
                    MAX(posted_at) AS max_posted_at
                FROM raw.ig_posts
                """
        )
        overview = dict(cur.fetchone() or {})

        cur.execute(
            """
                SELECT
                    percentile_disc(ARRAY[0.25, 0.5, 0.75, 0.9, 0.99])
                        WITHIN GROUP (ORDER BY NULLIF(likes_count, -1))
                        AS likes_percentiles,
                    percentile_disc(ARRAY[0.25, 0.5, 0.75, 0.9, 0.99])
                        WITHIN GROUP (ORDER BY comments_count)
                        AS comments_percentiles
                FROM raw.ig_posts
                """
        )
        percentiles = dict(cur.fetchone() or {})

        cur.execute(
            """
                WITH base AS (
                    SELECT
                        GREATEST(COALESCE(NULLIF(likes_count, -1), 0), 0)
                            + COALESCE(comments_count, 0) AS engagement_count
                    FROM raw.ig_posts
                )
                SELECT
                    percentile_disc(ARRAY[0.25, 0.5, 0.75, 0.9, 0.99])
                        WITHIN GROUP (ORDER BY engagement_count)
                        AS engagement_count_percentiles,
                    MIN(engagement_count) AS min_engagement_count,
                    MAX(engagement_count) AS max_engagement_count,
                    AVG(engagement_count)::numeric(10, 2) AS avg_engagement_count
                FROM base
                """
        )
        engagement_distribution = dict(cur.fetchone() or {})

        cur.execute(
            """
                SELECT post_type, product_type, COUNT(*) AS posts
                FROM raw.ig_posts
                GROUP BY 1, 2
                ORDER BY posts DESC, post_type, product_type
                """
        )
        post_type_distribution = [dict(row) for row in cur.fetchall()]

        cur.execute(
            """
                SELECT source_hashtag, COUNT(*) AS source_rows
                FROM raw.ig_post_sources
                GROUP BY 1
                ORDER BY source_rows DESC, source_hashtag
                """
        )
        source_hashtag_distribution = [dict(row) for row in cur.fetchall()]

        cur.execute(
            """
                SELECT
                    COUNT(*) FILTER (WHERE raw_payload ? 'videoViewCount')
                        AS video_view_count_rows,
                    COUNT(*) FILTER (WHERE raw_payload ? 'viewCount')
                        AS view_count_rows,
                    COUNT(*) FILTER (WHERE raw_payload ? 'viewsCount')
                        AS views_count_rows,
                    COUNT(*) FILTER (WHERE raw_payload ? 'impressions')
                        AS impressions_rows,
                    COUNT(*) FILTER (WHERE raw_payload ? 'paidPartnership')
                        AS paid_partnership_key_rows,
                    COUNT(*) FILTER (
                        WHERE COALESCE((raw_payload->>'paidPartnership')::boolean, false)
                    ) AS paid_partnership_true_rows
                FROM raw.ig_posts
                """
        )
        field_availability = dict(cur.fetchone() or {})

        cur.execute(
            """
                SELECT key, COUNT(*) AS rows_with_key
                FROM raw.ig_posts
                CROSS JOIN LATERAL jsonb_object_keys(raw_payload) AS key
                GROUP BY key
                ORDER BY rows_with_key DESC, key
                """
        )
        raw_payload_keys = [dict(row) for row in cur.fetchall()]

    return {
        "generated_at": datetime.now().astimezone(),
        "source": "raw.ig_posts + raw.ig_post_sources",
        "overview": overview,
        "percentiles": {
            "percentile_labels": ["p25", "p50", "p75", "p90", "p99"],
            **percentiles,
            **engagement_distribution,
        },
        "post_type_distribution": post_type_distribution,
        "source_hashtag_distribution": source_hashtag_distribution,
        "field_availability": field_availability,
        "raw_payload_keys": raw_payload_keys,
        "recommended_metric_policy": {
            "use_views": False,
            "use_impressions": False,
            "reason": (
                "Current Apify payload has videoViewCount only for a tiny subset "
                "and has no stable viewCount/viewsCount/impressions fields."
            ),
            "primary_observed_signals": [
                "likes_count",
                "comments_count",
                "post_type",
                "product_type",
                "source_hashtag",
                "paidPartnership",
            ],
        },
    }


def write_apify_profile(output_path: Path = DEFAULT_OUTPUT_PATH) -> dict[str, Any]:
    """관측 profile을 JSON 파일로 저장한다."""
    profile = build_apify_profile()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return profile


if __name__ == "__main__":
    written_profile = write_apify_profile()
    print(
        json.dumps(
            {
                "output_path": str(DEFAULT_OUTPUT_PATH),
                "raw_posts": written_profile["overview"]["raw_posts"],
                "metric_policy": written_profile["recommended_metric_policy"],
            },
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        )
    )
