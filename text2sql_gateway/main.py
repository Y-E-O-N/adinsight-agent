from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from agent.text2sql.llm_client import SqlGenerationRequest
from text2sql_gateway.backends import GatewayBackendError, generate_sql_with_backend

DEFAULT_GATEWAY_MODE = "text2sql_gateway_mock_v1"

app = FastAPI(
    title="AdInsight Text2SQL Gateway",
    version="0.1.0",
    description="Provider-facing Text2SQL generation gateway for AdInsight.",
)


class GatewayHealthResponse(BaseModel):
    status: str
    service: str
    mode: str


class GenerateSqlRequest(BaseModel):
    question: str = Field(..., min_length=1)
    schema_context: str = Field(..., min_length=1)


class GenerateSqlResponse(BaseModel):
    answerability: str
    sql: str | None
    expected_tables: list[str]
    reason: str
    mode: str
    usage: dict | None = None
    usage_attempts: list[dict] = Field(default_factory=list)
    fallback_reason: str | None = None


@app.get("/health", response_model=GatewayHealthResponse)
def health() -> GatewayHealthResponse:
    return GatewayHealthResponse(
        status="ok",
        service="adinsight-text2sql-gateway",
        mode=current_gateway_mode(),
    )


@app.post("/text2sql/generate", response_model=GenerateSqlResponse)
def generate_sql(
    request: GenerateSqlRequest,
    authorization: str | None = Header(default=None),
) -> GenerateSqlResponse:
    verify_gateway_auth(authorization)
    try:
        generation = generate_sql_with_backend(
            SqlGenerationRequest(
                question=request.question,
                schema_context=request.schema_context,
            )
        )
    except GatewayBackendError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return GenerateSqlResponse(
        answerability=generation.response.answerability,
        sql=generation.response.sql,
        expected_tables=list(generation.response.expected_tables),
        reason=generation.response.reason,
        mode=generation.mode,
        usage=(
            generation.response.usage.to_dict()
            if generation.response.usage is not None
            else None
        ),
        usage_attempts=[
            usage.to_dict()
            for usage in generation.response.usage_attempts
        ],
        fallback_reason=generation.response.fallback_reason,
    )


def verify_gateway_auth(authorization: str | None) -> None:
    expected_api_key = os.getenv("TEXT2SQL_GATEWAY_API_KEY")
    if not expected_api_key:
        return

    expected_header = f"Bearer {expected_api_key}"
    if authorization != expected_header:
        raise HTTPException(
            status_code=401,
            detail="Invalid Text2SQL gateway bearer token.",
        )


def current_gateway_mode() -> str:
    backend = os.getenv("TEXT2SQL_GATEWAY_BACKEND", "mock").lower()
    if backend == "ollama":
        return "text2sql_gateway_ollama_v1"
    if backend == "openai":
        return "text2sql_gateway_openai_v1"
    if backend == "gemini":
        return "text2sql_gateway_gemini_v1"
    if backend in {"dual", "gemini_openai_fallback"}:
        return "text2sql_gateway_gemini_openai_fallback_v1"
    return DEFAULT_GATEWAY_MODE
