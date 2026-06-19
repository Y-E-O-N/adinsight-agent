import json
import os

from superset.app import create_app

db = None
SqlaTable = None
SqlMetric = None
TableColumn = None
Database = None
Dashboard = None
Slice = None


DATABASE_NAME = "AdInsight Warehouse"
DATASET_SCHEMA = "marts"
DATASET_TABLE = "mart_campaign_roas_prediction_monitor"
DATASET_NAME = DATASET_TABLE
CHART_NAME = "Campaign ROAS Prediction Monitor Table"
DASHBOARD_TITLE = "AdInsight Campaign ROAS Prediction Monitor"


COLUMNS = [
    ("scoring_snapshot_date", "DATE", True),
    ("model_name", "TEXT", False),
    ("campaign_id", "TEXT", False),
    ("campaign_name", "TEXT", False),
    ("region", "TEXT", False),
    ("category", "TEXT", False),
    ("objective", "TEXT", False),
    ("campaign_budget_krw", "NUMERIC", False),
    ("predicted_roas", "NUMERIC", False),
    ("actual_roas", "NUMERIC", False),
    ("roas_prediction_error", "NUMERIC", False),
    ("absolute_roas_prediction_error", "NUMERIC", False),
    ("net_payment_amount_krw", "NUMERIC", False),
    ("payment_events", "BIGINT", False),
    ("actual_roas_performance_tier", "TEXT", False),
    ("prediction_reason", "TEXT", False),
    ("training_rows_used", "INTEGER", False),
    ("prediction_generated_at_utc", "TIMESTAMP", True),
]


TABLE_COLUMNS = [
    "campaign_id",
    "campaign_name",
    "objective",
    "predicted_roas",
    "actual_roas",
    "absolute_roas_prediction_error",
    "prediction_reason",
]


def main() -> None:
    database = get_or_create_database()
    dataset = get_or_create_dataset(database)
    chart = get_or_create_table_chart(dataset)
    dashboard = get_or_create_dashboard(chart)

    db.session.commit()
    print(
        "created_or_updated",
        f"database={database.database_name}",
        f"dataset={dataset.table_name}",
        f"chart={chart.slice_name}",
        f"dashboard={dashboard.dashboard_title}",
    )


def get_or_create_database():
    database = (
        db.session.query(Database)
        .filter(Database.database_name == DATABASE_NAME)
        .one_or_none()
    )

    if database is None:
        database = Database(
            database_name=DATABASE_NAME,
            sqlalchemy_uri=build_sqlalchemy_uri(),
            expose_in_sqllab=True,
            allow_run_async=False,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
            allow_file_upload=False,
        )
        db.session.add(database)
    else:
        database.sqlalchemy_uri = build_sqlalchemy_uri()
        database.expose_in_sqllab = True

    return database


def get_or_create_dataset(database):
    dataset = (
        db.session.query(SqlaTable)
        .filter(
            SqlaTable.database_id == database.id,
            SqlaTable.schema == DATASET_SCHEMA,
            SqlaTable.table_name == DATASET_TABLE,
        )
        .one_or_none()
    )

    if dataset is None:
        dataset = SqlaTable(
            table_name=DATASET_TABLE,
            schema=DATASET_SCHEMA,
            database=database,
        )
        db.session.add(dataset)
        db.session.flush()

    dataset.description = (
        "Campaign ROAS baseline prediction과 actual synthetic ROAS를 비교하는 "
        "prediction monitoring mart."
    )
    existing_columns = {column.column_name: column for column in dataset.columns}
    for column_name, column_type, is_dttm in COLUMNS:
        column = existing_columns.get(column_name)
        if column is None:
            column = TableColumn(column_name=column_name)
            dataset.columns.append(column)

        column.type = column_type
        column.is_dttm = is_dttm
        column.groupby = True
        column.filterable = True

    existing_metrics = {metric.metric_name: metric for metric in dataset.metrics}
    count_metric = existing_metrics.get("count")
    if count_metric is None:
        count_metric = SqlMetric(metric_name="count")
        dataset.metrics.append(count_metric)

    count_metric.verbose_name = "COUNT(*)"
    count_metric.metric_type = "count"
    count_metric.expression = "COUNT(*)"

    return dataset


def get_or_create_table_chart(dataset):
    chart = (
        db.session.query(Slice)
        .filter(Slice.slice_name == CHART_NAME)
        .one_or_none()
    )

    if chart is None:
        chart = Slice(slice_name=CHART_NAME)
        db.session.add(chart)

    params = {
        "datasource": f"{dataset.id}__table",
        "viz_type": "table",
        "query_mode": "raw",
        "groupby": [],
        "time_grain_sqla": "P1D",
        "temporal_columns_lookup": {},
        "all_columns": TABLE_COLUMNS,
        "percent_metrics": [],
        "adhoc_filters": [],
        "order_by_cols": ['["absolute_roas_prediction_error", false]'],
        "row_limit": 1000,
        "server_page_length": 10,
        "order_desc": True,
        "table_timestamp_format": "smart_date",
        "show_cell_bars": True,
        "color_pn": True,
        "extra_form_data": {},
    }

    chart.viz_type = "table"
    chart.datasource_id = dataset.id
    chart.datasource_type = "table"
    chart.params = json.dumps(params)
    chart.query_context = json.dumps(
        {
            "datasource": {"id": dataset.id, "type": "table"},
            "force": False,
            "queries": [
                {
                    "filters": [],
                    "extras": {
                        "time_grain_sqla": "P1D",
                        "having": "",
                        "where": "",
                    },
                    "applied_time_extras": {},
                    "columns": TABLE_COLUMNS,
                    "orderby": [["absolute_roas_prediction_error", False]],
                    "annotation_layers": [],
                    "row_limit": 1000,
                    "series_limit": 0,
                    "order_desc": True,
                    "url_params": {},
                    "custom_params": {},
                    "custom_form_data": {},
                    "post_processing": [],
                }
            ],
            "form_data": params,
            "result_format": "json",
            "result_type": "full",
        }
    )

    return chart


def get_or_create_dashboard(chart):
    dashboard = (
        db.session.query(Dashboard)
        .filter(Dashboard.dashboard_title == DASHBOARD_TITLE)
        .one_or_none()
    )

    if dashboard is None:
        dashboard = Dashboard(dashboard_title=DASHBOARD_TITLE, published=False)
        db.session.add(dashboard)

    dashboard.slices = [chart]
    dashboard.position_json = json.dumps(build_dashboard_position(chart))

    return dashboard


def build_dashboard_position(chart: Slice) -> dict:
    return {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {
            "children": ["GRID_ID"],
            "id": "ROOT_ID",
            "type": "ROOT",
        },
        "GRID_ID": {
            "children": ["ROW-ROAS-MONITOR"],
            "id": "GRID_ID",
            "parents": ["ROOT_ID"],
            "type": "GRID",
        },
        "HEADER_ID": {
            "id": "HEADER_ID",
            "meta": {"text": DASHBOARD_TITLE},
            "type": "HEADER",
        },
        "ROW-ROAS-MONITOR": {
            "children": ["CHART-ROAS-MONITOR"],
            "id": "ROW-ROAS-MONITOR",
            "meta": {"0": "ROOT_ID", "background": "BACKGROUND_TRANSPARENT"},
            "type": "ROW",
            "parents": ["ROOT_ID", "GRID_ID"],
        },
        "CHART-ROAS-MONITOR": {
            "children": [],
            "id": "CHART-ROAS-MONITOR",
            "meta": {
                "chartId": chart.id,
                "height": 64,
                "sliceName": CHART_NAME,
                "uuid": str(chart.uuid),
                "width": 12,
            },
            "type": "CHART",
            "parents": ["ROOT_ID", "GRID_ID", "ROW-ROAS-MONITOR"],
        },
    }


def build_sqlalchemy_uri() -> str:
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    database = os.getenv("POSTGRES_DB", "adinsight")
    return f"postgresql+psycopg2://{user}:{password}@postgres:5432/{database}"


def run_with_app_context() -> None:
    global Dashboard
    global Database
    global Slice
    global SqlaTable
    global SqlMetric
    global TableColumn
    global db

    app = create_app()
    with app.app_context():
        from superset import db as superset_db
        from superset.connectors.sqla.models import (
            SqlaTable as SupersetSqlaTable,
        )
        from superset.connectors.sqla.models import (
            SqlMetric as SupersetSqlMetric,
        )
        from superset.connectors.sqla.models import (
            TableColumn as SupersetTableColumn,
        )
        from superset.models.core import Database as SupersetDatabase
        from superset.models.dashboard import Dashboard as SupersetDashboard
        from superset.models.slice import Slice as SupersetSlice

        db = superset_db
        SqlaTable = SupersetSqlaTable
        SqlMetric = SupersetSqlMetric
        TableColumn = SupersetTableColumn
        Database = SupersetDatabase
        Dashboard = SupersetDashboard
        Slice = SupersetSlice

        main()


if __name__ == "__main__":
    run_with_app_context()
