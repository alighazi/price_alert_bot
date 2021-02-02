import math, time, requests, pickle, traceback
from datetime import datetime
from cache import cache
from repository.market import MarketRepository
from formating import format_price
from api.binance_rest import CandleInterval

import config
from tg_api import TgApi
from command_handler import CommandHandler


class TgBot(object):
    db = {}  # this makes db static!

    def __init__(self):
        self.repository = MarketRepository()
        self.api = TgApi()
        self.command_handler = CommandHandler(self.api, self.repository, TgBot.db)

    def processMessage(self, message):
        if "text" not in message:
            print(F"message doesn't have text! \n {message}")
            return
        if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
            self.command_handler.dispatch(message)

    def removeAlert(self, fsym, tsym, target, chatId, op):
        alerts = TgBot.db['alerts']
        alerts[chatId][fsym][op][tsym].remove(target)
        if len(alerts[chatId][fsym][op][tsym]) == 0:
            alerts[chatId][fsym][op].pop(tsym)
            if len(alerts[chatId][fsym][op]) == 0:
                alerts[chatId][fsym].pop(op)
                if len(alerts[chatId][fsym]) == 0:
                    alerts[chatId].pop(fsym)
                    if len(alerts[chatId]) == 0:
                        alerts.pop(chatId)

    def processAlerts(self):
        if 'alerts' not in TgBot.db:
            return
        higher = 'HIGHER'
        lower = 'LOWER'
        alerts = TgBot.db['alerts']
        toRemove = []
        for chatId in alerts:
            for fsym in alerts[chatId]:
                ops = alerts[chatId][fsym]
                for op in ops:
                    tsyms = ops[op]
                    for tsym in tsyms:
                        targets = tsyms[tsym]
                        price = self.repository.get_price_if_valid(fsym, tsym)
                        for target in targets:
                            if op == lower and price < target or op == higher and price > target:
                                self.api.sendMessage('{} is {} {} at {} {}'.format(self.repository.get_symbols()[fsym],
                                'below' if op == lower else 'above', format_price(target), format_price(price), tsym), chatId)
                                toRemove.append((fsym, tsym, target, chatId, op))

        for tr in toRemove:
            self.removeAlert(tr[0], tr[1], tr[2], tr[3], tr[4])
    


    def processUpdates(self, updates):
        for update in updates:
            print('processing {}...'.format(update['update_id']))
            message = update['message'] if 'message' in update else update['edited_message']
            try:
                self.processMessage(message)
                self.last_update = TgBot.db['last_update'] = update['update_id']
            except:
                traceback.print_exc()

    def init(self):
        try:
            with open(config.DB_FILENAME, 'rb') as fp:
                TgBot.db = pickle.load(fp)
        except:
            self.log("error loading db")
            TgBot.db = {}
        #self.log("db at start: {}".format(TgBot.db))
        self.last_update = TgBot.db['last_update'] if 'last_update' in TgBot.db else 0

    def persist_db(self):
        with open(config.DB_FILENAME, 'wb') as fp:
            #self.log(f"db at save: {TgBot.db}")
            pickle.dump(TgBot.db, fp)

    def log(self, str):
        print('{} - {}'.format(datetime.today(), str))
