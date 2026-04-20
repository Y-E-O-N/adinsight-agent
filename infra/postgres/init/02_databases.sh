#!/usr/bin/env bash
# =============================================================================
# 02_databases.sh
# -----------------------------------------------------------------------------
# 목적: 추가 DB (airflow_meta, superset_meta) + Phase 6 Text2SQL 용
#       읽기 전용 role (agent_readonly) 생성 및 권한 부여.
# 실행 시점: /docker-entrypoint-initdb.d/ 에서 01_extensions.sql 다음에 자동 실행.
# 재실행 안전: \gexec 트릭 + DO 블록으로 idempotent.
# =============================================================================
set -euo pipefail

# heredoc 내부의 ${VAR} 는 bash 가 확장해서 완성된 SQL 을 psql 에 전달.
# -v ON_ERROR_STOP=1 : SQL 오류 시 즉시 중단 (반쪽 초기화 방지).
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL

    -- ---------------------------------------------------------------------------
    -- Airflow / Superset 메타데이터 DB 생성
    -- Postgres 는 CREATE DATABASE IF NOT EXISTS 미지원 → \gexec 트릭으로 조건부 실행
    -- ---------------------------------------------------------------------------
    SELECT 'CREATE DATABASE ${AIRFLOW_DB}'
     WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${AIRFLOW_DB}')\gexec

    SELECT 'CREATE DATABASE ${SUPERSET_DB}'
     WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${SUPERSET_DB}')\gexec

    -- ---------------------------------------------------------------------------
    -- Phase 6 Text2SQL Agent 전용 읽기 전용 role
    -- ROLE 도 IF NOT EXISTS 미지원 → DO 블록(anonymous PL/pgSQL)으로 idempotent 처리
    -- \$\$ 는 bash 이스케이프 → psql 에는 \$\$ (dollar-quoting) 로 전달됨
    -- ---------------------------------------------------------------------------
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${AGENT_DB_USER}') THEN
            CREATE ROLE ${AGENT_DB_USER} WITH LOGIN PASSWORD '${AGENT_DB_PASSWORD}';
        END IF;
    END
    \$\$;

    -- ---------------------------------------------------------------------------
    -- 권한 부여 (3단 계층: DB → SCHEMA → TABLES)
    -- ALTER DEFAULT PRIVILEGES 가 "미래에 생길 테이블" 에도 SELECT 를 자동 부여
    -- ---------------------------------------------------------------------------
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${AGENT_DB_USER};
    GRANT USAGE ON SCHEMA public TO ${AGENT_DB_USER};
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${AGENT_DB_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT ON TABLES TO ${AGENT_DB_USER};

EOSQL