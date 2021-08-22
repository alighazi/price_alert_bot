import pickle, time, requests, math, json
from datetime import datetime
from api import binance_rest
from repository.market import MarketRepository

# cc = cryptocompare.CryptoCompare()
# syms = cc.get_symbols()
# print(syms)

# mr = MarketRepository()
# p = mr.get_price("BTC", "USD")
# print(p)


br = binance_rest.RestApiBinance()

pairs = br.get_prices()
print(pairs)