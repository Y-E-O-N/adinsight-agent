from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from agent.text2sql.llm_client import MockSqlGenerationClient, SqlGenerationRequest

GATEWAY_MODE = "text2sql_gateway_mock_v1"

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


@app.get("/health", response_model=GatewayHealthResponse)
def health() -> GatewayHealthResponse:
    return GatewayHealthResponse(
        status="ok",
        service="adinsight-text2sql-gateway",
        mode=GATEWAY_MODE,
    )


@app.post("/text2sql/generate", response_model=GenerateSqlResponse)
def generate_sql(
    request: GenerateSqlRequest,
    authorization: str | None = Header(default=None),
) -> GenerateSqlResponse:
    verify_gateway_auth(authorization)
    generation = MockSqlGenerationClient().generate_sql(
        SqlGenerationRequest(
            question=request.question,
            schema_context=request.schema_context,
        )
    )

    return GenerateSqlResponse(
        answerability=generation.answerability,
        sql=generation.sql,
        expected_tables=list(generation.expected_tables),
        reason=generation.reason,
        mode=GATEWAY_MODE,
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
