"""
sample_smoke_test DAG.

목적: docker-compose로 올라온 Postgres와 Airflow가 정상 통신하는지 검증.
     Airflow UI에서 수동 트리거 -> 'SELECT 1' 성공 -> 전체 스택 건강.

참고: 
- Airflow TaskFlow API (@dag 데코레이터 방식, Airflow 2.0+ 권장)
- PostgresOperator 는 deprecated -> SQLExecuteQueryOperator 사용
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator


@dag(
    dag_id="sample_smoke_test",
    description="Postgres 연결 + Airflow 기동 검증용 smoke test",
    schedule=None,  # 수동 트리거 전용 (자동 실행 X)
    start_date=datetime(2026, 1, 1),    # 고정 리터럴
    catchup=False,   # Backfill 방지
    tags=["phase1", "smoke"],
)
def sample_smoke_test():
    """스택 기동 검증용 최소 DAG - 'SELECT 1'만 실행."""
    SQLExecuteQueryOperator(
        task_id="select_one",
        conn_id="warehouse",    # docker-compose의 AIRFLOW_CONN_WAREHOUSE로 주입된 커넥션
        sql="SELECT 1;",
    )
    

sample_smoke_test()