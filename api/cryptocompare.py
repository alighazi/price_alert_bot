import sys, math, time, requests, pickle
from datetime import datetime
import collections
import config

BASE_URL = "https://min-api.cryptocompare.com"
def get_symbols():
    syms = collections.OrderedDict()
    for page in range(0,10):        
        url = f"{BASE_URL}/data/top/totalvol?limit=100&tsym=USD&page={page}"
        print(f'loading symbols from network: {url}')
        r = requests.get(url)
        data = r.json()["Data"]
        for coin in data:
            syms[coin["CoinInfo"]["Internal"]] = coin["CoinInfo"]["FullName"]
    return syms

def get_price(fsyms, tsyms):
    url = f"{BASE_URL}/data/pricemulti?fsyms={','.join(fsyms)}&tsyms={','.join(tsyms)}"
    r = requests.get(url)
    return r.json()

#max count is 30
def get_top(tsym= "USD", count=40):
    url = f"{BASE_URL}/data/top/mktcapfull?limit={count}&tsym={tsym}"
    r = requests.get(url)
    data= r.json()["Data"]
    coins =[]
    rank=1
    for row in data:
        coin={}
        coin["rank"]= rank
        rank+=1
        coin["cap"]= row["RAW"][tsym]["MKTCAP"]
        coin["symbol"]=row["CoinInfo"]["Name"]
        coin["price"]=row["DISPLAY"][tsym]["PRICE"]
        
        coins.append(coin)

    return coins