import urllib 
import requests
import collections
from enum import Enum, unique
from cache import cache
from candle import Candle

import logger_config


class RestApiBinance:    
    BASE_URL="https://api.binance.com/"
    PATH_CANDLESTICK_DATA = "api/v1/klines"
    PATH_EXCHANGEINFO = "api/v1/exchangeInfo"
    PATH_PRICE = "api/v3/ticker/price"

    def __init__(self):
        self.logger = logger_config.instance

    # function to get the ath price from binance of a coin
    @cache("binance.getath", 86400, [1,2])
    def get_ath(self, fsym, tsym):
        #set up the query params
        query_params = {}
        query_params["symbol"] = fsym+tsym  
        query_params["interval"] = "1M" # 1M = 1 month
        query_params["limit"] = 500 # is the max periods of time that can be requested
        query_params["startTime"] = 1633068154000 # 1 Oct 2021

        query=urllib.parse.urlencode(query_params)

        url = self.BASE_URL + self.PATH_CANDLESTICK_DATA
        self.logger.debug("requesting: "+ url + " - "+str(query))
        r = requests.request("GET", url,params= query)

        # loop through responses and find the highest value to return
        highest_value = 0.0
        highest_datetimemilliseconds = 0
        for c in r.json():
            print(float(c[2]) )
            if float(c[2]) > highest_value:
                highest_value = float(c[2])
                highest_datetimemilliseconds = int(c[0])

        return highest_value, highest_datetimemilliseconds







    # function to get the bitcoin price from binance on a date
    @cache("binance.getpriceondate", 86400, [1,2])    
    def get_price_on_date(self, symbol, dateofprice):
        """ Returns the high price of the 24 hour period starting with dateofprice """
        # convert dateofprice to linux epoch milliseconds
        dateofprice_epoch = int(dateofprice.timestamp() * 1000)

        #set up the query params
        query_params = {}
        query_params["symbol"] = symbol
        query_params["interval"] = "1d"
        query_params["limit"] = 1
        query_params["startTime"] = dateofprice_epoch
        query=urllib.parse.urlencode(query_params)

        url = self.BASE_URL + self.PATH_CANDLESTICK_DATA
        self.logger.debug("requesting: "+ url + " - "+str(query))
        r = requests.request("GET", url,params= query)

        # parse the json response

# Example
#  [
#   [
#     1499040000000,      // Open time
#     "0.01634790",       // Open
#     "0.80000000",       // High
#     "0.01575800",       // Low
#     "0.01577100",       // Close
#     "148976.11427815",  // Volume
#     1499644799999,      // Close time
#     "2434.19055334",    // Quote asset volume
#     308,                // Number of trades
#     "1756.87402397",    // Taker buy base asset volume
#     "28.46694368",      // Taker buy quote asset volume
#     "17928899.62484339" // Ignore.
#   ]
# ]


        # get the HIGH price from the second value of the first item in the json response
        # print('about to fail')
        return float(r.json()[0][2])


    @cache("binance.getcandles", 420, [1,2,3])
    def get_candles(self, symbol, interval, limit= 500):
        query_params = {}
        query_params["symbol"] = symbol
        query_params["interval"] = interval.value
        query_params["limit"] = limit
        query=urllib.parse.urlencode(query_params)

        url = self.BASE_URL + self.PATH_CANDLESTICK_DATA
        self.logger.debug("requesting: "+ url + " - "+str(query))
        r = requests.request("GET", url,params= query)
        return self.parse_candles(r.json())

    def parse_candles(self, json):
        candles={}
        for c in json:
            candles[c[0]] = Candle(float(c[1]), float(c[2]), float(c[3]), float(c[4]), c[0],c[6], float(c[5]))
        return candles
    
    @cache("binance.exchangeinfo", 86400)
    def get_exchangeinfo(self):
        url = self.BASE_URL + self.PATH_EXCHANGEINFO
        self.logger.debug("requesting: "+ url)
        r = requests.request("GET", url)
        return r.json()

    @cache("binance.pairs", 86400)
    def get_pairs(self):
        pairs=[]
        info = self.get_exchangeinfo()
        for s in info["symbols"]:
            pairs.append((s["baseAsset"],s["quoteAsset"]))
        return pairs

    @cache("binance.symbols", 86400)
    def get_symbols(self):
        info = self.get_exchangeinfo()
        symbols = []
        for s in info["symbols"]:
            symbols.append(s["symbol"])
        return symbols

    @cache("binance.prices", 420)
    def get_prices(self):
        url = self.BASE_URL + self.PATH_PRICE
        self.logger.debug("requesting: "+ url)
        r = requests.request("GET", url)
        js = r.json()
        prices = {}
        for price in js:
            prices[price["symbol"]] = float(price["price"])
        return prices


            
@unique
class CandleInterval(Enum):
    ONE_MINUTE = "1m"
    THREE_MINUTE = "3m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    THIRTY_MINUTE = "30m"
    ONE_HOUR = "1h"
    TWO_HOUR = "2h"
    FOUR_HOUR = "4h"
    SIX_HOUR = "6h"
    EIGHT_HOUR = "8h"
    TWELVE_HOUR = "12h"
    ONE_DAY = "1d"
    THREE_DAY = "3d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"

    def __str__(self):
        return self.value

    #to enable checking wether a value is a valid enum
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_ 