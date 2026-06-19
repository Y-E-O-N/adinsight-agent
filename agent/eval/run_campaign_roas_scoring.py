import os
from dataclasses import dataclass
from datetime import date

import psycopg

TRAINING_TABLE = "features.feature_campaign_roas_training_set"
SCORING_TABLE = "features.feature_campaign_roas_scoring_set"
PREDICTION_TABLE = "features.campaign_roas_baseline_predictions"
MODEL_NAME = "objective_mean_roas_baseline_v1"


@dataclass(frozen=True)
class TrainingRow:
    objective: str
    label_roas: float


@dataclass(frozen=True)
class ScoringRow:
    scoring_snapshot_date: date
    campaign_id: str
    region: str
    category: str
    objective: str


@dataclass(frozen=True)
class PredictionRow:
    scoring_snapshot_date: date
    campaign_id: str
    model_name: str
    predicted_roas: float
    prediction_reason: str
    training_rows_used: int


def main() -> None:
    training_rows = fetch_training_rows()
    scoring_rows = fetch_scoring_rows()

    if not training_rows:
        raise SystemExit(f"No rows found in {TRAINING_TABLE}.")

    if not scoring_rows:
        raise SystemExit(f"No rows found in {SCORING_TABLE}.")

    global_mean = calculate_global_mean(training_rows)
    objective_means = calculate_objective_means(training_rows)

    predictions = [
        score_campaign(row, global_mean, objective_means, len(training_rows))
        for row in scoring_rows
    ]

    write_predictions(predictions)
    print_summary(predictions)


def fetch_training_rows() -> list[TrainingRow]:
    sql = f"""
        select
            objective,
            label_roas
        from {TRAINING_TABLE}
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [
            TrainingRow(
                objective=record[0],
                label_roas=float(record[1]),
            )
            for record in cur.fetchall()
        ]


def fetch_scoring_rows() -> list[ScoringRow]:
    sql = f"""
        select
            scoring_snapshot_date,
            campaign_id,
            region,
            category,
            objective
        from {SCORING_TABLE}
        order by campaign_id
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [
            ScoringRow(
                scoring_snapshot_date=record[0],
                campaign_id=record[1],
                region=record[2],
                category=record[3],
                objective=record[4],
            )
            for record in cur.fetchall()
        ]


def calculate_global_mean(rows: list[TrainingRow]) -> float:
    return sum(row.label_roas for row in rows) / len(rows)


def calculate_objective_means(rows: list[TrainingRow]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}

    for row in rows:
        grouped.setdefault(row.objective, []).append(row.label_roas)

    return {
        objective: sum(values) / len(values)
        for objective, values in grouped.items()
    }


def score_campaign(
    row: ScoringRow,
    global_mean: float,
    objective_means: dict[str, float],
    training_rows_used: int,
) -> PredictionRow:
    if row.objective in objective_means:
        predicted_roas = objective_means[row.objective]
        reason = f"objective_mean:{row.objective}"
    else:
        predicted_roas = global_mean
        reason = "global_mean_fallback"

    return PredictionRow(
        scoring_snapshot_date=row.scoring_snapshot_date,
        campaign_id=row.campaign_id,
        model_name=MODEL_NAME,
        predicted_roas=predicted_roas,
        prediction_reason=reason,
        training_rows_used=training_rows_used,
    )


def write_predictions(rows: list[PredictionRow]) -> None:
    create_sql = f"""
        create table if not exists {PREDICTION_TABLE} (
            scoring_snapshot_date date not null,
            campaign_id text not null,
            model_name text not null,
            predicted_roas numeric not null,
            prediction_reason text not null,
            training_rows_used integer not null,
            prediction_generated_at_utc timestamptz not null default now(),
            primary key (scoring_snapshot_date, campaign_id, model_name)
        )
    """

    delete_sql = f"""
        delete from {PREDICTION_TABLE}
        where scoring_snapshot_date = %s
          and model_name = %s
    """

    insert_sql = f"""
        insert into {PREDICTION_TABLE} (
            scoring_snapshot_date,
            campaign_id,
            model_name,
            predicted_roas,
            prediction_reason,
            training_rows_used
        )
        values (%s, %s, %s, %s, %s, %s)
    """

    snapshot_date = rows[0].scoring_snapshot_date

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(create_sql)
        cur.execute(delete_sql, (snapshot_date, MODEL_NAME))
        cur.executemany(
            insert_sql,
            [
                (
                    row.scoring_snapshot_date,
                    row.campaign_id,
                    row.model_name,
                    row.predicted_roas,
                    row.prediction_reason,
                    row.training_rows_used,
                )
                for row in rows
            ],
        )
        conn.commit()


def print_summary(rows: list[PredictionRow]) -> None:
    predicted_values = [row.predicted_roas for row in rows]
    min_roas = min(predicted_values)
    max_roas = max(predicted_values)
    avg_roas = sum(predicted_values) / len(predicted_values)

    print(
        f"predictions table={PREDICTION_TABLE}",
        f"model={MODEL_NAME}",
        f"rows={len(rows)}",
        f"snapshot_date={rows[0].scoring_snapshot_date}",
    )
    print(
        f"predicted_roas_min={min_roas:.4f}",
        f"predicted_roas_avg={avg_roas:.4f}",
        f"predicted_roas_max={max_roas:.4f}",
    )


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "adinsight"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


if __name__ == "__main__":
    main()
