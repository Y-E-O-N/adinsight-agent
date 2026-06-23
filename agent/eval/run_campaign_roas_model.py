from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import psycopg

FEATURE_TABLE = "features.feature_campaign_roas_training_set"
METRICS_PATH = Path("metrics/run_results.jsonl")
ARTIFACT_PATH = Path("agent/model_artifacts/campaign_roas_linear_v1.json")
MODEL_COMPARISON_NAME = "campaign_roas_model_comparison_v1"
LINEAR_MODEL_NAME = "linear_regression_numpy_v1"
BASELINE_NAME = "objective_mean_roas_baseline_v1"
RIDGE_ALPHA = 1.0
KNN_NEIGHBORS = 5

CATEGORICAL_FEATURES = ("region", "category", "objective")
NUMERIC_FEATURES = (
    "campaign_budget_krw",
    "duration_days",
    "attributed_posts",
    "distinct_posts",
    "distinct_creators",
    "paid_partnership_posts",
    "avg_observed_engagement_count",
    "high_engagement_posts",
    "viral_engagement_posts",
    "paid_partnership_post_rate",
    "high_engagement_post_rate",
    "viral_engagement_post_rate",
    "creator_diversity_rate",
)


@dataclass(frozen=True)
class CampaignRoasFeatureRow:
    campaign_id: str
    region: str
    category: str
    objective: str
    numeric_features: dict[str, float]
    label_roas: float


@dataclass(frozen=True)
class EvaluationMetrics:
    model_name: str
    rows: int
    mae: float
    rmse: float
    bias: float


def main() -> None:
    rows = fetch_rows()

    if len(rows) < 3:
        raise SystemExit("Need at least 3 campaign rows to run leave-one-out model evaluation.")

    actual = np.array([row.label_roas for row in rows], dtype=float)
    candidate_predictions = {
        "global_mean_baseline_v1": predict_leave_one_out_global_mean(actual),
        BASELINE_NAME: predict_leave_one_out_objective_mean(rows, actual),
        LINEAR_MODEL_NAME: predict_leave_one_out_linear(rows),
        "ridge_regression_numpy_v1": predict_leave_one_out_ridge(rows, alpha=RIDGE_ALPHA),
        "knn_regression_numpy_v1": predict_leave_one_out_knn(rows, neighbors=KNN_NEIGHBORS),
    }
    candidate_metrics = [
        calculate_metrics(model_name, actual, predictions)
        for model_name, predictions in candidate_predictions.items()
    ]
    candidate_metrics = sorted(candidate_metrics, key=lambda metrics: (metrics.mae, metrics.rmse))

    baseline_metrics = find_metrics(candidate_metrics, BASELINE_NAME)
    best_metrics = candidate_metrics[0]

    print(f"dataset table={FEATURE_TABLE} rows={len(rows)}")
    for metrics in candidate_metrics:
        print_metrics(metrics)

    print(
        "comparison",
        f"best_model={best_metrics.model_name}",
        f"mae_delta_vs_baseline={best_metrics.mae - baseline_metrics.mae:.4f}",
        f"rmse_delta_vs_baseline={best_metrics.rmse - baseline_metrics.rmse:.4f}",
    )

    write_metrics(baseline_metrics, best_metrics, candidate_metrics)
    export_linear_model_artifact(rows, ARTIFACT_PATH)


def fetch_rows() -> list[CampaignRoasFeatureRow]:
    selected_columns = [
        "campaign_id",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
        "label_roas",
    ]
    sql = f"""
        select
            {", ".join(selected_columns)}
        from {FEATURE_TABLE}
        order by campaign_id
    """

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        records = cur.fetchall()

    rows: list[CampaignRoasFeatureRow] = []
    for record in records:
        numeric_offset = 1 + len(CATEGORICAL_FEATURES)
        numeric_values = record[numeric_offset:numeric_offset + len(NUMERIC_FEATURES)]
        rows.append(
            CampaignRoasFeatureRow(
                campaign_id=record[0],
                region=record[1],
                category=record[2],
                objective=record[3],
                numeric_features={
                    feature_name: coerce_float(value)
                    for feature_name, value in zip(NUMERIC_FEATURES, numeric_values, strict=True)
                },
                label_roas=coerce_float(record[-1]),
            )
        )

    return rows


def predict_leave_one_out_objective_mean(
    rows: list[CampaignRoasFeatureRow],
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
        predictions.append(float(np.mean(peer_labels)) if peer_labels else float(global_predictions[index]))

    return np.array(predictions, dtype=float)


def predict_leave_one_out_global_mean(labels: np.ndarray) -> np.ndarray:
    total = labels.sum()
    return np.array(
        [
            (total - label) / (len(labels) - 1)
            for label in labels
        ],
        dtype=float,
    )


def predict_leave_one_out_ridge(
    rows: list[CampaignRoasFeatureRow],
    alpha: float,
) -> np.ndarray:
    predictions: list[float] = []

    for holdout_index, holdout_row in enumerate(rows):
        train_rows = [
            row
            for row_index, row in enumerate(rows)
            if row_index != holdout_index
        ]
        train_labels = np.array([row.label_roas for row in train_rows], dtype=float)

        train_matrix, holdout_matrix = build_design_matrices(train_rows, [holdout_row])
        coefficients = fit_ridge(train_matrix, train_labels, alpha=alpha)
        prediction = float((holdout_matrix @ coefficients)[0])
        predictions.append(prediction)

    return np.array(predictions, dtype=float)


def predict_leave_one_out_linear(rows: list[CampaignRoasFeatureRow]) -> np.ndarray:
    predictions: list[float] = []

    for holdout_index, holdout_row in enumerate(rows):
        train_rows = [
            row
            for row_index, row in enumerate(rows)
            if row_index != holdout_index
        ]
        train_labels = np.array([row.label_roas for row in train_rows], dtype=float)

        train_matrix, holdout_matrix = build_design_matrices(train_rows, [holdout_row])
        coefficients = fit_linear(train_matrix, train_labels)
        prediction = float((holdout_matrix @ coefficients)[0])
        predictions.append(prediction)

    return np.array(predictions, dtype=float)


def predict_leave_one_out_knn(
    rows: list[CampaignRoasFeatureRow],
    neighbors: int,
) -> np.ndarray:
    predictions: list[float] = []

    for holdout_index, holdout_row in enumerate(rows):
        train_rows = [
            row
            for row_index, row in enumerate(rows)
            if row_index != holdout_index
        ]
        train_labels = np.array([row.label_roas for row in train_rows], dtype=float)
        train_matrix, holdout_matrix = build_design_matrices(train_rows, [holdout_row])

        distances = np.linalg.norm(train_matrix[:, 1:] - holdout_matrix[:, 1:], axis=1)
        neighbor_count = min(neighbors, len(train_rows))
        nearest_indices = np.argsort(distances)[:neighbor_count]
        prediction = float(np.mean(train_labels[nearest_indices]))
        predictions.append(prediction)

    return np.array(predictions, dtype=float)


def build_design_matrices(
    train_rows: list[CampaignRoasFeatureRow],
    scoring_rows: list[CampaignRoasFeatureRow],
) -> tuple[np.ndarray, np.ndarray]:
    categories_by_feature = {
        feature_name: sorted({getattr(row, feature_name) for row in train_rows})
        for feature_name in CATEGORICAL_FEATURES
    }

    numeric_train = np.array(
        [
            [row.numeric_features[feature_name] for feature_name in NUMERIC_FEATURES]
            for row in train_rows
        ],
        dtype=float,
    )
    means = numeric_train.mean(axis=0)
    stds = numeric_train.std(axis=0)
    stds = np.where(stds == 0, 1.0, stds)

    return (
        build_design_matrix(train_rows, categories_by_feature, means, stds),
        build_design_matrix(scoring_rows, categories_by_feature, means, stds),
    )


def build_training_transform(rows: list[CampaignRoasFeatureRow]) -> tuple[dict[str, list[str]], np.ndarray, np.ndarray]:
    categories_by_feature = {
        feature_name: sorted({getattr(row, feature_name) for row in rows})
        for feature_name in CATEGORICAL_FEATURES
    }
    numeric_matrix = np.array(
        [
            [row.numeric_features[feature_name] for feature_name in NUMERIC_FEATURES]
            for row in rows
        ],
        dtype=float,
    )
    means = numeric_matrix.mean(axis=0)
    stds = numeric_matrix.std(axis=0)
    stds = np.where(stds == 0, 1.0, stds)
    return categories_by_feature, means, stds


def build_design_matrix(
    rows: list[CampaignRoasFeatureRow],
    categories_by_feature: dict[str, list[str]],
    means: np.ndarray,
    stds: np.ndarray,
) -> np.ndarray:
    matrix_rows: list[list[float]] = []

    for row in rows:
        numeric_values = np.array(
            [row.numeric_features[feature_name] for feature_name in NUMERIC_FEATURES],
            dtype=float,
        )
        standardized_values = ((numeric_values - means) / stds).tolist()
        categorical_values = []

        for feature_name, categories in categories_by_feature.items():
            row_value = getattr(row, feature_name)
            categorical_values.extend(1.0 if row_value == category else 0.0 for category in categories)

        matrix_rows.append([1.0, *standardized_values, *categorical_values])

    return np.array(matrix_rows, dtype=float)


def build_design_matrix_from_artifact(
    rows: list[CampaignRoasFeatureRow],
    artifact: dict[str, object],
) -> np.ndarray:
    transform = artifact["transform"]
    assert isinstance(transform, dict)

    categories_by_feature = transform["categories_by_feature"]
    numeric_means = transform["numeric_means"]
    numeric_stds = transform["numeric_stds"]

    assert isinstance(categories_by_feature, dict)
    assert isinstance(numeric_means, list)
    assert isinstance(numeric_stds, list)

    return build_design_matrix(
        rows,
        {
            str(feature_name): [str(category) for category in categories]
            for feature_name, categories in categories_by_feature.items()
        },
        np.array(numeric_means, dtype=float),
        np.array(numeric_stds, dtype=float),
    )


def fit_ridge(matrix: np.ndarray, labels: np.ndarray, alpha: float) -> np.ndarray:
    penalty = np.eye(matrix.shape[1], dtype=float) * alpha
    penalty[0, 0] = 0.0
    lhs = matrix.T @ matrix + penalty
    rhs = matrix.T @ labels

    try:
        return np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        return np.linalg.lstsq(lhs, rhs, rcond=None)[0]


def fit_linear(matrix: np.ndarray, labels: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(matrix, labels, rcond=None)[0]


def export_linear_model_artifact(
    rows: list[CampaignRoasFeatureRow],
    path: Path,
) -> None:
    categories_by_feature, means, stds = build_training_transform(rows)
    training_matrix = build_design_matrix(rows, categories_by_feature, means, stds)
    labels = np.array([row.label_roas for row in rows], dtype=float)
    coefficients = fit_linear(training_matrix, labels)

    artifact = {
        "model_name": LINEAR_MODEL_NAME,
        "feature_table": FEATURE_TABLE,
        "training_rows_used": len(rows),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "categorical_features": list(CATEGORICAL_FEATURES),
        "numeric_features": list(NUMERIC_FEATURES),
        "transform": {
            "categories_by_feature": categories_by_feature,
            "numeric_means": means.tolist(),
            "numeric_stds": stds.tolist(),
        },
        "coefficients": coefficients.tolist(),
        "known_limitation": "Fitted on 25 synthetic labeled campaign rows; benchmark artifact only.",
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"artifact path={path} model={LINEAR_MODEL_NAME} rows={len(rows)}")


def load_linear_model_artifact(path: Path = ARTIFACT_PATH) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def predict_with_linear_artifact(
    row: CampaignRoasFeatureRow,
    artifact: dict[str, object],
) -> float:
    coefficients = np.array(artifact["coefficients"], dtype=float)
    scoring_matrix = build_design_matrix_from_artifact([row], artifact)
    return float((scoring_matrix @ coefficients)[0])


def calculate_metrics(
    model_name: str,
    actual: np.ndarray,
    predicted: np.ndarray,
) -> EvaluationMetrics:
    residuals = actual - predicted
    return EvaluationMetrics(
        model_name=model_name,
        rows=len(actual),
        mae=float(np.mean(np.abs(residuals))),
        rmse=float(np.sqrt(np.mean(residuals**2))),
        bias=float(np.mean(predicted - actual)),
    )


def print_metrics(metrics: EvaluationMetrics) -> None:
    print(
        f"model={metrics.model_name}",
        f"rows={metrics.rows}",
        f"mae={metrics.mae:.4f}",
        f"rmse={metrics.rmse:.4f}",
        f"bias={metrics.bias:.4f}",
    )


def find_metrics(
    candidate_metrics: list[EvaluationMetrics],
    model_name: str,
) -> EvaluationMetrics:
    for metrics in candidate_metrics:
        if metrics.model_name == model_name:
            return metrics

    raise ValueError(f"Missing metrics for model={model_name}")


def write_metrics(
    baseline_metrics: EvaluationMetrics,
    best_metrics: EvaluationMetrics,
    candidate_metrics: list[EvaluationMetrics],
) -> None:
    record = {
        "phase": "p6",
        "step": "campaign_roas_model_comparison_v1",
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "feature_table": FEATURE_TABLE,
        "validation_strategy": "leave_one_out",
        "comparison_name": MODEL_COMPARISON_NAME,
        "best_model_name": best_metrics.model_name,
        "baseline_model_name": baseline_metrics.model_name,
        "rows": best_metrics.rows,
        "ridge_alpha": RIDGE_ALPHA,
        "knn_neighbors": KNN_NEIGHBORS,
        "best_model_mae": round(best_metrics.mae, 4),
        "best_model_rmse": round(best_metrics.rmse, 4),
        "best_model_bias": round(best_metrics.bias, 4),
        "baseline_mae": round(baseline_metrics.mae, 4),
        "baseline_rmse": round(baseline_metrics.rmse, 4),
        "baseline_bias": round(baseline_metrics.bias, 4),
        "mae_delta_vs_baseline": round(best_metrics.mae - baseline_metrics.mae, 4),
        "rmse_delta_vs_baseline": round(best_metrics.rmse - baseline_metrics.rmse, 4),
        "candidate_metrics": [
            {
                "model_name": metrics.model_name,
                "mae": round(metrics.mae, 4),
                "rmse": round(metrics.rmse, 4),
                "bias": round(metrics.bias, 4),
            }
            for metrics in candidate_metrics
        ],
        "boosting_models_deferred": ["lightgbm", "xgboost", "catboost"],
        "defer_reason": "Only 25 synthetic labeled campaign rows; boosting models are more useful after larger labeled data.",
        "known_limitation": "25 synthetic labeled campaign rows; benchmark only, not production performance evidence.",
    }

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with METRICS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def coerce_float(value: object) -> float:
    if value is None:
        return 0.0
    return float(value)


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
