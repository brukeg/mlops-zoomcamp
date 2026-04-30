import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from conftest import ModelMock  # pylint: disable=wrong-import-position

import model  # pylint: disable=wrong-import-position


def test_prepare_features():
    model_service = model.ModelService(None)

    ride = {
        'PULocationID': 130,
        'DOLocationID': 205,
        'trip_distance': 3.66,
    }

    actual_features = model_service.prepare_features(ride)

    expected_features = {
        'PU_DO': '130_205',
        'trip_distance': 3.66,
    }

    assert actual_features == expected_features


def test_predict():
    model_mock = ModelMock(10.0)
    model_service = model.ModelService(model_mock)

    features = {
        'PU_DO': '130_205',
        'trip_distance': 3.66,
    }

    actual_prediction = model_service.predict(features)
    expected_prediction = 10.0

    assert actual_prediction == expected_prediction


def test_predict_ride():
    model_mock = ModelMock(10.0)
    model_service = model.ModelService(model_mock)

    ride = {
        'PULocationID': 130,
        'DOLocationID': 205,
        'trip_distance': 3.66,
    }

    actual_prediction = model_service.predict_ride(ride)
    expected_prediction = 10.0

    assert actual_prediction == expected_prediction
