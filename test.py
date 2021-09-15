from datetime import date
from re import I
import requests
import json
url = "http://127.0.0.1:5000/listings"
data = {
    "item_name":"ljk",
    "expiry_date":5,
    "amount":5
}
payload = json.dumps(data)
response = requests.post(url=url,json=payload)
print(response.content)