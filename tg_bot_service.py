import hashlib
import traceback
import math, time, requests, pickle, traceback, sys, os
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
            print(f'processing watch [{i}] of {len(self.db["watches"])}')
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

                durationindays = int(durationindays)

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
            elif watch['op'] == 'stable':
                # logic for stable is:
                
                # if it is persistent then check the last notify because if that fails then there is no point in calculating the stabilit
                if persistent:
                    if datetime.now() - last_notify < timedelta(seconds=notify_frequency):
                        self.log.debug("persistent watch, not notifying")
                        i += 1
                        continue

                # get current price
                todaysprice = self.repository.get_day_price(watch['fsym'], watch['tsym'], datetime.now())

                if '%' in watch['target']:
                    pricerangepercentage = float(watch['target'].replace('%', ''))
                    pricerange = comparitorprice * (pricerangepercentage / 100)
                else:
                    pricerange = int(watch['target'])

                # work out the bounds
                #   stable_price_lower_bound
                stable_price_lower_bound = todaysprice - pricerange


                #   stable_price_higher_bound
                stable_price_higher_bound = todaysprice + pricerange
                
                stable = True
                testday_datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                # Loop through the last n days
                for day in range(durationindays):
                    current_day = testday_datetime - timedelta(days=day)
                    
                    # For each day, get the price and see if it is more than the higher bound
                    testdayprice = self.repository.get_day_price(watch['fsym'], watch['tsym'], current_day)
                    if testdayprice > stable_price_higher_bound or testdayprice < stable_price_lower_bound:
                        # Out of range, not stable
                        stable = False
                        break

                if stable:                    
                    self.api.sendMessage(f"Stable watch: {watch['fsym']} at {todaysprice} is within +/- {watch['target']} range for {durationindays} days ", watch['chatId'])
                    if not persistent:
                        self.log.debug("removing completed Stable watch")
                        del self.db['watches'][i]
                    else:
                        # set the most recent notify key as now epoch as int
                        self.db['watches'][i]['last_notify'] = int(datetime.now().timestamp()) * 1000                        
                        i += 1
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
        new_filename = config.DB_FILENAME + ".temp"  # New temporary file name
        
        if hashlib.md5(repr(self.db).encode('utf-8')).hexdigest() == self.dbmd5:
            self.log.debug('no change')
        else:
            self.log.debug('writing data to a new file')

            # Write data to the new temporary file
            with open(new_filename, 'wb') as fp:
                pickle.dump(self.db, fp)
            
            # Perform file operations after confirming the data is saved to the new file
            if os.path.isfile(new_filename):
                self.log.debug('renaming files and creating backup')
                
                # Remove old backup file if it exists
                backup_filename = config.DB_FILENAME + ".backup"
                if os.path.isfile(backup_filename):
                    os.remove(backup_filename)
                
                try:
                    # Rename the current file to a backup file
                    os.rename(config.DB_FILENAME, backup_filename)
                    
                    # Rename the new temporary file to the current file
                    os.rename(new_filename, config.DB_FILENAME)
                    
                    self.log.debug('file persistence completed')
                except Exception as e:
                    self.log.error('error occurred during file operations: {}'.format(str(e)))
            else:
                self.log.debug('data not saved to the new file')

    def run(self, debug=False):
            self.log = logger_config.instance
            if debug:
                self.log.setLevel(logger_config.logging.DEBUG)
            else:
                self.log.setLevel(logger_config.logging.INFO)

            cache.log = self.log
            try:
                # Check if the current data file exists and is non-zero
                if os.path.isfile(config.DB_FILENAME) and os.path.getsize(config.DB_FILENAME) > 0:
                    with open(config.DB_FILENAME, 'rb') as fp:
                        self.db = pickle.load(fp)
                    self.dbmd5 = hashlib.md5(repr(self.db).encode('utf-8')).hexdigest()
                else:
                    self.log.debug("Current data file is missing or empty.")
                    # Check if a backup file exists
                    backup_filename = config.DB_FILENAME + ".backup"
                    if os.path.isfile(backup_filename) and os.path.getsize(backup_filename) > 0:
                        with open(backup_filename, 'rb') as fp:
                            self.db = pickle.load(fp)
                        self.dbmd5 = hashlib.md5(repr(self.db).encode('utf-8')).hexdigest()
                        self.log.debug("Loaded data from the backup file.")
                    else:
                        self.log.debug("Both current and backup files are missing or empty. Creating an empty database.")
                        self.db = {}
                        self.dbmd5 = ""
            except Exception as e:
                self.log.exception("Error loading data: {}".format(str(e)))
                self.db = {}
                self.dbmd5 = ""

            self.api = TgApi(self.log)
            self.repository = MarketRepository(self.log)
            self.command_handler = CommandHandler(self.api, self.repository, self.db, self.log)

            self.log.debug("db at start: {}".format(self.db))
            self.last_update = self.db['last_update'] if 'last_update' in self.db else 0
            # main loop
            loop = True
            sequence_id = 0
            while loop:
                sequence_id += 1
                time.sleep(1)
                try:                
                    updates = self.api.getUpdates(self.last_update)   
    
                    if updates is None:
                        self.log.error('get update request failed')
                    else:
                        if len(updates) > 0:
                            self.processUpdates(updates)
                            # if we have just done an update then we should process alerts and watches
                            self.processAlerts
                            self.processWatches

                    # processing Alerts is quite cheap, do it every 3 seconds, if the current_seconds mod 2 = 0 then
                    if sequence_id % 3 == 0:
                        try:
                            self.processAlerts()
                        except:
                            self.log.exception("exception at processing alerts")

                    # processing watches is quite expensive, do it every 29 seconds, if the current_seconds mod 10 = 0
                    if sequence_id % 29 == 0:
                        try:
                            self.processWatches()
                        except:
                            self.log.exception("exception at processing watches")

                    

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
