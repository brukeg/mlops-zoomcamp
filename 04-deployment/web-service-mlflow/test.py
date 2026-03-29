import requests

ride = {
    "PULocationID": 10,
    "DOLocationID": 50,
    "trip_distance": 40
}

url = 'http://ec2-16-144-74-163.us-west-2.compute.amazonaws.com:9696/predict'
response = requests.post(url, json=ride)
print(response.json())