#!/usr/bin/env python
# coding: utf-8

import uuid

import pandas as pd
import mlflow
import argparse

from datetime import datetime
from dateutil.relativedelta import relativedelta


def generate_uuids(n):
    ride_ids = []
    for i in range(n):
        ride_ids.append(str(uuid.uuid4()))
    return ride_ids


def read_dataframe(filename: str):
    df = pd.read_parquet(filename)

    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.dt.total_seconds() / 60
    df = df[(df.duration >= 1) & (df.duration <= 60)]
    
    df['ride_id'] = generate_uuids(len(df))

    return df


def prepare_dictionaries(df: pd.DataFrame):
    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)
    
    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    categorical = ['PU_DO']
    numerical = ['trip_distance']
    dicts = df[categorical + numerical].to_dict(orient='records')
    return dicts


def load_model(run_id):
    logged_model = f'runs:/{run_id}/model'
    model = mlflow.pyfunc.load_model(logged_model)
    return model


def save_results(df, y_pred, run_id, output_file):
    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['lpep_pickup_datetime'] = df['lpep_pickup_datetime']
    df_result['PULocationID'] = df['PULocationID']
    df_result['DOLocationID'] = df['DOLocationID']
    df_result['actual_duration'] = df['duration']
    df_result['predicted_duration'] = y_pred
    df_result['diff'] = df_result['actual_duration'] - df_result['predicted_duration']
    df_result['model_version'] = run_id

    df_result.to_parquet(output_file, index=False)


def apply_model(input_file, run_id, output_file):
    print(f'reading the data from {input_file}...')
    df = read_dataframe(input_file)
    dicts = prepare_dictionaries(df)

    print(f'loading the model with RUN_ID={run_id}...')
    model = load_model(run_id)

    print(f'applying the model...')
    y_pred = model.predict(dicts)

    print(f'saving the result to {output_file}...')
    save_results(df, y_pred, run_id, output_file)
    return output_file


def get_paths(run_date, taxi_type, run_id):
    prev_month = run_date - relativedelta(months=1)
    year = prev_month.year
    month = prev_month.month 

    input_file = f's3://mlflow-artifacts-remote-bruke-720881264075-us-west-2-an/data/green/{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
    output_file = f's3://mlflow-artifacts-remote-bruke-720881264075-us-west-2-an/taxi_type={taxi_type}/year={year:04d}/month={month:02d}/{run_id}.parquet'

    return input_file, output_file


def ride_duration_prediction(taxi_type: str, run_id: str, run_date: datetime = None):
    input_file, output_file = get_paths(run_date, taxi_type, run_id)

    apply_model(
        input_file=input_file,
        run_id=run_id,
        output_file=output_file
    )


def run():
    parser = argparse.ArgumentParser(description='Batch score ride durations')

    parser.add_argument('--taxi-type', required=True, help='Type of taxi (e.g. green)')
    parser.add_argument('--year', type=int, required=True, help='Year of data to score (e.g. 2021)')
    parser.add_argument('--month', type=int, required=True, help='Month of data to score (e.g. 3)')
    parser.add_argument('--run-id', required=True, help='MLflow run ID')

    args = parser.parse_args()

    ride_duration_prediction(
        taxi_type=args.taxi_type,
        run_id=args.run_id,
        run_date=datetime(year=args.year, month=args.month, day=1)
    )


if __name__ == '__main__':
    run()
