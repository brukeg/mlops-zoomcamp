import os

import requests

PREDICT_URL = os.getenv('PREDICT_URL', 'http://44.245.50.220:9696/predict')

RIDE = {
    'PULocationID': 130,
    'DOLocationID': 205,
    'trip_distance': 3.66,
}


def test_predict_endpoint():
    try:
        response = requests.post(PREDICT_URL, json=RIDE, timeout=10)
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            'Could not reach prediction service. Is EC2 running and the container started?'
        ) from e

    assert response.status_code == 200
    result = response.json()
    assert 'duration' in result
    assert isinstance(result['duration'], float)
    assert 0 < result['duration'] < 100
    assert 'model_version' in result
