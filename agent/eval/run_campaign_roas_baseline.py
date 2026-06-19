import os
from dataclasses import dataclass

import numpy as np
import psycopg

FEATURE_TABLE = "features.feature_campaign_roas_training_set"


@dataclass(frozen=True)
class CampaignRoasRow:
    campaign_id: str
    objective: str
    label_roas: float


def main() -> None:
    rows = fetch_rows()

    if len(rows) < 2:
        raise SystemExit("Need at least 2 campaign rows to run leave-one-out evaluation.")

    labels = np.array([row.label_roas for row in rows], dtype=float)
    global_predictions = predict_leave_one_out_global_mean(labels)
    objective_predictions = predict_leave_one_out_objective_mean(rows, labels)

    print(f"dataset table={FEATURE_TABLE} rows={len(rows)}")
    print_metrics("global_mean", labels, global_predictions)
    print_metrics("objective_mean", labels, objective_predictions)


def fetch_rows() -> list[CampaignRoasRow]:
    sql = f"""
        select
            campaign_id,
            objective,
            label_roas
        from {FEATURE_TABLE}
        order by campaign_id
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return [
            CampaignRoasRow(
                campaign_id=record[0],
                objective=record[1],
                label_roas=float(record[2]),
            )
            for record in cur.fetchall()
        ]


def predict_leave_one_out_global_mean(labels: np.ndarray) -> np.ndarray:
    total = labels.sum()
    return np.array(
        [
            (total - label) / (len(labels) - 1)
            for label in labels
        ],
        dtype=float,
    )


def predict_leave_one_out_objective_mean(
    rows: list[CampaignRoasRow],
    labels: np.ndarray,
) -> np.ndarray:
    global_predictions = predict_leave_one_out_global_mean(labels)
    predictions: list[float] = []

    for index, row in enumerate(rows):
        peer_labels = [
            peer.label_roas
            for peer_index, peer in enumerate(rows)
            if peer_index != index and peer.objective == row.objective
        ]

        if peer_labels:
            predictions.append(float(np.mean(peer_labels)))
        else:
            predictions.append(float(global_predictions[index]))

    return np.array(predictions, dtype=float)


def print_metrics(name: str, actual: np.ndarray, predicted: np.ndarray) -> None:
    residuals = actual - predicted
    mae = np.mean(np.abs(residuals))
    rmse = np.sqrt(np.mean(residuals**2))
    bias = np.mean(predicted - actual)

    print(
        f"model={name}",
        f"mae={mae:.4f}",
        f"rmse={rmse:.4f}",
        f"bias={bias:.4f}",
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
