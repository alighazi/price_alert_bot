from time import time
from datetime import datetime
import math
import collections
from os import remove

from cache import cache
from api.binance_rest import RestApiBinance,CandleInterval
from draw_candles import DrawChart
from api.cryptocompare import get_symbols, get_price
from api.coinmarketcap import get_top

class MarketRepository(object):  
    binance_api = RestApiBinance()

    @cache("market.symbols", 3600)
    def get_symbols(self):
        symbols = get_symbols()
        return symbols        

    TSYMS = ['BTC','USD','EUR','SEK','IRR','JPY','CNY','GBP','CAD','AUD','RUB','INR','USDT','ETH']
    def isPricePairValid(self, fsym, tsym):
        return fsym in self.get_symbols().keys() and tsym in self.TSYMS

    @cache("market.top", 20)
    def get_top_coins(self):          
        top_coins = get_top()
        out = "`"
        for coin in top_coins:
            cap_f = math.floor(float(coin['market_cap_usd']))
            cap_s =''
            if cap_f>1000*1000*1000:
                cap_s ='${:.3f}B\n'.format(cap_f/(1000*1000*1000))
            else:
                cap_s ='${:.3f}M\n'.format(cap_f/(1000*1000))
                
            out = out+coin['rank']+': ' + coin['symbol']+' '+coin['price_usd'] + \
                '$\t'+coin['price_btc']+'BTC\t' + cap_s
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

        print('index: {}, partition: {}, fsym: {}, tsym: {}'.format(index,partition, fsym,tsym))

        if (partition not in MarketRepository.last_price_queries) or (time() - MarketRepository.last_price_queries[partition]> MarketRepository.CACHE_DURATION_PRICE):
            index_start = max(0, partition * MarketRepository.PARTITION_SIZE - 2)
            index_end = index_start + MarketRepository.PARTITION_SIZE
            fsyms = list(symbols.keys())[index_start : index_end]
            self.price_partitions[partition] = get_price(fsyms, self.TSYMS)
            MarketRepository.last_price_queries[partition] = time()
        
        return self.price_partitions[partition][fsym][tsym]
    

    @cache("market.chart", 30, [1,2])
    def get_chart(self, fsym, tsym):
        TF = CandleInterval.FOUR_HOUR
        CANDLES = 120
        ROOT = "charts"
        
        print(f"generating chart for {fsym} {tsym} ")
        fsym = fsym.upper()
        tsym = tsym.upper()

        if tsym == "USD":
            tsym = "USDT"
        pair = fsym + tsym

        filename= f"{ROOT}/{pair}-{TF.value}-{CANDLES}-{time()}.png"
        pairs = self.binance_api.get_pairs()
        #TODO: remove the previous chart first!
        if (fsym, tsym) in pairs:
            c = self.binance_api.get_candles(pair, TF, CANDLES)
            dr = DrawChart()
            dr.save(filename, c)



        