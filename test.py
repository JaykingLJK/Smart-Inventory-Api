import requests
url = "http://127.0.0.1:5000/listings"
data = {
    "item":"ljk",
    "amount":5
}
response = requests.delete(url=url,json=data)
print(response.content)

# a = ['a', None, None]
# for b in a:
#     if b != a:
#         print('None')
