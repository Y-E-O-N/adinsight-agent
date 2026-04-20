# =============================================================================
# infra/airflow/Dockerfile
# 베이스: apache/airflow:2.9.3-python3.11 (arm64 멀티아치 지원)
# 추가: requirements.txt 의 패키지 설치
# =============================================================================

ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# FROM 이후 스테이지에서 ARG 재선언 (Docker ARG 스코프 규칙)
ARG AIRFLOW_VERSION=2.9.3
ARG PYTHON_VERSION=3.11

# constraints 파일로 의존성 충돌 방지 (Airflow 공식 권장 패턴)
ARG CONSTRAINTS_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# requirements.txt 를 이미지 안으로 복사
COPY requirements.txt /tmp/requirements.txt

# airflow 유저로 패키지 설치 (airflow 이미지의 기본 유저)
# --no-cache-dir : pip 캐시 저장 안 함 -> 이미지 크기 절약
# -c : constraints 파일로 버전 충돌 방지
RUN pip install --no-cache-dir \
    -r /tmp/requirements.txt \
    -c "${CONSTRAINTS_URL}"
