import hashlib
import traceback
import math, time, requests, pickle, traceback, sys
from datetime import datetime, timedelta
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
        self.log.debug('processing alerts')
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
                        # self.log.info("ath for {} is {}".format(fsym, self.repository.get_ath(fsym, tsym)[0]))
                        targets = tsyms[tsym]
                        price = self.repository.get_price_if_valid(fsym, tsym)
                        for target in targets:
                            if op == lower and price < target or op == higher and price > target:
                                self.api.sendMessage(f"{fsym} is {'below' if op == lower else 'above'} {format_price(target)} at {format_price(price)} {tsym}", chatId)
                                toRemove.append((fsym, tsym, target, chatId, op))

        for tr in toRemove:
            self.removeAlert(tr[0], tr[1], tr[2], tr[3], tr[4])

    def processWatches(self):
        self.log.debug('processing watches')
        if 'watches' not in self.db:
            return  
        # self.log.debug(f'processing { len(self.db['watches']) } watches')
        i = 0
        while i < len (self.db['watches']):
            watch = self.db['watches'][i]
            # if watch is ath true then get the ath and athdate
            if watch['from_ath']:
                comparitorprice, comparitordate = self.repository.get_ath(watch['fsym'], watch['tsym']) 

                # convert comparitordate from epoch ms to datetime
                comparitordate = datetime.fromtimestamp(comparitordate/1000)
                comparitordate_str = comparitordate.strftime('%d-%b-%Y')
            else:
                # caluclate periodindays from duration and duration_type
                duration = watch['duration'] 
                if watch['duration_type'][:3] == "day":
                    durationindays = duration
                elif watch['duration_type'][:4] == "week":
                    durationindays = duration * 7
                elif watch['duration_type'][:5] == "month":
                    durationindays = duration * 30
                elif watch['duration_type'][:4] == "year":
                    durationindays = duration * 365

                # at this point we have durationindays and can work backwards from now to find the comparitor date
                comparitordate = datetime.now() - timedelta(days=durationindays)

                # date rounding to nearest day for comparitor date
                comparitordate = comparitordate.replace(hour=0, minute=0, second=0, microsecond=0)


                # get the price for that symbol pair on that date
                comparitorprice = self.repository.get_day_price(watch['fsym'], watch['tsym'], comparitordate)

                # create string version of comparitor date in dd-mmm-yyyy format
                comparitordate_str = comparitordate.strftime('%d-%b-%Y')

            # log info the comparitor price and date
            self.log.debug(f"comparitor price: {comparitorprice} on {comparitordate}")

            # get the current price
            currentprice = self.repository.get_price_if_valid(watch['fsym'], watch['tsym'])



           # convert percentage values to absolute
            # if target contains a percentage then convert to absolute
            if '%' in watch['target']:
                targetpercentage = float(watch['target'].replace('%', ''))
                target = comparitorprice * (targetpercentage / 100)
            else:
                target = int(watch['target'])


            # lets see if this watch is persistent
            persistent = False
            last_notify = 0
            notify_frequency = 24 * 60 * 60
            if 'persistent' in watch:
                if watch['persistent']:
                    persistent = True
                if 'last_notify' in watch:
                    last_notify = watch['last_notify']
                    # convert last_notify from int as epoch to datetime
                if 'notify_frequency' in watch:
                    notify_frequency = watch['notify_frequency']
            last_notify = datetime.fromtimestamp(last_notify/1000)
                 
                

           # do the comparison
            if watch['op'] == 'drop':
                if currentprice < comparitorprice - target:
                    if persistent: # have to check it hasn't been notified too recently                        
                        if datetime.now() - last_notify < timedelta(seconds=notify_frequency):
                            self.log.debug("persistent watch, not notifying")
                            i += 1
                            continue
                                        
                    self.api.sendMessage(f"Drop watch: {watch['fsym']} is {currentprice} {watch['tsym']} which is at least {watch['target']} lower than it was at {comparitordate_str} when it was {format_price(comparitorprice)} ", watch['chatId'])
                    if not persistent:
                        self.log.debug("removing completed drop watch")
                        del self.db['watches'][i]
                    # set the most recent notify key as now epoch as int
                    self.db['watches'][i]['last_notify'] = int(datetime.now().timestamp()) * 1000
                
                else:
                    i += 1
            elif watch['op'] == 'rise':
                    if currentprice >  comparitorprice + target:
                        if persistent:
                            if datetime.now() - last_notify < timedelta(seconds=notify_frequency):
                                self.log.debug("persistent watch, not notifying")
                                i += 1
                                continue

                        self.api.sendMessage(f"Rise watch: {watch['fsym']} is {currentprice} {watch['tsym']} which is at least {watch['target']} higher than it was at {comparitordate_str} when it was {format_price(comparitorprice)} ", watch['chatId'])
                        if not persistent:
                            self.log.debug("removing completed rise watch")
                            del self.db['watches'][i]
                        else:
                            # set the most recent notify key as now epoch as int
                            self.db['watches'][i]['last_notify'] = int(datetime.now().timestamp()) * 1000                        

                    else:
                        i += 1
            else: # this item is invalid, delete it
                self.log.error(f"invalid watch op: {watch['op']}")
                del self.db['watches'][i]



            
        return

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
        self.log.debug('persisting db')
        if hashlib.md5(repr(self.db).encode('utf-8')).hexdigest() == self.dbmd5:
            self.log.debug('no change')
        else:
            cache.log.debug('write to disk and update md5')
            with open(config.DB_FILENAME, 'wb') as fp:
                pickle.dump(self.db, fp)
            self.dbmd5 = hashlib.md5(repr(self.db).encode('utf-8')).hexdigest()


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
            self.dbmd5 = hashlib.md5(repr(self.db).encode('utf-8')).hexdigest()
        except:
            self.log.exception("error loading db, defaulting to empty db")
            self.db = {}
            self.dbmd5 = ""

        self.api = TgApi(self.log)
        self.repository = MarketRepository(self.log)
        self.command_handler = CommandHandler(self.api, self.repository, self.db, self.log)

        self.log.debug("db at start: {}".format(self.db))
        self.last_update = self.db['last_update'] if 'last_update' in self.db else 0
        # main loop
        loop = True
        while loop:
            # delay for 2 seconds
            time.sleep(4)


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
                try:
                    self.processWatches()
                except:
                    self.log.exception("exception at processing watches")
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
