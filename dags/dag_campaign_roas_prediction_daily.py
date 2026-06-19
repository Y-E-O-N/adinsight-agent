"""
Phase 5 - Campaign ROAS prediction daily refresh DAG

목적:
    - campaign ROAS feature table을 최신 dbt 모델 기준으로 재생성한다.
    - baseline scoring script를 실행해 daily prediction output을 만든다.
    - prediction monitor mart를 갱신하고 품질 테스트를 실행한다.
    - 운영/포트폴리오용 metrics JSONL에 row count와 error summary를 남긴다.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import psycopg
from airflow.decorators import dag, task

DBT_PROJECT_DIR = "/opt/dbt"
DBT_PROFILES_DIR = "/opt/dbt"
METRICS_PATH = Path("/opt/airflow/metrics/run_results.jsonl")


def run_command(command: list[str], cwd: str | None = None) -> None:
    """Airflow task 로그에 stdout/stderr를 그대로 남기면서 subprocess를 실행한다."""
    print(f"[campaign_roas_prediction] command={' '.join(command)} cwd={cwd}")
    subprocess.run(command, cwd=cwd, check=True)


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adinsight"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


@dag(
    dag_id="campaign_roas_prediction_daily",
    description="Phase 5: Refresh campaign ROAS features, baseline predictions, and monitor mart",
    schedule="0 22 * * *",
    start_date=datetime(2026, 6, 19),
    catchup=False,
    tags=["phase5", "campaign", "roas", "prediction", "dbt"],
)
def campaign_roas_prediction_daily_dag() -> None:
    """Campaign ROAS prediction monitor를 매일 재계산한다."""

    @task
    def refresh_feature_tables() -> str:
        """training/scoring feature table을 dbt로 재생성한다."""
        run_command(
            [
                "dbt",
                "run",
                "--profiles-dir",
                DBT_PROFILES_DIR,
                "--select",
                "feature_campaign_roas_training_set",
                "feature_campaign_roas_scoring_set",
            ],
            cwd=DBT_PROJECT_DIR,
        )
        return "feature_tables_refreshed"

    @task
    def score_campaign_roas() -> str:
        """feature table을 읽어 baseline prediction output table을 갱신한다."""
        run_command(
            ["python", "-m", "agent.eval.run_campaign_roas_scoring"],
            cwd="/opt/airflow",
        )
        return "campaign_roas_scored"

    @task
    def refresh_monitor_mart() -> str:
        """prediction output과 실제 ROAS를 결합한 monitoring mart를 재생성한다."""
        run_command(
            [
                "dbt",
                "run",
                "--profiles-dir",
                DBT_PROFILES_DIR,
                "--select",
                "mart_campaign_roas_prediction_monitor",
            ],
            cwd=DBT_PROJECT_DIR,
        )
        return "monitor_mart_refreshed"

    @task
    def run_quality_tests() -> str:
        """feature/monitor 모델의 dbt tests를 실행한다."""
        run_command(
            [
                "dbt",
                "test",
                "--profiles-dir",
                DBT_PROFILES_DIR,
                "--select",
                "feature_campaign_roas_training_set",
                "feature_campaign_roas_scoring_set",
                "mart_campaign_roas_prediction_monitor",
            ],
            cwd=DBT_PROJECT_DIR,
        )
        return "quality_tests_passed"

    @task
    def record_prediction_metrics() -> dict[str, float | int | str | None]:
        """monitor mart summary를 JSONL metrics로 저장한다."""
        sql = """
            select
                count(*) as rows,
                min(scoring_snapshot_date)::text as min_snapshot_date,
                max(scoring_snapshot_date)::text as max_snapshot_date,
                round(avg(absolute_roas_prediction_error)::numeric, 4) as mae,
                round(avg(roas_prediction_error)::numeric, 4) as bias,
                round(min(predicted_roas)::numeric, 4) as predicted_roas_min,
                round(avg(predicted_roas)::numeric, 4) as predicted_roas_avg,
                round(max(predicted_roas)::numeric, 4) as predicted_roas_max
            from marts.mart_campaign_roas_prediction_monitor
        """

        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()

        record = {
            "phase": "p5",
            "step": "campaign_roas_prediction_daily",
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "dag_id": "campaign_roas_prediction_daily",
            "rows": int(row[0]),
            "min_snapshot_date": row[1],
            "max_snapshot_date": row[2],
            "mae": float(row[3]) if row[3] is not None else None,
            "bias": float(row[4]) if row[4] is not None else None,
            "predicted_roas_min": float(row[5]) if row[5] is not None else None,
            "predicted_roas_avg": float(row[6]) if row[6] is not None else None,
            "predicted_roas_max": float(row[7]) if row[7] is not None else None,
        }

        METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with METRICS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"[campaign_roas_prediction] metrics={record}")
        return record

    features = refresh_feature_tables()
    predictions = score_campaign_roas()
    monitor = refresh_monitor_mart()
    tests = run_quality_tests()
    metrics = record_prediction_metrics()

    features >> predictions >> monitor >> tests >> metrics


campaign_roas_prediction_daily_dag()
