from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from typing import Any

import numpy as np

from data_generation.generators.generation_profile import (
    CAMPAIGN_BUDGET_MIN_KRW,
    CAMPAIGN_DURATION_DAYS,
    CAMPAIGN_DURATION_PROBABILITIES,
    CATEGORIES,
    CATEGORY_PROBABILITIES,
    OBJECTIVE_PROBABILITIES,
    OBJECTIVES,
    REGION_PROBABILITIES,
    REGIONS,
    SEED,
)


def generate_campaigns(
    rng: np.random.Generator,
    count: int,
    base_date: date,
) -> list[dict[str, Any]]:
    """Synthetic campaign 목록을 생성한다"""
    campaigns = []

    for index in range(count):
        region = str(rng.choice(REGIONS, p=REGION_PROBABILITIES))
        category = str(rng.choice(CATEGORIES, p=CATEGORY_PROBABILITIES))
        objective = str(rng.choice(OBJECTIVES, p=OBJECTIVE_PROBABILITIES))

        budget = int(rng.lognormal(mean=14.2, sigma=0.8))
        campaign_budget_krw = max(CAMPAIGN_BUDGET_MIN_KRW, budget)

        start_offset_days = int(rng.integers(-60, 15))
        duration_days = int(
            rng.choice(CAMPAIGN_DURATION_DAYS, p=CAMPAIGN_DURATION_PROBABILITIES)
        )

        start_date = base_date + timedelta(days=start_offset_days)
        end_date = start_date + timedelta(days=duration_days - 1)

        campaigns.append(
            {
                "campaign_id": f"camp_{index:06d}",
                "campaign_name": f"{category}_{region.lower()}_{objective}_{index:06d}",
                "region": region,
                "category": category,
                "objective": objective,
                "campaign_budget_krw": campaign_budget_krw,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": duration_days,
                "synthetic_source": "campaigns_lognormal_budget_v1",
            }
        )

    return campaigns


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic campaigns.")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--base-date", default="2026-06-16")
    parser.add_argument(
        "--write-postgres",
        action="store_true",
        help="Persist campaigns into raw.syn_campaigns.",
    )
    args = parser.parse_args()

    rng = np.random.default_rng(SEED)
    campaigns = generate_campaigns(
        rng=rng,
        count=args.count,
        base_date=date.fromisoformat(args.base_date),
    )
    load_metrics = None
    if args.write_postgres:
        from data_generation.collectors.loaders.synthetic_loader import upsert_campaigns

        load_metrics = upsert_campaigns(campaigns)

    print(
        json.dumps(
            {
                "campaign_count": len(campaigns),
                "load_metrics": load_metrics,
                "campaigns": campaigns,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
