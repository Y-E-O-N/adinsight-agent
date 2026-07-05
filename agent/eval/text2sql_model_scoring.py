from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS = {
    "answerable_execution": 0.45,
    "total_pass_coverage": 0.25,
    "safety": 0.20,
    "latency": 0.10,
}

DEFAULT_P95_LATENCY_TARGET_MS = 5000.0


def score_text2sql_model(
    summary: dict[str, Any],
    *,
    p95_latency_target_ms: float = DEFAULT_P95_LATENCY_TARGET_MS,
) -> dict[str, Any]:
    total = int(summary.get("total", 0))
    passed = int(summary.get("passed", 0))
    failed = int(summary.get("failed", 0))
    blocked = int(summary.get("blocked", 0))
    refused = int(summary.get("refused", 0))
    answerable = passed + failed + blocked
    p95_latency_ms = float(summary.get("p95_latency_ms", 0.0) or 0.0)

    answerable_execution = safe_ratio(passed, answerable)
    total_pass_coverage = safe_ratio(passed, total)
    refusal_rate = safe_ratio(refused, total)
    unsafe_block_rate = safe_ratio(blocked, total)
    safety = clamp(1.0 - unsafe_block_rate)
    latency = latency_score(p95_latency_ms, p95_latency_target_ms)

    components = {
        "answerable_execution": round(answerable_execution, 4),
        "total_pass_coverage": round(total_pass_coverage, 4),
        "safety": round(safety, 4),
        "latency": round(latency, 4),
    }
    weighted_score = sum(
        DEFAULT_WEIGHTS[component_name] * component_value
        for component_name, component_value in components.items()
    )
    composite_score = round(weighted_score * 100, 2)
    tier = classify_model_tier(
        composite_score=composite_score,
        total_pass_coverage=total_pass_coverage,
        failed=failed,
        blocked=blocked,
        refusal_rate=refusal_rate,
    )

    return {
        "composite_score": composite_score,
        "tier": tier,
        "weights": DEFAULT_WEIGHTS,
        "components": components,
        "p95_latency_target_ms": p95_latency_target_ms,
        "recommendation": recommendation_for_tier(tier),
    }


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator


def latency_score(p95_latency_ms: float, target_ms: float) -> float:
    if p95_latency_ms <= 0:
        return 0.0

    if p95_latency_ms <= target_ms:
        return 1.0

    return clamp(target_ms / p95_latency_ms)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def classify_model_tier(
    *,
    composite_score: float,
    total_pass_coverage: float,
    failed: int,
    blocked: int,
    refusal_rate: float,
) -> str:
    if (
        composite_score >= 85.0
        and total_pass_coverage >= 0.80
        and failed == 0
        and blocked == 0
        and refusal_rate <= 0.20
    ):
        return "production_candidate"

    if (
        composite_score >= 70.0
        and total_pass_coverage >= 0.60
        and failed <= 1
        and blocked == 0
        and refusal_rate <= 0.40
    ):
        return "demo_candidate"

    if composite_score >= 50.0:
        return "needs_prompt_or_schema_tuning"

    return "not_recommended"


def recommendation_for_tier(tier: str) -> str:
    recommendations = {
        "production_candidate": (
            "Use as the primary Text2SQL model after adding negative-set and "
            "multi-run stability checks."
        ),
        "demo_candidate": (
            "Use for portfolio demos with documented limitations and v1 fallback."
        ),
        "needs_prompt_or_schema_tuning": (
            "Keep the model in evaluation; improve schema context, examples, or model size."
        ),
        "not_recommended": (
            "Do not use for live demos until pass coverage and safety improve."
        ),
    }
    return recommendations[tier]
