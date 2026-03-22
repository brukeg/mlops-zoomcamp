import pandas as pd


def read_dataframe(year, month):
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'
    df = pd.read_parquet(url)

    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)

    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)

    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    return df


@data_loader
def load_data(*args, **kwargs):
    from datetime import datetime

    now = datetime.now()

    train_month = now.month - 2
    train_year = now.year
    if train_month <= 0:
        train_month += 12
        train_year -= 1

    val_month = now.month - 1
    val_year = now.year
    if val_month <= 0:
        val_month += 12
        val_year -= 1

    df_train = read_dataframe(2021, 1)
    df_val = read_dataframe(2021, 2)

    df_train = df_train.sample(n=10000, random_state=42)
    df_val = df_val.sample(n=10000, random_state=42)   
    return df_train, df_val