"""Load Phase 2C synthetic/semi-synthetic rows into Postgres raw tables."""

from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

_ATTRIBUTION_COLUMNS = (
    "post_campaign_attribution_id",
    "post_id",
    "creator_username",
    "campaign_id",
    "post_date",
    "source_hashtag",
    "category",
    "likes_count_clean",
    "likes_hidden",
    "comments_count",
    "observed_engagement_count",
    "observed_engagement_tier",
    "paid_partnership_observed",
    "metric_policy",
    "synthetic_source",
    "raw_payload",
)

_CAMPAIGN_COLUMNS = (
    "campaign_id",
    "campaign_name",
    "region",
    "category",
    "objective",
    "campaign_budget_krw",
    "start_date",
    "end_date",
    "duration_days",
    "synthetic_source",
    "raw_payload",
)

_PAYMENT_COLUMNS = (
    "payment_event_id",
    "post_campaign_attribution_id",
    "post_id",
    "campaign_id",
    "creator_username",
    "event_ts",
    "region",
    "category",
    "objective",
    "currency",
    "payment_amount_local",
    "fx_rate_to_krw",
    "payment_amount_krw",
    "is_refunded",
    "observed_engagement_count",
    "observed_engagement_tier",
    "campaign_budget_krw",
    "paid_partnership_observed",
    "expected_payment_count",
    "conversion_model",
    "synthetic_source",
    "raw_payload",
)

_CAMPAIGN_UPDATABLE = tuple(
    column for column in _CAMPAIGN_COLUMNS if column != "campaign_id"
)

_UPSERT_CAMPAIGN_SQL = f"""
INSERT INTO raw.syn_campaigns ({", ".join(_CAMPAIGN_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_CAMPAIGN_COLUMNS))})
ON CONFLICT (campaign_id) DO UPDATE SET
    {", ".join(f"{column} = EXCLUDED.{column}" for column in _CAMPAIGN_UPDATABLE)},
    updated_at = now()
RETURNING (xmax = 0) AS inserted;
"""

_ATTRIBUTION_UPDATABLE = tuple(
    column
    for column in _ATTRIBUTION_COLUMNS
    if column != "post_campaign_attribution_id"
)

_UPSERT_ATTRIBUTION_SQL = f"""
INSERT INTO raw.syn_post_campaign_attributions ({", ".join(_ATTRIBUTION_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_ATTRIBUTION_COLUMNS))})
ON CONFLICT (post_campaign_attribution_id) DO UPDATE SET
    {", ".join(f"{column} = EXCLUDED.{column}" for column in _ATTRIBUTION_UPDATABLE)},
    updated_at = now()
RETURNING (xmax = 0) AS inserted;
"""

_PAYMENT_UPDATABLE = tuple(
    column for column in _PAYMENT_COLUMNS if column != "payment_event_id"
)

_UPSERT_PAYMENT_SQL = f"""
INSERT INTO raw.syn_payment_events ({", ".join(_PAYMENT_COLUMNS)})
VALUES ({", ".join(["%s"] * len(_PAYMENT_COLUMNS))})
ON CONFLICT (payment_event_id) DO UPDATE SET
    {", ".join(f"{column} = EXCLUDED.{column}" for column in _PAYMENT_UPDATABLE)},
    updated_at = now()
RETURNING (xmax = 0) AS inserted;
"""

_DELETE_STALE_PAYMENTS_SQL = """
DELETE FROM raw.syn_payment_events
WHERE post_campaign_attribution_id = ANY(%s)
  AND NOT (payment_event_id = ANY(%s));
"""


def _postgres_dsn() -> str:
    """환경변수로 Postgres 접속 문자열을 만든다."""
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'postgres')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )


def _attribution_row(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["post_campaign_attribution_id"],
        row["post_id"],
        row["creator_username"],
        row["campaign_id"],
        row["post_date"],
        row["source_hashtag"],
        row["category"],
        int(row["likes_count_clean"]),
        bool(row["likes_hidden"]),
        int(row["comments_count"]),
        int(row["observed_engagement_count"]),
        row["observed_engagement_tier"],
        bool(row["paid_partnership_observed"]),
        row["metric_policy"],
        row["synthetic_source"],
        Jsonb(row),
    )


def _campaign_row(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["campaign_id"],
        row["campaign_name"],
        row["region"],
        row["category"],
        row["objective"],
        int(row["campaign_budget_krw"]),
        row["start_date"],
        row["end_date"],
        int(row["duration_days"]),
        row["synthetic_source"],
        Jsonb(row),
    )


def _payment_row(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["payment_event_id"],
        row["post_campaign_attribution_id"],
        row["post_id"],
        row["campaign_id"],
        row["creator_username"],
        row["event_ts"],
        row["region"],
        row["category"],
        row["objective"],
        row["currency"],
        row["payment_amount_local"],
        row["fx_rate_to_krw"],
        row["payment_amount_krw"],
        bool(row["is_refunded"]),
        int(row["observed_engagement_count"]),
        row["observed_engagement_tier"],
        int(row["campaign_budget_krw"]),
        bool(row["paid_partnership_observed"]),
        row["expected_payment_count"],
        row["conversion_model"],
        row["synthetic_source"],
        Jsonb(row),
    )


def upsert_campaigns(rows: list[dict[str, Any]]) -> dict[str, int]:
    """raw.syn_campaigns에 campaign rows를 멱등 upsert한다."""
    if not rows:
        return {"inserted": 0, "updated": 0, "total": 0}

    inserted = 0
    updated = 0

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        for row in rows:
            cur.execute(_UPSERT_CAMPAIGN_SQL, _campaign_row(row))
            result = cur.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()

    return {"inserted": inserted, "updated": updated, "total": len(rows)}


def upsert_post_campaign_attributions(rows: list[dict[str, Any]]) -> dict[str, int]:
    """raw.syn_post_campaign_attributions에 attribution rows를 멱등 upsert한다."""
    if not rows:
        return {"inserted": 0, "updated": 0, "total": 0}

    inserted = 0
    updated = 0

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        for row in rows:
            cur.execute(_UPSERT_ATTRIBUTION_SQL, _attribution_row(row))
            result = cur.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()

    return {"inserted": inserted, "updated": updated, "total": len(rows)}


def upsert_payment_events(rows: list[dict[str, Any]]) -> dict[str, int]:
    """raw.syn_payment_events에 payment event rows를 멱등 upsert한다."""
    if not rows:
        return {"inserted": 0, "updated": 0, "total": 0}

    inserted = 0
    updated = 0

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        for row in rows:
            cur.execute(_UPSERT_PAYMENT_SQL, _payment_row(row))
            result = cur.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()

    return {"inserted": inserted, "updated": updated, "total": len(rows)}


def sync_payment_events_for_attributions(
    rows: list[dict[str, Any]],
    attribution_ids: list[str],
) -> dict[str, int]:
    """입력 attribution 범위의 payment events를 생성 결과와 동기화한다.

    Poisson event count는 attribution별 기대값에서 샘플링되므로, 재생성 시
    특정 attribution의 event 수가 0이 될 수 있다. 단순 upsert만 하면 이전 실행의
    남은 event가 삭제되지 않으므로 입력 attribution 범위의 stale event를 먼저 지운다.
    """
    if not attribution_ids:
        return {"inserted": 0, "updated": 0, "deleted": 0, "total": 0}

    generated_event_ids = [row["payment_event_id"] for row in rows]
    inserted = 0
    updated = 0
    deleted = 0

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        cur.execute(
            _DELETE_STALE_PAYMENTS_SQL,
            (attribution_ids, generated_event_ids),
        )
        deleted = cur.rowcount

        for row in rows:
            cur.execute(_UPSERT_PAYMENT_SQL, _payment_row(row))
            result = cur.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
        conn.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "deleted": deleted,
        "total": len(rows),
    }
