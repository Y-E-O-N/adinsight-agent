# =============================================================================
# infra/superset/Dockerfile
# 베이스: apache/superset:4.0.2 (arm64 멀티아치 지원)
# 추가: Postgres 드라이버 + pgvector 클라이언트
# =============================================================================

FROM apache/superset:4.0.2

# pip 캐시 전역 비활성화 (이미지 크기 절약)
ENV PIP_NO_CACHE_DIR=1

# superset 이미지의 기본 유저는 superset(비root)
# 시스템 레벨 pip 설치를 위해 root로 전환 후 복귀
USER root

RUN pip install \
    psycopg2-binary==2.9.9 \
    pgvector==0.3.2

# 최소 권한 복귀 - 컨테이너가 root로 실행되지 않도록
USER superset