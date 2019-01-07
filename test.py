import pickle, time, requests
import math
import json
from datetime import datetime
from api_binance import RestApiBinance, CandleInterval
from candle import Candle
from draw_candles import DrawChart

b = RestApiBinance()
pair = "BTCUSDT"
output_dir="output_images"
c = b.get_candles(pair, CandleInterval.ONE_HOUR, 60)


print(c)

dr = DrawChart()
dr.save(f"{output_dir}/{pair}.png", c)
