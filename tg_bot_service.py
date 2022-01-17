import traceback
import math, time, requests, pickle, traceback, sys
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import logger_config
import config
from cache import cache
from repository.market import MarketRepository
from formating import format_price
from api.binance_rest import CandleInterval
from command_handler import CommandHandler
from tg_api import TgApi

class TgBotService(object):
    def processMessage(self, message):
        if "text" not in message:
            self.log.debug("IGNORING MSG [NO TEXT]")
            return
        if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
            self.command_handler.dispatch(message)
        else:
            self.log.debug("IGNORING MSG [NON-COMMAND]")


    def removeAlert(self, fsym, tsym, target, chatId, op):
        alerts = self.db['alerts']
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
        if 'alerts' not in self.db:
            return
        higher = 'HIGHER'
        lower = 'LOWER'
        alerts = self.db['alerts']
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
                                self.api.sendMessage(f"{fsym} is {'below' if op == lower else 'above'} {format_price(target)} at {format_price(price)} {tsym}", chatId)
                                toRemove.append((fsym, tsym, target, chatId, op))

        for tr in toRemove:
            self.removeAlert(tr[0], tr[1], tr[2], tr[3], tr[4])


    def processUpdates(self, updates):
        for update in updates:
            self.last_update = self.db['last_update'] = update['update_id']            
            self.log.debug(f"processing update: {update}")
            if 'message' in update:
                message = update['message']
            elif "edited_message" in update:
                message = update['edited_message']
            else:
                self.log.debug(f"no message in update: {update}")
                return

            try:
                self.processMessage(message)                
            except:
                self.log.exception(f"error processing update: {update}")


    def persist_db(self):
        with open(config.DB_FILENAME, 'wb') as fp:
            pickle.dump(self.db, fp)

    def run(self, debug=False):
        self.log = logger_config.instance
        if debug:
            self.log.setLevel(logger_config.logging.DEBUG)
        else:
            self.log.setLevel(logger_config.logging.INFO)

        cache.log = self.log
        try:
            with open(config.DB_FILENAME, 'rb') as fp:
                self.db = pickle.load(fp)
        except:
            self.log.exception("error loading db, defaulting to empty db")
            self.db = {}

        self.api = TgApi(self.log)
        self.repository = MarketRepository(self.log)
        self.command_handler = CommandHandler(self.api, self.repository, self.db, self.log)

        self.log.debug("db at start: {}".format(self.db))
        self.last_update = self.db['last_update'] if 'last_update' in self.db else 0
        # main loop
        loop = True
        while loop:
            # delay for 2 seconds - maximum deplay in processing commands
            # unlikely to hit server limit as everything is cached using the 
            # cache module and cache file is persisted to disk
            time.sleep(2)


            try:                
                updates = self.api.getUpdates(self.last_update)   
 
                if updates is None:
                    self.log.error('get update request failed')
                else:
                    self.processUpdates(updates)
                try:
                    self.processAlerts()
                except:
                    self.log.exception("exception at processing alerts")
                time.sleep(1)            
            except KeyboardInterrupt:
                self.log.info("interrupt received, stopping…")
                loop = False
            except requests.exceptions.ConnectionError as e:
                # A serious problem happened, like DNS failure, refused connection, etc.
                updates = None   
            except:            
                self.log.exception("exception at processing updates")
                loop = False

            self.persist_db()
            cache.persist()

if __name__ == "__main__":
    service = TgBotService()
    debug= False
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug=True
    service.run(debug)
