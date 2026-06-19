"""
    Stage 1: Apify 수집 결과를 raw.ig_posts에 멱등 적재.
    순수 함수 형태로 제공 - 로컬 CLI / Airflow DAG 양쪽 재사용.
"""
from __future__ import annotations

import json
import os
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

# raw.ig_posts의 INSERT 컬럼 순서 (placeholder 순서와 일치해야함)
_COLUMNS = (
    "id", "short_code", "url",
    "post_type", "product_type",
    "caption", "comments_count", "likes_count", "posted_at",
    "owner_username", "owner_full_name", "owner_id",
    "display_url", "images", "child_posts", "music_info",
    "raw_payload",
)

_UPDATABLE = (
    "short_code", "url", "post_type", "product_type",
    "caption", "comments_count", "likes_count", "posted_at",
    "owner_username", "owner_full_name", "owner_id",
    "display_url", "images", "child_posts", "music_info",
    "raw_payload",
)

_INSERT_SQL = f"""
INSERT INTO raw.ig_posts ({", ".join(_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_COLUMNS))})
ON CONFLICT (id) DO UPDATE SET
    {", ".join(f"{c} = EXCLUDED.{c}" for c in _UPDATABLE)},
    updated_at = now()
RETURNING (xmax = 0) AS inserted;
"""

_INSERT_SOURCE_SQL = f"""
INSERT INTO raw.ig_post_sources (post_id, source_hashtag)
VALUES (%s, %s)
ON CONFLICT (post_id, source_hashtag) DO NOTHING
RETURNING 1;
"""

def _row_from_item(item: dict[str, Any], source_hashtag: str) -> tuple:
    """Apify 응답 1건을 INSERT placeholder 순서의 튜플로 변환."""
    likes = item.get("likesCount")
    return (
        item["id"],
        item.get("shortCode"),
        item.get("url"),
        item.get("type"),
        item.get("productType"),
        item.get("caption"),
        item.get("commentsCount"),
        likes,                               # -1 그대로 보존, NULL 변환은 staging
        item.get("timestamp"),
        item.get("ownerUsername"),
        item.get("ownerFullName"),
        item.get("ownerId"),
        item.get("displayUrl"),
        Jsonb(item.get("images") or []),
        Jsonb(item.get("childPosts") or []),
        Jsonb(item.get("musicInfo") or {}),
        Jsonb(item),
    )

def upsert_posts(items: list[dict[str, Any]], source_hashtag: str) -> dict[str, int]:
    """raw.ig_posts 에 items 를 upsert하고 inserted/updated 카운트를 반환."""
    if not items:
        return {"inserted": 0, "updated": 0, "source_links_inserted": 0, "total": 0}

    dsn = (
        f"host={os.environ.get('POSTGRES_HOST', 'postgres')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )

    inserted = 0
    updated = 0

    source_links_inserted = 0

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for item in items:
                row = _row_from_item(item, source_hashtag)
                cur.execute(_INSERT_SQL, row)
                result = cur.fetchone()
                if result and result[0]:
                    inserted += 1
                else:
                    updated += 1

                cur.execute(_INSERT_SOURCE_SQL, (item["id"], source_hashtag))
                source_result = cur.fetchone()
                if source_result:
                    source_links_inserted += 1
        conn.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "source_links_inserted": source_links_inserted,
        "total": len(items)}

if __name__ == "__main__":
    import argparse
    import sys
    from data_generation.collectors.apify_hashtag import collect_hashtag

    parser = argparse.ArgumentParser(description="Apify수집 + raw.ig_posts upsert")
    parser.add_argument("--hashtag", required=True)
    parser.add_argument("--k", type=int, default=20)
    args = parser.parse_args()

    print(f"[loader] collecting #{args.hashtag!r} k={args.k} ...", file=sys.stderr)
    items = collect_hashtag(args.hashtag, args.k)
    print(f"[loader] collected {len(items)} items, upserting ...", file=sys.stderr)
    metrics = upsert_posts(items, source_hashtag=args.hashtag)
    print(json.dumps(metrics, ensure_ascii=False))