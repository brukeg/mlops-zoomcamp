import os


def get_model_location(run_id):
    model_location = os.getenv('MODEL_LOCATION')
    if model_location is not None:
        return model_location
    model_bucket = os.getenv(
        'MODEL_BUCKET', 'mlflow-artifacts-remote-bruke-720881264075-us-west-2-an'
    )
    run_id = os.getenv('RUN_ID', run_id)
    return f's3://{model_bucket}/1/{run_id}/artifacts/model'


def load_model(run_id):
    import mlflow  # pylint: disable=import-outside-toplevel

    model_path = get_model_location(run_id)
    return mlflow.pyfunc.load_model(model_path)


class ModelService:
    def __init__(self, model, model_version=None):
        self.model = model
        self.model_version = model_version

    def prepare_features(self, ride):
        features = {}
        features['PU_DO'] = f"{ride['PULocationID']}_{ride['DOLocationID']}"
        features['trip_distance'] = ride['trip_distance']
        return features

    def predict(self, features):
        preds = self.model.predict(features)
        return float(preds[0])

    def predict_ride(self, ride):
        features = self.prepare_features(ride)
        return self.predict(features)


def init(run_id: str):
    model = load_model(run_id)
    return ModelService(model=model, model_version=run_id)
