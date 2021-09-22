from datetime import date
from re import I
from types import resolve_bases
import requests
import json
url = "http://127.0.0.1:5000/listings"
data = {
    "item_name":"ljk",
    "expiry_date":5,
    "amount":5
}
response = requests.post(url=url,json=data)
print(response.content)

