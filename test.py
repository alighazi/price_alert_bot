import pickle, time, requests, math, json
from datetime import datetime
from api.binance_rest import RestApiBinance, CandleInterval
from candle import Candle
from draw_candles import DrawChart
from cache import cache
from repository.market import MarketRepository
import tg_bot

b = RestApiBinance()
pair = "BTCUSDT"
output_dir="output_images"
candle_interval = CandleInterval.FOUR_HOUR
total_candles = 120

#c = b.get_candles(pair, candle_interval, total_candles)
#print(c)
#dr = DrawChart()
#dr.save(f"{output_dir}/{pair}-{candle_interval.value}-{total_candles}-{datetime.today():%Y-%m-%d-%H%M%S}.png", c)


# tb=tg_bot.TgBot()
# tb.init()


#print(b.get_pairs())

# @cache("sex",5,[0,1])
# def sex(lengthOfDick, sizeOfCup):
#     print("my name is ali and I am sexy")
#     print(f"{lengthOfDick}/{sizeOfCup}")

# sex("100m", "5F")

# mr = MarketRepository()
# mr.get_chart_near("trx", "btc")



#print(CandleInterval.has_value("4h"))


# cache.persist()