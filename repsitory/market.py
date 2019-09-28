from time import time
import math
import collections

from api.cryptocompare import get_symbols, get_price
from api.coinmarketcap import get_top

class MarketRepsitory(object):  

    CACHE_DURATION_SYMBOL = 3600.0#1 hour
    last_symbol_update = 0.0
    symbols = collections.OrderedDict
    def get_symbols(self):
        t = time()
        t -= self.last_symbol_update
        if t < self.CACHE_DURATION_SYMBOL:
            return self.symbols

        self.symbols = get_symbols()
        self.last_symbol_update = time()
        return self.symbols     

    TSYMS = ['BTC','USD','EUR','SEK','IRR','JPY','CNY','GBP','CAD','AUD','RUB','INR','USDT','ETH']
    def isPricePairValid(self, fsym, tsym):
        return fsym in self.get_symbols().keys() and tsym in self.TSYMS

    CACHE_DURATION_TOP = 30.0
    last_top_update = 0.0
    top = str()
    def get_top_coins(self):          
        if (time() - self.last_top_update > self.CACHE_DURATION_TOP):
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
            self.top = out
            self.last_top_update = time()
        else:
            print('reading top() from the cache')

        return self.top
    
    PARTITION_SIZE = 45
    CACHE_DURATION_PRICE = 10.0
    last_price_queries = {}
    price_partitions = {}
    def get_price(self, fsym, tsym):
        symbols = self.get_symbols()
        index=list(symbols.keys()).index(fsym)
        partition= index//self.PARTITION_SIZE 

        print('index: {}, partition: {}, fsym: {}, tsym: {}'.format(index,partition, fsym,tsym))

        if (partition not in self.last_price_queries) or (time() - self.last_price_queries[partition]> self.CACHE_DURATION_PRICE):
            index_start = max(0, partition * self.PARTITION_SIZE - 2)
            index_end = index_start + self.PARTITION_SIZE
            fsyms = list(symbols.keys())[index_start : index_end]
            self.price_partitions[partition] = get_price(fsyms, self.TSYMS)
            self.last_price_queries[partition] = time()
        
        return self.price_partitions[partition][fsym][tsym]


        