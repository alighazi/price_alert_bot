import sys, math, time, requests, pickle
from datetime import datetime
import collections
import config

def get_symbols():
    syms = collections.OrderedDict()
    for page in range(0,10):        
        url = f"https://min-api.cryptocompare.com/data/top/totalvol?limit=100&tsym=USD&page={page}"
        print(f'loading symbols from network: {url}')
        r = requests.get(url)
        data = r.json()["Data"]
        for coin in data:
            syms[coin["CoinInfo"]["Internal"]] = coin["CoinInfo"]["FullName"]
    return syms

def get_price(fsyms, tsyms):
    url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}".format(','.join(fsyms), ','.join(tsyms))
    r = requests.get(url)
    return r.json()
