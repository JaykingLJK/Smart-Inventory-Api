from datetime import date
from re import I
from types import resolve_bases
import requests
import json
url = "http://127.0.0.1:5000/listings"
data = {
    "item":"ljk",
    "amount":5
}
response = requests.delete(url=url,json=data)
print(response.content)
