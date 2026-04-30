# isort: skip_file

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch  # pylint: disable=wrong-import-position

from conftest import ModelMock  # pylint: disable=wrong-import-position

import model  # pylint: disable=wrong-import-position

with patch('model.load_model', return_value=MagicMock()):
    import app  # pylint: disable=wrong-import-position


def test_predict_endpoint():
    with patch('app.model_service', model.ModelService(ModelMock(12.5))):
        client = app.app.test_client()
        ride = {
            'PULocationID': 130,
            'DOLocationID': 205,
            'trip_distance': 3.66,
        }
        response = client.post('/predict', json=ride)
        assert response.status_code == 200
        result = response.get_json()
        assert 'duration' in result
        assert isinstance(result['duration'], float)
        assert 0 < result['duration'] < 100
        assert 'model_version' in result
