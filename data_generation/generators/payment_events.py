from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import date, datetime, time, timedelta
from typing import Any

import numpy as np

from data_generation.generators.generation_profile import (
    CATEGORY_CONVERSION_MULTIPLIERS,
    PAYMENT_AMOUNT_LOGNORMAL_MEAN,
    PAYMENT_AMOUNT_LOGNORMAL_SIGMA,
    PAYMENT_BUDGET_MULTIPLIER_MAX,
    PAYMENT_BUDGET_MULTIPLIER_MIN,
    PAYMENT_BUDGET_REFERENCE_KRW,
    PAYMENT_ENGAGEMENT_LOG_WEIGHT,
    PAYMENT_OBJECTIVE_MULTIPLIERS,
    PAYMENT_PAID_PARTNERSHIP_MULTIPLIER,
    PAYMENT_REFUND_PROBABILITY,
    PAYMENT_TIER_BASE_RATES,
    REGION_CURRENCY,
    SEED,
)


def _rng_for_attribution(attribution_id: str) -> np.random.Generator:
    """입력 순서가 바뀌어도 같은 attribution은 같은 event를 만들도록 한다."""
    seed_bytes = hashlib.sha256(f"{SEED}:{attribution_id}".encode()).digest()
    seed = int.from_bytes(seed_bytes[:8], byteorder="big", signed=False)
    return np.random.default_rng(seed)


def _postgres_dsn() -> str:
    """환경변수로 Postgres 접속 문자열을 만든다."""
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'localhost')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB', 'adinsight')} "
        f"user={os.environ.get('POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('POSTGRES_PASSWORD', 'postgres')}"
    )


def load_payment_inputs(limit: int) -> list[dict[str, Any]]:
    """Payment simulation 입력이 되는 attribution + campaign row를 읽는다."""
    import psycopg
    from psycopg.rows import dict_row

    sql = """
        SELECT
            a.post_campaign_attribution_id,
            a.post_id,
            a.creator_username,
            a.campaign_id,
            a.post_date,
            a.category,
            a.observed_engagement_count,
            a.observed_engagement_tier,
            a.paid_partnership_observed,
            c.region,
            c.objective,
            c.campaign_budget_krw
        FROM raw.syn_post_campaign_attributions AS a
        INNER JOIN raw.syn_campaigns AS c
            ON a.campaign_id = c.campaign_id
        ORDER BY a.post_date DESC, a.post_campaign_attribution_id
        LIMIT %s
    """

    with psycopg.connect(_postgres_dsn(), row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(row) for row in cur.fetchall()]


def _budget_multiplier(campaign_budget_krw: int) -> float:
    """광고비 규모를 완만한 배수로 변환한다."""
    raw_multiplier = math.sqrt(
        max(campaign_budget_krw, 1) / PAYMENT_BUDGET_REFERENCE_KRW
    )
    return min(
        PAYMENT_BUDGET_MULTIPLIER_MAX,
        max(PAYMENT_BUDGET_MULTIPLIER_MIN, raw_multiplier),
    )


def estimate_expected_payment_count(
    observed_engagement_count: int,
    observed_engagement_tier: str,
    campaign_budget_krw: int,
    category: str,
    objective: str,
    paid_partnership_observed: bool,
) -> float:
    """관측 engagement와 campaign 조건으로 기대 결제 건수를 계산한다.

    views/impressions/clicks는 현재 Apify 공개 수집 데이터에서 안정적으로
    제공되지 않으므로 사용하지 않는다.
    """
    tier_base_rate = PAYMENT_TIER_BASE_RATES.get(observed_engagement_tier, 0.03)
    engagement_component = (
        math.log1p(max(0, observed_engagement_count)) * PAYMENT_ENGAGEMENT_LOG_WEIGHT
    )
    budget_multiplier = _budget_multiplier(campaign_budget_krw)
    category_multiplier = CATEGORY_CONVERSION_MULTIPLIERS.get(category, 1.0)
    objective_multiplier = PAYMENT_OBJECTIVE_MULTIPLIERS.get(objective, 1.0)
    partnership_multiplier = (
        PAYMENT_PAID_PARTNERSHIP_MULTIPLIER if paid_partnership_observed else 1.0
    )

    expected_count = (
        (tier_base_rate + engagement_component)
        * budget_multiplier
        * category_multiplier
        * objective_multiplier
        * partnership_multiplier
    )

    return max(0.0, expected_count)


def generate_payment_events_for_attribution(
    rng: np.random.Generator,
    attribution: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attribution row 1개에서 발생한 synthetic payment event 목록을 생성한다."""
    expected_payment_count = estimate_expected_payment_count(
        observed_engagement_count=int(attribution["observed_engagement_count"]),
        observed_engagement_tier=attribution["observed_engagement_tier"],
        campaign_budget_krw=int(attribution["campaign_budget_krw"]),
        category=attribution["category"],
        objective=attribution["objective"],
        paid_partnership_observed=bool(attribution["paid_partnership_observed"]),
    )
    payment_count = int(rng.poisson(expected_payment_count))

    region = attribution["region"]
    currency, fx_rate_to_krw = REGION_CURRENCY.get(region, ("KRW", 1.0))
    events = []
    post_date_value = attribution["post_date"]
    if isinstance(post_date_value, date):
        post_datetime = datetime.combine(post_date_value, time(hour=12))
    else:
        post_datetime = datetime.fromisoformat(str(post_date_value)[:10])

    for event_index in range(payment_count):
        seconds_after_post = int(rng.integers(0, 7 * 24 * 60 * 60))
        event_ts = post_datetime + timedelta(seconds=seconds_after_post)

        payment_amount_krw = float(
            rng.lognormal(
                mean=PAYMENT_AMOUNT_LOGNORMAL_MEAN,
                sigma=PAYMENT_AMOUNT_LOGNORMAL_SIGMA,
            )
        )
        payment_amount_local = payment_amount_krw / fx_rate_to_krw
        is_refunded = bool(rng.random() < PAYMENT_REFUND_PROBABILITY)
        attribution_id = attribution["post_campaign_attribution_id"]

        events.append(
            {
                "payment_event_id": f"pay_{attribution_id}_{event_index:04d}",
                "post_campaign_attribution_id": attribution_id,
                "post_id": attribution["post_id"],
                "campaign_id": attribution["campaign_id"],
                "creator_username": attribution["creator_username"],
                "event_ts": event_ts.isoformat(),
                "region": region,
                "category": attribution["category"],
                "objective": attribution["objective"],
                "currency": currency,
                "payment_amount_local": round(payment_amount_local, 2),
                "fx_rate_to_krw": fx_rate_to_krw,
                "payment_amount_krw": round(payment_amount_krw, 2),
                "is_refunded": is_refunded,
                "observed_engagement_count": int(
                    attribution["observed_engagement_count"]
                ),
                "observed_engagement_tier": attribution["observed_engagement_tier"],
                "campaign_budget_krw": int(attribution["campaign_budget_krw"]),
                "paid_partnership_observed": bool(
                    attribution["paid_partnership_observed"]
                ),
                "expected_payment_count": round(expected_payment_count, 4),
                "conversion_model": "poisson_observed_engagement_v1",
                "synthetic_source": "observed_engagement_payment_simulation_v1",
            }
        )

    return events


def generate_payment_events(
    rng: np.random.Generator,
    attributions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attribution rows 전체에서 synthetic payment events를 생성한다."""
    events = []
    for attribution in attributions:
        events.extend(
            generate_payment_events_for_attribution(
                rng=_rng_for_attribution(attribution["post_campaign_attribution_id"]),
                attribution=attribution,
            )
        )
    return events


def _sample_attributions() -> list[dict[str, Any]]:
    return [
        {
            "post_campaign_attribution_id": "postattr_sample_0001",
            "post_id": "3921832188514966508",
            "creator_username": "bruce_naver",
            "campaign_id": "camp_000001",
            "post_date": "2026-06-17",
            "region": "KR",
            "category": "beauty",
            "objective": "conversion",
            "campaign_budget_krw": 2_000_000,
            "observed_engagement_count": 12,
            "observed_engagement_tier": "medium",
            "paid_partnership_observed": False,
        },
        {
            "post_campaign_attribution_id": "postattr_sample_0002",
            "post_id": "3903059314819618546",
            "creator_username": "yeti__st",
            "campaign_id": "camp_000002",
            "post_date": "2026-05-20",
            "region": "JP",
            "category": "beauty",
            "objective": "conversion",
            "campaign_budget_krw": 8_000_000,
            "observed_engagement_count": 788,
            "observed_engagement_tier": "viral",
            "paid_partnership_observed": True,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic payment events from observed post attribution."
    )
    parser.add_argument(
        "--from-postgres",
        action="store_true",
        help="Read raw.syn_post_campaign_attributions joined to raw.syn_campaigns.",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument(
        "--write-postgres",
        action="store_true",
        help="Persist generated payment events into raw.syn_payment_events.",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)
    inputs = load_payment_inputs(args.limit) if args.from_postgres else _sample_attributions()
    events = generate_payment_events(rng=rng, attributions=inputs)

    load_metrics = None
    if args.write_postgres:
        from data_generation.collectors.loaders.synthetic_loader import (
            sync_payment_events_for_attributions,
        )

        load_metrics = sync_payment_events_for_attributions(
            rows=events,
            attribution_ids=[
                row["post_campaign_attribution_id"] for row in inputs
            ],
        )

    print(
        json.dumps(
            {
                "input_count": len(inputs),
                "event_count": len(events),
                "input_mode": "postgres" if args.from_postgres else "sample",
                "load_metrics": load_metrics,
                "events": events[:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
