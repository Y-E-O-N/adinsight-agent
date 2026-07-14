from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

DEFAULT_TEXT2SQL_PRICES_USD_PER_1M = {
    "openai": {
        "input": Decimal("0.75"),
        "cached_input": Decimal("0.075"),
        "output": Decimal("4.5"),
        "source": "default:gpt-5.4-mini:user_supplied_2026-07-10",
    },
    "gemini": {
        "input": Decimal("0.25"),
        "cached_input": Decimal("0.025"),
        "output": Decimal("1.5"),
        "source": "default:gemini-3.1-flash-lite:user_supplied_2026-07-10",
    },
}


@dataclass(frozen=True)
class LlmUsage:
    provider: str
    model: str | None
    input_tokens: int | None = None
    cached_input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None
    elapsed_ms: float | None = None
    pricing_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_llm_usage(
    *,
    provider: str,
    model: str | None,
    payload: object,
    elapsed_ms: float | None,
    env: dict[str, str] | os._Environ[str] = os.environ,
) -> LlmUsage:
    token_payload = extract_token_payload(payload)
    input_tokens = first_int(
        token_payload,
        (
            "input_tokens",
            "prompt_tokens",
            "prompt_token_count",
            "promptTokenCount",
            "inputTokenCount",
            "total_input_tokens",
        ),
    )
    output_tokens = first_int(
        token_payload,
        (
            "output_tokens",
            "completion_tokens",
            "candidates_token_count",
            "candidatesTokenCount",
            "outputTokenCount",
            "total_output_tokens",
            "eval_count",
        ),
    )
    cached_input_tokens = extract_cached_input_tokens(token_payload)
    total_tokens = first_int(
        token_payload,
        ("total_tokens", "totalTokenCount", "total_token_count"),
    )
    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = (input_tokens or 0) + (output_tokens or 0)

    estimated_cost_usd, pricing_source = estimate_cost_usd(
        provider=provider,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        env=env,
    )

    return LlmUsage(
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        cached_input_tokens=cached_input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        elapsed_ms=elapsed_ms,
        pricing_source=pricing_source,
    )


def extract_token_payload(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    best_payload: dict[str, Any] = {}
    best_score = 0
    for candidate in iter_token_payload_candidates(payload):
        normalized = normalize_usage_keys(candidate)
        score = score_usage_payload(normalized)
        if score > best_score:
            best_payload = normalized
            best_score = score

    if best_payload:
        return best_payload

    return {}


def iter_token_payload_candidates(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    seen: set[int] = set()
    preferred_candidates: list[object] = [
        payload.get("usage"),
        payload.get("usage_metadata"),
        payload.get("usageMetadata"),
        payload.get("token_usage"),
        payload.get("tokenUsage"),
    ]

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        preferred_candidates.extend(
            [
                metadata.get("usage"),
                metadata.get("usage_metadata"),
                metadata.get("usageMetadata"),
                metadata.get("token_usage"),
                metadata.get("tokenUsage"),
            ]
        )

    preferred_candidates.append(payload)
    for candidate in preferred_candidates:
        if isinstance(candidate, dict) and id(candidate) not in seen:
            seen.add(id(candidate))
            yield candidate

    yield from iter_nested_dicts(payload, seen)


def iter_nested_dicts(value: object, seen: set[int]) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if id(value) not in seen:
            seen.add(id(value))
            yield value
        for child in value.values():
            yield from iter_nested_dicts(child, seen)
    elif isinstance(value, list):
        for child in value:
            yield from iter_nested_dicts(child, seen)


def score_usage_payload(payload: dict[str, Any]) -> int:
    score = 0
    token_keys = (
        "input_tokens",
        "prompt_tokens",
        "prompt_token_count",
        "promptTokenCount",
        "inputTokenCount",
        "total_input_tokens",
        "output_tokens",
        "completion_tokens",
        "candidates_token_count",
        "candidatesTokenCount",
        "outputTokenCount",
        "total_output_tokens",
        "eval_count",
        "total_tokens",
        "totalTokenCount",
        "total_token_count",
        "cached_input_tokens",
        "cached_tokens",
        "cachedTokens",
        "cached_content_token_count",
        "cachedContentTokenCount",
        "total_cached_tokens",
        "prompt_eval_count",
    )
    for key in token_keys:
        if first_int(payload, (key,)) is not None:
            score += 1

    prompt_details = payload.get("prompt_tokens_details")
    if isinstance(prompt_details, dict) and first_int(prompt_details, ("cached_tokens",)):
        score += 1

    return score


def normalize_usage_keys(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    prompt_details = payload.get("prompt_tokens_details")
    if isinstance(prompt_details, dict):
        normalized["cached_input_tokens"] = prompt_details.get("cached_tokens")
    if "prompt_eval_count" in payload and "prompt_tokens" not in normalized:
        normalized["prompt_tokens"] = payload["prompt_eval_count"]
    if "eval_count" in payload and "completion_tokens" not in normalized:
        normalized["completion_tokens"] = payload["eval_count"]
    return normalized


def extract_cached_input_tokens(payload: dict[str, Any]) -> int | None:
    return first_int(
        payload,
        (
            "cached_input_tokens",
            "cached_tokens",
            "cachedTokens",
            "cached_content_token_count",
            "cachedContentTokenCount",
            "total_cached_tokens",
        ),
    )


def first_int(payload: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def estimate_cost_usd(
    *,
    provider: str,
    input_tokens: int | None,
    cached_input_tokens: int | None,
    output_tokens: int | None,
    env: dict[str, str] | os._Environ[str] = os.environ,
) -> tuple[float | None, str | None]:
    input_price, input_source = resolve_price_per_1m(provider, "input", env)
    cached_input_price, cached_input_source = resolve_price_per_1m(
        provider,
        "cached_input",
        env,
    )
    output_price, output_source = resolve_price_per_1m(provider, "output", env)

    if input_price is None or cached_input_price is None or output_price is None:
        return None, None

    resolved_cached_input_tokens = min(cached_input_tokens or 0, input_tokens or 0)
    uncached_input_tokens = max((input_tokens or 0) - resolved_cached_input_tokens, 0)
    input_cost = Decimal(uncached_input_tokens) * input_price / Decimal(1_000_000)
    cached_input_cost = (
        Decimal(resolved_cached_input_tokens) * cached_input_price / Decimal(1_000_000)
    )
    output_cost = Decimal(output_tokens or 0) * output_price / Decimal(1_000_000)
    return (
        float(round(input_cost + cached_input_cost + output_cost, 8)),
        f"{input_source},{cached_input_source},{output_source}",
    )


def resolve_price_per_1m(
    provider: str,
    direction: str,
    env: dict[str, str] | os._Environ[str],
) -> tuple[Decimal | None, str | None]:
    normalized_provider = provider.upper()
    normalized_direction = direction.upper()
    keys = (
        f"TEXT2SQL_{normalized_provider}_{normalized_direction}_USD_PER_1M",
        f"TEXT2SQL_{normalized_direction}_USD_PER_1M",
    )

    for key in keys:
        value = env.get(key)
        if value:
            return Decimal(value), key

    defaults = DEFAULT_TEXT2SQL_PRICES_USD_PER_1M.get(provider.lower())
    if defaults is not None and direction in defaults:
        return defaults[direction], str(defaults["source"])

    return None, None


def summarize_usages(usages: list[LlmUsage | None]) -> dict[str, Any]:
    present_usages = [usage for usage in usages if usage is not None]
    if not present_usages:
        return {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
            "provider_elapsed_ms": None,
        }

    return {
        "input_tokens": sum_optional_int(usage.input_tokens for usage in present_usages),
        "cached_input_tokens": sum_optional_int(
            usage.cached_input_tokens for usage in present_usages
        ),
        "output_tokens": sum_optional_int(usage.output_tokens for usage in present_usages),
        "total_tokens": sum_optional_int(usage.total_tokens for usage in present_usages),
        "estimated_cost_usd": sum_optional_float(
            usage.estimated_cost_usd for usage in present_usages
        ),
        "provider_elapsed_ms": sum_optional_float(usage.elapsed_ms for usage in present_usages),
    }


def combine_usages(usages: list[LlmUsage | None]) -> LlmUsage | None:
    present_usages = [usage for usage in usages if usage is not None]
    if not present_usages:
        return None

    summary = summarize_usages(present_usages)
    final_usage = present_usages[-1]
    pricing_sources = sorted(
        {
            usage.pricing_source
            for usage in present_usages
            if usage.pricing_source is not None
        }
    )
    return LlmUsage(
        provider=final_usage.provider,
        model=final_usage.model,
        input_tokens=summary["input_tokens"],
        cached_input_tokens=summary["cached_input_tokens"],
        output_tokens=summary["output_tokens"],
        total_tokens=summary["total_tokens"],
        estimated_cost_usd=summary["estimated_cost_usd"],
        elapsed_ms=summary["provider_elapsed_ms"],
        pricing_source=";".join(pricing_sources) if pricing_sources else None,
    )


def sum_optional_int(values: object) -> int | None:
    resolved = [value for value in values if value is not None]
    return sum(resolved) if resolved else None


def sum_optional_float(values: object) -> float | None:
    resolved = [value for value in values if value is not None]
    return round(sum(resolved), 6) if resolved else None
