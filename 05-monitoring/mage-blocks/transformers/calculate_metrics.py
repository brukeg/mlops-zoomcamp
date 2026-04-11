import os
import datetime
import pandas as pd
import psycopg2
from evidently import DataDefinition, Dataset, Report
from evidently.metrics import ValueDrift, DriftedColumnsCount, MissingValueCount

BEGIN = datetime.datetime(2022, 2, 1, 0, 0)

RDS_HOST = 'mlflow-backend-db.c1aw8egmm7x1.us-west-2.rds.amazonaws.com'
RDS_DB = 'monitoring'
RDS_USER = 'mlflow'
RDS_PASSWORD = os.environ.get('RDS_PASSWORD')

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS taxi_monitoring_metrics (
    timestamp           TIMESTAMP,
    prediction_drift    FLOAT,
    num_drifted_columns INTEGER,
    share_missing_values FLOAT
);
"""

DATA_DEFINITION = DataDefinition(
    numerical_columns=['trip_distance', 'prediction'],
    categorical_columns=['PU_DO']
)

REPORT = Report(metrics=[
    ValueDrift(column='prediction'),
    DriftedColumnsCount(),
    MissingValueCount(column='prediction'),
])


@transformer
def calculate_metrics(data, *args, **kwargs):
    reference_df, batches = data

    reference_dataset = Dataset.from_pandas(reference_df, data_definition=DATA_DEFINITION)

    conn = psycopg2.connect(
        host=RDS_HOST,
        port=5432,
        dbname=RDS_DB,
        user=RDS_USER,
        password=RDS_PASSWORD,
        sslmode='require'
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE)

    for batch in batches:
        i = batch['day_index'].iloc[0]
        timestamp = BEGIN + datetime.timedelta(i)

        current_dataset = Dataset.from_pandas(batch, data_definition=DATA_DEFINITION)
        snapshot = REPORT.run(reference_data=reference_dataset, current_data=current_dataset)
        result = snapshot.dict()

        prediction_drift = result['metrics'][0]['value']
        num_drifted_columns = result['metrics'][1]['value']['count']
        share_missing_values = result['metrics'][2]['value']['share']

        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO taxi_monitoring_metrics
                   (timestamp, prediction_drift, num_drifted_columns, share_missing_values)
                   VALUES (%s, %s, %s, %s)""",
                (timestamp, prediction_drift, num_drifted_columns, share_missing_values)
            )

        print(f"Day {i}: drift={prediction_drift:.4f}, drifted_cols={num_drifted_columns}, missing={share_missing_values:.4f}")

    conn.close()
    print("All metrics written to RDS")
    return batches
