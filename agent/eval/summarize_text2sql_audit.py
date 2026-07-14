from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_AUDIT_PATH = Path("logs/text2sql_audit.jsonl")


def main() -> None:
    args = parse_args()
    records = load_audit_records(args.input)
    summary = summarize_audit_records(records)
    payload = json.dumps(summary, ensure_ascii=False, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {args.output} records={summary['total_records']}")
        return

    print(payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize Text2SQL /query/v2 audit logs by provider.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_AUDIT_PATH,
        help=f"Audit JSONL path. Default: {DEFAULT_AUDIT_PATH}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    return parser.parse_args()


def load_audit_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Audit line {line_number} must be a JSON object.")
        records.append(payload)
    return records


def summarize_audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        provider = provider_key(record)
        groups.setdefault(provider, []).append(record)

    provider_summaries = [
        summarize_provider(provider, provider_records)
        for provider, provider_records in sorted(groups.items())
    ]

    return {
        "total_records": len(records),
        "providers": provider_summaries,
    }


def provider_key(record: dict[str, Any]) -> str:
    summary = record.get("provider_summary")
    if isinstance(summary, dict):
        final_provider = summary.get("final_provider")
        if isinstance(final_provider, str) and final_provider:
            return final_provider

    usage = record.get("usage")
    if isinstance(usage, dict):
        provider = usage.get("provider")
        if isinstance(provider, str) and provider:
            return provider

    mode = record.get("mode")
    if isinstance(mode, str) and mode:
        return f"unknown:{mode}"

    return "unknown"


def summarize_provider(provider: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [
        latency
        for latency in (optional_float(record.get("latency_ms")) for record in records)
        if latency is not None
    ]
    summaries = [
        summary
        for summary in (record.get("provider_summary") for record in records)
        if isinstance(summary, dict)
    ]

    input_tokens = sum_optional_int(summary.get("input_tokens") for summary in summaries)
    cached_input_tokens = sum_optional_int(
        summary.get("cached_input_tokens") for summary in summaries
    )

    return {
        "provider": provider,
        "request_count": len(records),
        "status_counts": status_counts(records),
        "fallback_count": sum(1 for record in records if fallback_used(record)),
        "estimated_cost_usd": sum_optional_float(
            summary.get("estimated_cost_usd") for summary in summaries
        ),
        "provider_elapsed_ms": sum_optional_float(
            summary.get("provider_elapsed_ms") for summary in summaries
        ),
        "p50_latency_ms": percentile(latencies, 50),
        "p95_latency_ms": percentile(latencies, 95),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": sum_optional_int(summary.get("output_tokens") for summary in summaries),
        "total_tokens": sum_optional_int(summary.get("total_tokens") for summary in summaries),
        "cached_input_ratio": (
            round(cached_input_tokens / input_tokens, 4)
            if input_tokens and cached_input_tokens is not None
            else None
        ),
    }


def status_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = record.get("status")
        key = status if isinstance(status, str) and status else "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def fallback_used(record: dict[str, Any]) -> bool:
    summary = record.get("provider_summary")
    if isinstance(summary, dict) and summary.get("fallback_used") is True:
        return True
    return record.get("status") == "fallback_success"


def percentile(values: list[float], percentile_value: int) -> float | None:
    if not values:
        return None

    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * (percentile_value / 100))
    return round(sorted_values[index], 3)


def sum_optional_int(values: object) -> int | None:
    resolved = [
        int(value)
        for value in values
        if isinstance(value, int) and not isinstance(value, bool)
    ]
    return sum(resolved) if resolved else None


def sum_optional_float(values: object) -> float | None:
    resolved = [
        float(value)
        for value in values
        if isinstance(value, int | float) and not isinstance(value, bool)
    ]
    return round(sum(resolved), 8) if resolved else None


def optional_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


if __name__ == "__main__":
    main()
