import pickle, time, requests, math, json
from datetime import datetime
from api import cryptocompare
from repository.market import MarketRepository

# cc = cryptocompare.CryptoCompare()
# syms = cc.get_symbols()
# print(syms)

# mr = MarketRepository()
# p = mr.get_price("BTC", "USD")
# print(p)

def jick():
    print("jick jick")

def woof():
    print("woof")

commands = {
    "j":jick,
    "wuf":woof
}

commands["j"]()
commands["wuf"]()