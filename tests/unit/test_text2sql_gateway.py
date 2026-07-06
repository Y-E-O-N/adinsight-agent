from __future__ import annotations

import json

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
                b'\\"reason\\":\\"unit test openai provider\\"}"}}]}'
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
                b'\\"reason\\":\\"unit test gemini interactions shape\\"}"}]}]}'
            )

    monkeypatch.delenv("TEXT2SQL_GATEWAY_API_KEY", raising=False)
    monkeypatch.setenv("TEXT2SQL_GATEWAY_BACKEND", "gemini")
    monkeypatch.setenv("TEXT2SQL_GEMINI_API_KEY", "unit-test-gemini-key")
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
