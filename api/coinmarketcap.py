import requests

def get_top():
    url = "https://api.coinmarketcap.com/v1/ticker/?limit=32"
    r = requests.get(url)
    return r.json()
