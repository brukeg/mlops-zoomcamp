import os
import pickle
import requests
import pandas as pd
import mlflow
import xgboost as xgb

S3_BUCKET = 'mlflow-artifacts-remote-bruke-720881264075-us-west-2-an'
REFERENCE_S3_KEY = 'monitoring/reference.parquet'
MLFLOW_RUN_ID = '10709df52be546d98b12d158668a11fa'
MLFLOW_TRACKING_URI = f"http://{os.environ.get('MLFLOW_EC2_HOST', '172.31.24.14')}:5000"


def read_dataframe(year, month):
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'
    save_path = f'/tmp/green_tripdata_{year}-{month:02d}.parquet'
    resp = requests.get(url, stream=True, timeout=60)
    with open(save_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    df = pd.read_parquet(save_path)

    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)
    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)
    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    return df


@data_loader
def prepare_reference_data(*args, **kwargs):
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    # Load DictVectorizer from MLflow artifacts
    dv_path = mlflow.artifacts.download_artifacts(
        run_id=MLFLOW_RUN_ID,
        artifact_path='preprocessor/preprocessor.b'
    )
    with open(dv_path, 'rb') as f:
        dv = pickle.load(f)

    # Load XGBoost booster
    model_uri = f'runs:/{MLFLOW_RUN_ID}/models_mlflow'
    booster = mlflow.xgboost.load_model(model_uri)

    # Feb 2021 — matches the val split used during training
    df = read_dataframe(2021, 2)
    df = df.sample(n=10000, random_state=42)

    # Score
    dicts = df[['PU_DO', 'trip_distance']].to_dict(orient='records')
    X = dv.transform(dicts)
    df['prediction'] = booster.predict(xgb.DMatrix(X))

    # Write to S3
    s3_path = f's3://{S3_BUCKET}/{REFERENCE_S3_KEY}'
    df.to_parquet(s3_path, index=False)
    print(f"Reference data written to {s3_path} — {len(df)} rows")

    return df
    