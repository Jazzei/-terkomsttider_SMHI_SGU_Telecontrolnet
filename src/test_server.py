import requests
# print(requests.get('http://127.0.0.1:8000/items/56').json())
print(requests.get('http://127.0.0.1:8000/items?name=test').json())