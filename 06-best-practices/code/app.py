import os

from flask import Flask, jsonify, request

import model

RUN_ID = os.getenv('RUN_ID', '44ce31d3a5234ae68e95c79221cbfadc')

model_service = model.init(run_id=RUN_ID)

app = Flask('duration-prediction')


@app.route('/predict', methods=['POST'])
def predict_endpoint():
    ride = request.get_json()
    prediction = model_service.predict_ride(ride)
    result = {'duration': prediction, 'model_version': RUN_ID}
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=9696)
