from time import time
from datetime import datetime
import math
import collections
from os import remove,listdir


from cache import cache
from api.binance_rest import RestApiBinance,CandleInterval
from draw_candles import DrawChart
from api.cryptocompare import CryptoCompare

class MarketRepository(object):  
    def __init__(self, log):
        self.log = log
        self.binance_api = RestApiBinance()
        self.crypto_compare = CryptoCompare()

    @cache("market.symbols", 3600)
    def get_symbols(self):
        symbols = self.crypto_compare.get_symbols()
        return symbols        

    TSYMS = ['BTC','USD','EUR','SEK','IRR','JPY','CNY','GBP','CAD','AUD','RUB','INR','USDT','ETH']
    def isPricePairValid(self, fsym, tsym):
        return fsym in self.get_symbols().keys() and tsym in self.TSYMS

    @cache("market.top", 30)
    def get_top_coins(self):   
        tsym = "USD"       #must be in CAPS
        top_coins = self.crypto_compare.get_top(tsym)
        out = "`"
        for coin in top_coins:
            cap_f = math.floor(float(coin["cap"]))
            cap_s =''
            if cap_f>1000*1000*1000:
                cap_s ='${:.2f}B'.format(cap_f/(1000*1000*1000))
            else:
                cap_s ='${:.3f}M'.format(cap_f/(1000*1000))

            out = f"{out}{coin['rank']}: {coin['symbol']} {coin['price']} \t {cap_s}\n"
        out = out+'`'
        return out
    
    PARTITION_SIZE = 45
    CACHE_DURATION_PRICE = 10.0
    last_price_queries = {}
    price_partitions = {}
    def get_price(self, fsym, tsym):
        symbols = self.get_symbols()
        index=list(symbols.keys()).index(fsym)
        partition= index//MarketRepository.PARTITION_SIZE 

        #print('index: {}, partition: {}, fsym: {}, tsym: {}'.format(index,partition, fsym,tsym))

        if (partition not in MarketRepository.last_price_queries) or (time() - MarketRepository.last_price_queries[partition]> MarketRepository.CACHE_DURATION_PRICE):
            index_start = max(0, partition * MarketRepository.PARTITION_SIZE - 2)
            index_end = index_start + MarketRepository.PARTITION_SIZE
            fsyms = list(symbols.keys())[index_start : index_end]
            self.price_partitions[partition] = self.crypto_compare.get_price(fsyms, self.TSYMS)
            MarketRepository.last_price_queries[partition] = time()
        
        return self.price_partitions[partition][fsym][tsym]
    

    def get_price_if_valid(self, fsym, tsym):
        if not self.isPricePairValid(fsym, tsym):
            self.log.debug(f"price pair not valid {fsym} {tsym}")
        else:
            return self.get_price(fsym, tsym)

    @cache("market.chart", 30, [1,2,3])
    def get_chart(self, fsym, tsym, tf):
        CANDLES = 170
        ROOT = "charts"

        fsym = fsym.upper()
        tsym = tsym.upper()        
        print(f"generating chart for {fsym} {tsym} ")

        if tsym == "USD":
            tsym = "USDT"
        pair = fsym + tsym

        filenameBase= f"{pair}-{tf.value}-{CANDLES}"
        toRemove = [f for f in listdir(ROOT) if f.startswith(filenameBase)]
        for f in toRemove:
            remove(f"{ROOT}/{f}")
        filename= f"{ROOT}/{filenameBase}-{time()}.png"
        pairs = self.binance_api.get_pairs()
        if (fsym, tsym) in pairs:
            c = self.binance_api.get_candles(pair, tf, CANDLES)
            dr = DrawChart()
            dr.save(filename, c, f"{pair}-{tf.value}-Binance\n@crypto_price_notification_bot ")
            return filename
        return None
    
    def get_chart_far(self, fsym, tsym):
        return self.get_chart(fsym, tsym, CandleInterval.FOUR_HOUR)
    def get_chart_near(self, fsym, tsym):
        return self.get_chart(fsym, tsym, CandleInterval.FIFTEEN_MINUTE)        




        