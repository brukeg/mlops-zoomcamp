import os
import pickle
import datetime
import requests
import pandas as pd
import mlflow
import xgboost as xgb

MLFLOW_RUN_ID = '10709df52be546d98b12d158668a11fa'
MLFLOW_TRACKING_URI = f"http://{os.environ.get('MLFLOW_EC2_HOST', '172.31.24.14')}:5000"
S3_BUCKET = 'mlflow-artifacts-remote-bruke-720881264075-us-west-2-an'

BEGIN = datetime.datetime(2022, 2, 1, 0, 0)
NUM_DAYS = 27


def read_dataframe(year, month):
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'
    save_path = f'/tmp/green_tripdata_{year}-{month:02d}.parquet'
    resp = requests.get(url, stream=True, timeout=60)
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    df = pd.read_parquet(save_path)

    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)
    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    return df


@transformer
def score_batch(reference_df, *args, **kwargs):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Load DictVectorizer
    dv_path = mlflow.artifacts.download_artifacts(
        run_id=MLFLOW_RUN_ID,
        artifact_path='preprocessor/preprocessor.b'
    )
    with open(dv_path, 'rb') as f:
        dv = pickle.load(f)

    # Load XGBoost booster
    booster = mlflow.xgboost.load_model(f'runs:/{MLFLOW_RUN_ID}/models_mlflow')

    # Load Feb 2022 raw data
    raw_data = read_dataframe(2022, 2)

    # Score each daily batch
    batches = []
    for i in range(NUM_DAYS):
        day_start = BEGIN + datetime.timedelta(i)
        day_end = BEGIN + datetime.timedelta(i + 1)

        batch = raw_data[
            (raw_data.lpep_pickup_datetime >= day_start) &
            (raw_data.lpep_pickup_datetime < day_end)
        ].copy()

        if len(batch) == 0:
            continue

        dicts = batch[['PU_DO', 'trip_distance']].to_dict(orient='records')
        X = dv.transform(dicts)
        batch['prediction'] = booster.predict(xgb.DMatrix(X))
        batch['day_index'] = i
        batches.append(batch)

    print(f"Scored {len(batches)} daily batches")
    return reference_df, batches

