import requests
import json

url = 'http://127.0.0.1:5000/api/compare'
headers = {'Content-Type': 'application/json'}
payload = {'productIds': [1,2]}

r = requests.post(url, json=payload, headers=headers)
print('status:', r.status_code)
print('headers:', r.headers.get('Content-Type'))
try:
    print('json:', json.dumps(r.json(), indent=2))
except Exception as e:
    print('text:', r.text)
