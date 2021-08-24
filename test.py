import pickle, time, requests, math, json, logging
from datetime import datetime
from api import binance_rest
from repository.market import MarketRepository
import logger_config

# cc = cryptocompare.CryptoCompare()
# syms = cc.get_symbols()
# print(syms)

# mr = MarketRepository()
# p = mr.get_price("BTC", "USD")
# print(p)


# br = binance_rest.RestApiBinance()

# pairs = br.get_prices()
# print(pairs)

logger = logger_config.instance
logger.setLevel(logging.INFO)

logger.debug("1. this is a debug message")
logger.info("2. this is a info message")
logger.error("3. this is a error message")
logger.warning("3. this is a warning message")