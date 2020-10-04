import sys, math, time, requests, pickle
from datetime import datetime
import collections
import config
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

BASE_URL = "https://min-api.cryptocompare.com"

class CryptoCompare():
    def __init__(self):
        self.session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])

        self.session.mount(BASE_URL, HTTPAdapter(max_retries=retries))

    def get_symbols(self):
        syms = collections.OrderedDict()
        for page in range(0,10):        
            url = f"{BASE_URL}/data/top/totalvol?limit=100&tsym=USD&page={page}"
            print(f'loading symbols from network: {url}')
            time.sleep(0.3)
            r = self.session.get(url, headers={"authorization": "Apikey "+config.CC_API_KEY})
            data = r.json()["Data"]
            for coin in data:
                syms[coin["CoinInfo"]["Internal"]] = coin["CoinInfo"]["FullName"]
        return syms

    def get_price(self, fsyms, tsyms):
        url = f"{BASE_URL}/data/pricemulti?fsyms={','.join(fsyms)}&tsyms={','.join(tsyms)}"
        r = self.session.get(url)
        return r.json()

    #max count is 30
    def get_top(self, tsym= "USD", count=40):
        url = f"{BASE_URL}/data/top/mktcapfull?limit={count}&tsym={tsym}"
        r = self.session.get(url)
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