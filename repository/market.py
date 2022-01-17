from time import time
from datetime import datetime
import math
import collections
from os import remove,listdir


from cache import cache
from api.binance_rest import RestApiBinance,CandleInterval
from draw_candles import DrawChart

class MarketRepository(object):  
    def __init__(self, log):
        self.log = log
        self.binance_api = RestApiBinance()

    def get_day_price(self, fsym, tsym, queryday):
        dayprice = self.binance_api.get_price_on_date(fsym+tsym, queryday)
        return dayprice

    @cache("market.symbols", 3600)
    def get_symbols(self):
        symbols = self.binance_api.get_symbols()
        return symbols        

    @cache("market.ath", 86400, [1]) # 1 day is 86400 seconds, cache vary by symbol
    def get_ath(self, symbol):
        tsym = "USDT"  
                
        return self.binance_api.get_ath(symbol+tsym)



    TSYMS = ['BTC','USDT','BNB', 'ETH', 'EUR']
    def isPricePairValid(self, fsym, tsym):
        return (fsym+tsym).upper() in self.get_symbols()

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
    

    def get_price(self, fsym, tsym):
        symbol = (fsym+tsym).upper()
        return self.binance_api.get_prices()[symbol]
    

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
        self.log.debug(f"generating chart for {fsym} {tsym} ")

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




        