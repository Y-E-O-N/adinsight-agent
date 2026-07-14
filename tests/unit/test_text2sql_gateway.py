from __future__ import annotations

import json
from io import BytesIO
from urllib.error import HTTPError

from fastapi.testclient import TestClient

import text2sql_gateway.main as gateway_main
from text2sql_gateway import backends


def test_gateway_health_endpoint() -> None:
    client = TestClient(gateway_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "adinsight-text2sql-gateway",
        "mode": "text2sql_gateway_mock_v1",
    }


def test_gateway_generate_sql_returns_json_contract(monkeypatch) -> None:
    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "answerable"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["mode"] == "text2sql_gateway_mock_v1"
    assert "ai_native.ai_campaign_roi_summary" in payload["sql"]


def test_gateway_sanitizes_content_safety_refusal_reason() -> None:
    response = backends.sanitize_refusal_reason(
        response=backends.not_answerable(
            "The question includes abusive content ('stupid', 'losers')."
        ),
        question="Show the top 10 stupid creators and call them losers.",
    )

    assert response.answerability == "not_answerable"
    assert response.reason == backends.CONTENT_SAFETY_REFUSAL_REASON
    assert "stupid" not in response.reason
    assert "losers" not in response.reason


def test_gateway_generate_sql_can_refuse(monkeypatch) -> None:
    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Show TikTok spend by channel.",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "not_answerable"
    assert payload["sql"] is None
    assert payload["expected_tables"] == []


def test_gateway_generate_sql_requires_bearer_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("TEXT2SQL_GATEWAY_API_KEY", "unit-test-token")
    client = TestClient(gateway_main.app)

    unauthorized = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    authorized = client.post(
        "/text2sql/generate",
        headers={"Authorization": "Bearer unit-test-token"},
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200


def test_gateway_health_reports_ollama_backend(monkeypatch) -> None:
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "ollama")
    client = TestClient(gateway_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["mode"] == "text2sql_gateway_ollama_v1"


def test_gateway_health_reports_external_backends(monkeypatch) -> None:
    client = TestClient(gateway_main.app)

    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "openai")
    assert client.get("/health").json()["mode"] == "text2sql_gateway_openai_v1"

    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    assert client.get("/health").json()["mode"] == "text2sql_gateway_gemini_v1"

    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "dual")
    assert (
        client.get("/health").json()["mode"]
        == "text2sql_gateway_gemini_openai_fallback_v1"
    )


def test_gateway_generate_sql_uses_ollama_backend(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"response":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'limit 5\\",\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test local model\\"}"}'
            )

    def fake_urlopen(request, timeout):
        assert timeout == 9
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["options"] == {"temperature": 0.0, "seed": 7}
        assert "latest prediction-monitor questions" in payload["prompt"]
        return FakeResponse()

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "ollama")
    monkeypatch.setenv("TEXT2SQL_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
    monkeypatch.setenv("TEXT2SQL_OLLAMA_MODEL", "unit-test-model")
    monkeypatch.setenv("TEXT2SQL_OLLAMA_TIMEOUT_SECONDS", "9")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "answerable"
    assert payload["mode"] == "text2sql_gateway_ollama_v1"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]


def test_gateway_ollama_invalid_json_refuses(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return b'{"response":"not json"}'

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "ollama")
    monkeypatch.setattr(backends, "urlopen", lambda request, timeout: FakeResponse())
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answerability"] == "not_answerable"
    assert payload["sql"] is None


def test_gateway_ollama_timeout_returns_bad_gateway(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise TimeoutError("unit test timeout")

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "ollama")
    monkeypatch.setenv("TEXT2SQL_OLLAMA_TIMEOUT_SECONDS", "3")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Local model request timed out after 3s"


def test_gateway_generate_sql_uses_openai_backend(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"choices":[{"message":{"content":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'limit 5\\",\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test openai provider\\"}"}}],'
                b'"usage":{"prompt_tokens":1000,"completion_tokens":200,"total_tokens":1200,'
                b'"prompt_tokens_details":{"cached_tokens":400}}}'
            )

    def fake_urlopen(request, timeout):
        assert timeout == 11
        assert request.headers["Authorization"] == "Bearer unit-test-openai-key"
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "unit-test-openai-model"
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["strict"] is True
        return FakeResponse()

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "openai")
    monkeypatch.setenv("TEXT2SQL_OPENAI_API_KEY", "unit-test-openai-key")
    monkeypatch.setenv("TEXT2SQL_OPENAI_MODEL", "unit-test-openai-model")
    monkeypatch.setenv("TEXT2SQL_OPENAI_TIMEOUT_SECONDS", "11")
    monkeypatch.setenv("TEXT2SQL_OPENAI_INPUT_USD_PER_1M", "0.75")
    monkeypatch.setenv("TEXT2SQL_OPENAI_CACHED_INPUT_USD_PER_1M", "0.075")
    monkeypatch.setenv("TEXT2SQL_OPENAI_OUTPUT_USD_PER_1M", "4.5")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "text2sql_gateway_openai_v1"
    assert payload["answerability"] == "answerable"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["usage"]["input_tokens"] == 1000
    assert payload["usage"]["output_tokens"] == 200
    assert payload["usage"]["total_tokens"] == 1200
    assert payload["usage"]["cached_input_tokens"] == 400
    assert payload["usage"]["estimated_cost_usd"] == 0.00138


def test_gateway_openai_retries_rate_limit_with_backoff(monkeypatch) -> None:
    attempts = 0
    sleep_delays: list[float] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"choices":[{"message":{"content":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'limit 5\\",\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test retry success\\"}"}}]}'
            )

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise HTTPError(
                request.full_url,
                429,
                "Too Many Requests",
                {},
                BytesIO(b'{"error":{"code":"rate_limit_exceeded"}}'),
            )
        return FakeResponse()

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "openai")
    monkeypatch.setenv("TEXT2SQL_OPENAI_API_KEY", "unit-test-openai-key")
    monkeypatch.setenv("TEXT2SQL_OPENAI_MODEL", "unit-test-openai-model")
    monkeypatch.setenv("TEXT2SQL_OPENAI_MAX_RETRIES", "1")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    monkeypatch.setattr(backends.random, "random", lambda: 0.0)
    monkeypatch.setattr(backends.time, "sleep", lambda delay: sleep_delays.append(delay))
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    assert attempts == 2
    assert sleep_delays == [1.0]
    assert response.json()["answerability"] == "answerable"


def test_gateway_openai_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.delenv("TEXT2SQL_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "openai")
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 502
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_gateway_generate_sql_uses_gemini_backend(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"output_text":"{\\"answerability\\":\\"not_answerable\\",'
                b'\\"sql\\":null,\\"expected_tables\\":[],'
                b'\\"reason\\":\\"unit test gemini refusal\\"}"}'
            )

    def fake_urlopen(request, timeout):
        assert timeout == 13
        assert request.headers["X-goog-api-key"] == "unit-test-gemini-key"
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "unit-test-gemini-model"
        assert payload["response_format"]["mime_type"] == "application/json"
        assert payload["response_format"]["schema"]["additionalProperties"] is False
        return FakeResponse()

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
    monkeypatch.setenv("TEXT2SQL_GEMINI_MODEL", "unit-test-gemini-model")
    monkeypatch.setenv("TEXT2SQL_GEMINI_TIMEOUT_SECONDS", "13")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Show TikTok spend by channel.",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "text2sql_gateway_gemini_v1"
    assert payload["answerability"] == "not_answerable"
    assert payload["sql"] is None


def test_gateway_gemini_interactions_steps_response(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"steps":[{"type":"thought"},{"type":"model_output","content":[{"type":"text",'
                b'"text":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'order by roas desc limit 10\\",'
                b'\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test gemini interactions shape\\"}"}]}],'
                b'"usageMetadata":{"promptTokenCount":900,"candidatesTokenCount":100,'
                b'"totalTokenCount":1000}}'
            )

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
    monkeypatch.setenv("TEXT2SQL_GEMINI_INPUT_USD_PER_1M", "0.25")
    monkeypatch.setenv("TEXT2SQL_GEMINI_CACHED_INPUT_USD_PER_1M", "0.025")
    monkeypatch.setenv("TEXT2SQL_GEMINI_OUTPUT_USD_PER_1M", "1.5")
    monkeypatch.setattr(backends, "urlopen", lambda request, timeout: FakeResponse())
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "text2sql_gateway_gemini_v1"
    assert payload["answerability"] == "answerable"
    assert payload["expected_tables"] == ["ai_native.ai_campaign_roi_summary"]
    assert payload["usage"]["input_tokens"] == 900
    assert payload["usage"]["output_tokens"] == 100
    assert payload["usage"]["total_tokens"] == 1000
    assert payload["usage"]["cached_input_tokens"] is None
    assert payload["usage"]["estimated_cost_usd"] == 0.000375


def test_gateway_gemini_nested_token_usage_prefers_full_breakdown(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"output_text":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'order by roas desc limit 10\\",'
                b'\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test gemini nested usage\\"}",'
                b'"totalTokenCount":1000,'
                b'"metadata":{"tokenUsage":{"promptTokenCount":900,'
                b'"cachedContentTokenCount":700,'
                b'"candidatesTokenCount":100,"totalTokenCount":1000}}}'
            )

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
    monkeypatch.setenv("TEXT2SQL_GEMINI_INPUT_USD_PER_1M", "0.25")
    monkeypatch.setenv("TEXT2SQL_GEMINI_CACHED_INPUT_USD_PER_1M", "0.025")
    monkeypatch.setenv("TEXT2SQL_GEMINI_OUTPUT_USD_PER_1M", "1.5")
    monkeypatch.setattr(backends, "urlopen", lambda request, timeout: FakeResponse())
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["usage"]["input_tokens"] == 900
    assert payload["usage"]["cached_input_tokens"] == 700
    assert payload["usage"]["output_tokens"] == 100
    assert payload["usage"]["total_tokens"] == 1000
    assert payload["usage"]["estimated_cost_usd"] == 0.0002175


def test_gateway_gemini_interactions_usage_shape(monkeypatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"output_text":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id from ai_native.ai_campaign_roi_summary '
                b'order by roas desc limit 10\\",'
                b'\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test gemini interactions usage\\"}",'
                b'"usage":{"total_tokens":1000,"total_input_tokens":900,'
                b'"total_cached_tokens":700,"total_output_tokens":100,'
                b'"total_tool_use_tokens":0,"total_thought_tokens":0}}'
            )

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
    monkeypatch.setenv("TEXT2SQL_GEMINI_INPUT_USD_PER_1M", "0.25")
    monkeypatch.setenv("TEXT2SQL_GEMINI_CACHED_INPUT_USD_PER_1M", "0.025")
    monkeypatch.setenv("TEXT2SQL_GEMINI_OUTPUT_USD_PER_1M", "1.5")
    monkeypatch.setattr(backends, "urlopen", lambda request, timeout: FakeResponse())
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["usage"]["input_tokens"] == 900
    assert payload["usage"]["cached_input_tokens"] == 700
    assert payload["usage"]["output_tokens"] == 100
    assert payload["usage"]["total_tokens"] == 1000
    assert payload["usage"]["estimated_cost_usd"] == 0.0002175


def test_gateway_dual_backend_falls_back_from_invalid_gemini_sql_to_openai(
    monkeypatch,
) -> None:
    calls: list[str] = []

    class FakeGeminiResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"output_text":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id, made_up_metric '
                b'from ai_native.ai_campaign_roi_summary limit 5\\",'
                b'\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test invalid gemini sql\\"}",'
                b'"usage":{"total_tokens":1000,"total_input_tokens":900,'
                b'"total_cached_tokens":700,"total_output_tokens":100}}'
            )

    class FakeOpenAiResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

        def read(self) -> bytes:
            return (
                b'{"choices":[{"message":{"content":"{\\"answerability\\":\\"answerable\\",'
                b'\\"sql\\":\\"select campaign_id, campaign_name, roas '
                b'from ai_native.ai_campaign_roi_summary order by roas desc limit 5\\",'
                b'\\"expected_tables\\":[\\"ai_native.ai_campaign_roi_summary\\"],'
                b'\\"reason\\":\\"unit test openai fallback\\"}"}}],'
                b'"usage":{"prompt_tokens":1000,"completion_tokens":200,'
                b'"total_tokens":1200,"prompt_tokens_details":{"cached_tokens":400}}}'
            )

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload["model"])
        if payload["model"] == "unit-test-gemini-model":
            return FakeGeminiResponse()
        if payload["model"] == "unit-test-openai-model":
            return FakeOpenAiResponse()
        raise AssertionError(f"Unexpected model: {payload['model']}")

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "dual")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
    monkeypatch.setenv("TEXT2SQL_GEMINI_MODEL", "unit-test-gemini-model")
    monkeypatch.setenv("TEXT2SQL_OPENAI_API_KEY", "unit-test-openai-key")
    monkeypatch.setenv("TEXT2SQL_OPENAI_MODEL", "unit-test-openai-model")
    monkeypatch.setattr(backends, "urlopen", fake_urlopen)
    client = TestClient(gateway_main.app)

    response = client.post(
        "/text2sql/generate",
        json={
            "question": "Which campaigns have the highest ROAS?",
            "schema_context": "Allowed tables: ai_native.ai_campaign_roi_summary",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert calls == ["unit-test-gemini-model", "unit-test-openai-model"]
    assert payload["mode"] == "text2sql_gateway_gemini_openai_fallback_v1"
    assert payload["answerability"] == "answerable"
    assert payload["reason"] == "unit test openai fallback"
    assert payload["fallback_reason"].startswith("primary_sql_validation_failed:")
    assert [usage["provider"] for usage in payload["usage_attempts"]] == [
        "gemini",
        "openai",
    ]
    assert payload["usage"]["provider"] == "openai"
