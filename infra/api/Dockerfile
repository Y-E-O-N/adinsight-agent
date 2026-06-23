FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY agent ./agent
COPY api ./api
COPY data_generation ./data_generation
COPY metrics ./metrics

RUN pip install --no-cache-dir -e . && \
    useradd --create-home --shell /bin/bash appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
