from __future__ import annotations

import json
from typing import Any

import numpy as np

from data_generation.generators.generation_profile import (
    CATEGORIES,
    CATEGORY_PROBABILITIES,
    CREATOR_FOLLOWER_MIN,
    REGION_PROBABILITIES,
    REGIONS,
    SEED,
)


def generate_creators(
    rng: np.random.Generator,
    count: int,
) -> list[dict[str, Any]]:
    """Synthetic creator profile 목록을 생성한다"""
    creators = []

    for index in range(count):
        region = str(rng.choice(REGIONS, p=REGION_PROBABILITIES))
        category = str(rng.choice(CATEGORIES, p=CATEGORY_PROBABILITIES))

        follower_count = int(rng.lognormal(mean=9.2, sigma=1.1))
        follower_count = max(CREATOR_FOLLOWER_MIN, follower_count)

        engagement_rate = float(rng.beta(a=2.0, b=30.0))
        sponsored_rate = float(rng.beta(a=2.0, b=8.0))

        creators.append(
            {
                "creator_username": f"{category}_{region.lower()}_{index:05d}",
                "region": region,
                "category": category,
                "follower_count": follower_count,
                "engagement_rate": round(engagement_rate, 4),
                "sponsored_rate": round(sponsored_rate, 4),
                "synthetic_source": "creators_lognormal_beta_v1",
            }
        )

    return creators

if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    creators = generate_creators(rng=rng, count=10)

    print(
        json.dumps(
            {
                "creator_count": len(creators),
                "creators": creators,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
