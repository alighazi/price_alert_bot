import pickle, time, requests, math, json
from datetime import datetime
from api.binance_rest import RestApiBinance, CandleInterval
from candle import Candle
from draw_candles import DrawChart
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


tb=tg_bot.TgBot()
tb.init()
syms = tb.getTop()
print(syms)

price= tb.get_price("BTC", "USD")
print(price)
print(tb.get_price("NANO","USD"))