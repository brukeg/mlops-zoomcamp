import os
import pickle

import mlflow
import xgboost as xgb
from sklearn.metrics import root_mean_squared_error


@transformer
def train_model(data, *args, **kwargs):
    X_train, X_val, y_train, y_val, dv = data

    MLFLOW_EC2_HOST = os.environ.get("MLFLOW_EC2_HOST", "localhost")
    mlflow.set_tracking_uri(f"http://{MLFLOW_EC2_HOST}:5000")
    mlflow.set_experiment("nyc-taxi-experiment")

    with mlflow.start_run() as run:
        train = xgb.DMatrix(X_train, label=y_train)
        valid = xgb.DMatrix(X_val, label=y_val)

        best_params = {
            'learning_rate': 0.09585355369315604,
            'max_depth': 30,
            'min_child_weight': 1.060597050922164,
            'objective': 'reg:linear',
            'reg_alpha': 0.018060244040060163,
            'reg_lambda': 0.011658731377413597,
            'seed': 42
        }

        mlflow.log_params(best_params)

        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=5,
            evals=[(valid, 'validation')],
            early_stopping_rounds=3
        )

        y_pred = booster.predict(valid)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        with open("/tmp/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact("/tmp/preprocessor.b", artifact_path="preprocessor")

        mlflow.xgboost.log_model(booster, artifact_path="models_mlflow")

        return run.info.run_id