"""Compatibility wrapper for the Phase 2C attribution generator.

post_metrics.py originally pointed toward synthetic views/impressions/clicks.
The current design uses observed Apify metrics instead. Use
post_campaign_attribution.py for new work.
"""

from __future__ import annotations

from data_generation.generators.post_campaign_attribution import (
    enrich_posts_with_campaign_attribution,
)

__all__ = ["enrich_posts_with_campaign_attribution"]
