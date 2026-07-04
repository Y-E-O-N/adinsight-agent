"""Instagram collection DAG common utilities.
    Phase 2B에서 daily collect / backfill DAG가 함께 쓰는 운영 함수 모음.
"""

from __future__ import annotations

import os
from datetime import date

import psycopg
from airflow.models import Variable

WATERMARK_VARIABLE_KEY = "ig_collect_last_watermark"

def get_watermark(default: str | None = None) -> str | None:
    """Airflow Variable에서 마지막 수집 완료 날짜를 읽는다"""
    return Variable.get(WATERMARK_VARIABLE_KEY, default_var=default)

def set_watermark(date_str: str | date) -> str:
    """마지막 수집 완료 날짜를 Airflow Variable에 저장한다"""
    value = date_str.isoformat() if isinstance(date_str, date) else date_str
    Variable.set(WATERMARK_VARIABLE_KEY, value)
    return value

def _postgres_dsn() -> str:
    """Airflow 환경변수로 Postgres 접속 문자열을 만든다"""
    return (
        f"host={os.environ.get('POSTGRES_HOST', 'postgres')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ['POSTGRES_DB']} "
        f"user={os.environ['POSTGRES_USER']} "
        f"password={os.environ['POSTGRES_PASSWORD']}"
    )

def get_today_collected_count() -> int:
    """UTC 기준 오늘 raw.ig_posts에 적재된 게시물 수를 센다"""
    sql = """
        SELECT COUNT(*)
        FROM raw.ig_posts
        WHERE collected_at >= date_trunc('day', now())
    """

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        cur.execute(sql)
        result = cur.fetchone()

    return int(result[0]) if result else 0

def get_weekly_avg_count() -> float:
    """UTC 기준 최근 7일 일평균 수집 게시물 수를 계산한다."""
    sql = """
        SELECT COUNT(*) / 7.0
        FROM raw.ig_posts
        WHERE collected_at >= date_trunc('day', now()) - INTERVAL '6 days'
    """

    with psycopg.connect(_postgres_dsn()) as conn, conn.cursor() as cur:
        cur.execute(sql)
        result = cur.fetchone()

    return float(result[0]) if result and result[0] is not None else 0.0

def check_freshness(min_ratio: float = 0.3) -> dict[str, float | int | str]:
    """오늘 수집량이 0건이거나 최근 평균 대비 급감했는지 확인한다"""
    today_count = get_today_collected_count()
    weekly_avg = get_weekly_avg_count()

    if today_count == 0:
        raise ValueError("freshness check failed: today collected count is 0")

    if weekly_avg > 0 and today_count < weekly_avg * min_ratio:
        return {
            "status": "warning",
            "today_count": today_count,
            "weekly_avg": weekly_avg,
            "min_ratio": min_ratio,
            "message": "today collected count is below weekly average threshold",
        }

    return {
        "status": "ok",
        "today_count": today_count,
        "weekly_avg": weekly_avg,
        "min_ratio": min_ratio,
        "message": "freshness check passed",
    }
