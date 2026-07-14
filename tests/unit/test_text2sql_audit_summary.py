from __future__ import annotations

import json

from agent.eval.summarize_text2sql_audit import (
    load_audit_records,
    provider_key,
    summarize_audit_records,
)


def test_summarize_audit_records_groups_provider_cost_and_latency() -> None:
    summary = summarize_audit_records(
        [
            {
                "status": "success",
                "mode": "llm_generated_sql_v2_http_json",
                "latency_ms": 4100.0,
                "provider_summary": {
                    "fallback_used": False,
                    "final_provider": "gemini",
                    "final_model": "gemini-3.1-flash-lite",
                    "estimated_cost_usd": 0.0014,
                    "provider_elapsed_ms": 4000.0,
                    "input_tokens": 1000,
                    "cached_input_tokens": 800,
                    "output_tokens": 100,
                    "total_tokens": 1100,
                },
            },
            {
                "status": "blocked",
                "mode": "llm_generated_sql_v2_http_json",
                "latency_ms": 5100.0,
                "provider_summary": {
                    "fallback_used": False,
                    "final_provider": "gemini",
                    "final_model": "gemini-3.1-flash-lite",
                    "estimated_cost_usd": 0.0016,
                    "provider_elapsed_ms": 5000.0,
                    "input_tokens": 1200,
                    "cached_input_tokens": 900,
                    "output_tokens": 120,
                    "total_tokens": 1320,
                },
            },
            {
                "status": "success",
                "mode": "llm_generated_sql_v2_http_json",
                "latency_ms": 2500.0,
                "provider_summary": {
                    "fallback_used": False,
                    "final_provider": "openai",
                    "final_model": "unit-openai",
                    "estimated_cost_usd": 0.004,
                    "provider_elapsed_ms": 2400.0,
                    "input_tokens": 500,
                    "cached_input_tokens": 450,
                    "output_tokens": 50,
                    "total_tokens": 550,
                },
            },
            {
                "status": "fallback_success",
                "mode": "deterministic_expected_sql_registry_fallback_v1",
                "latency_ms": 25.0,
                "provider_summary": {
                    "fallback_used": True,
                    "final_provider": "deterministic_registry",
                    "estimated_cost_usd": 0.0,
                    "provider_elapsed_ms": 0.0,
                },
            },
        ]
    )

    providers = {provider["provider"]: provider for provider in summary["providers"]}
    assert summary["total_records"] == 4
    assert providers["gemini"]["request_count"] == 2
    assert providers["gemini"]["status_counts"] == {"blocked": 1, "success": 1}
    assert providers["gemini"]["estimated_cost_usd"] == 0.003
    assert providers["gemini"]["provider_elapsed_ms"] == 9000.0
    assert providers["gemini"]["p50_latency_ms"] == 4100.0
    assert providers["gemini"]["p95_latency_ms"] == 5100.0
    assert providers["gemini"]["input_tokens"] == 2200
    assert providers["gemini"]["cached_input_ratio"] == 0.7727
    assert providers["openai"]["estimated_cost_usd"] == 0.004
    assert providers["deterministic_registry"]["fallback_count"] == 1


def test_provider_key_falls_back_to_usage_or_mode() -> None:
    assert provider_key({"usage": {"provider": "openai"}}) == "openai"
    assert (
        provider_key({"mode": "llm_generated_sql_v2_http_json"})
        == "unknown:llm_generated_sql_v2_http_json"
    )
    assert provider_key({}) == "unknown"


def test_load_audit_records_reads_jsonl(tmp_path) -> None:
    path = tmp_path / "audit.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"status": "success"}),
                "",
                json.dumps({"status": "error"}),
            ]
        ),
        encoding="utf-8",
    )

    assert load_audit_records(path) == [
        {"status": "success"},
        {"status": "error"},
    ]
