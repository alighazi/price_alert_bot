import pickle, time, requests
import math
import json
from datetime import datetime
from api_binance import RestApiBinance, CandleInterval
from candle import Candle
from draw_candles import DrawChart

b = RestApiBinance()
c = b.get_candles("MCOBTC", CandleInterval.THREE_DAY, 60)


print(c)

dr = DrawChart()
dr.save("MCOBTC.png", c)
