import requests
import json

url = "http://localhost:8000/inference"
data = {
    "data": [["aa", 2, 2]],
    "model_version": "1"
}
response = requests.post(url, json=data)

print(response.status_code)
print(response.content)
