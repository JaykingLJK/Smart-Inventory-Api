import requests
url_1 = "http://127.0.0.1:5000/listings"
url_2 = "http://127.0.0.1:5000/recipes"
url_3 = "http://127.0.0.1:5000/recom"
data_1_POST = {
    "item":"ljk",
    "expiry_date":"2021-10-06 00:00:05",
    "amount": 11
}
data_1_DELETE = {
    "item":"ljk",
    "amount":11
}
data_1_PUT = {
    "id": 14,
    "item": "Fish",
    "expiry_date": "2021-10-07 00:00:05",
    "amount": 7
}

data_2_POST = {
    "name":"my favorite dish",
    "ingredient_1":"love",
    "ingredient_2":"peace",
    "ingredient_3":"creation",
    "ingredient_4": None
}
data_2_DELETE = {
    "id": 1
}

data_2_PUT = {
    "id":1,
    "name": "nonono",
    "ingredient_1": "nononono",
    "ingredient_2": None,
    "ingredient_3": None,
    "ingredient_4": None
}
# response_1_GET = requests.get(url=url_1)
# response_1_POST = requests.post(url=url_1, json=data_1_POST)
# response_1_DELETE = requests.delete(url=url_1,json=data_1_DELETE)
# response_1_PUT = requests.put(url=url_1, json=data_1_PUT)
# response_2_GET = requests.get(url=url_2)
# response_2_POST = requests.post(url=url_2, json=data_2_POST)
# response_2_PUT = requests.put(url=url_2, json=data_2_PUT)
# response_2_DELETE = requests.delete(url=url_2, json=data_2_DELETE)
# response_3_GET = requests.get(url=url_3)

# print(response_1_GET.content)
# print(response_1_POST.content)
# print(response_1_DELETE.content)
# print(response_1_PUT.content)
# print(response_2_GET.content)
# print(response_2_POST.content)
# print(response_2_PUT.content)
# print(response_2_DELETE.content)
# print(response_3_GET.content)




# a = ['a', None, None]
# for b in a:
#     if b != a:
#         print('None')
