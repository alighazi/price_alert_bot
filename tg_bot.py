import sys, math, time, requests, pickle, traceback
from datetime import datetime
import collections
from cache import cache
from repository.market import MarketRepository
import config
from formating import format_price
from api.binance_rest import CandleInterval

class TgBot(object):
    DB_FILENAME = 'data/db.pickle'
    HELP_FILENAME = 'help.md'
    CACHE_DURATION = 10  # seconds
    DEFAULT_FIAT = "USD"
    DEFAULT_COIN = "BTC"

    db = {} #this makes db static!

    def __init__(self):
        self.repository = MarketRepository()

    def log(self, str):
        print('{} - {}'.format(datetime.today(), str))
    
#    @cache("TgBot.Help", 100000)
    def help(self):
        self.log("reading help file")
        with open(TgBot.HELP_FILENAME, 'rb') as fp:
            return fp.read()

    def getTgUrl(self, methodName):
        return 'https://api.telegram.org/bot{}/{}'.format(config.TG_TOKEN, methodName)

    def get_price(self, fsym, tsym):
        if not self.repository.isPricePairValid(fsym, tsym):
            print(f"price pair not valid {fsym} {tsym}")
        else:
            return self.repository.get_price(fsym, tsym)

    def getTop(self):
        return self.repository.get_top_coins()

    def get_symbols(self):
        return self.repository.get_symbols()

    def sendMessage(self, msg, chatid, parse_mode=None):
        url = self.getTgUrl('sendMessage')
        r = requests.post(url=url, data={
            'chat_id': chatid,
            'text': msg,
            'parse_mode': parse_mode
        })
        return r

    def sendPhoto(self, fileName, caption, chatid, parse_mode=None):
        files = {'photo': open(fileName, 'rb')}
        url = self.getTgUrl('sendPhoto')
        r = requests.post(url=url, data={
            'chat_id': chatid,
            'caption': caption,
            'parse_mode': parse_mode,
        }, files= files)
        return r

    def handleBotCommand(self, message):
        text = message['text']
        chatId = message['chat']['id']
        command = text.partition('/')[2]
        self.log('handling command "{}"...'.format(command))

        if command == 'start' or command == 'help':
            resp = self.help()
            self.sendMessage(resp, chatId, "Markdown")

        elif command == 'all' or command == 'top':
            resp = self.getTop()
            self.sendMessage(resp, chatId, 'Markdown')

        elif command == 'alerts':
            if 'alerts' in TgBot.db and chatId in TgBot.db['alerts']:
                alerts=TgBot.db['alerts'][chatId]
                msg='Current alerts:\n'
                for fsym in alerts:
                    for op in alerts[fsym]:
                        for tsym in alerts[fsym][op]:
                            for target in alerts[fsym][op][tsym]:
                                msg='{}{} {} {} {}\n'.format(msg, self.get_symbols()[fsym], op, target,tsym)
                self.sendMessage(msg, chatId)
            else:
                self.sendMessage('No alert is set',chatId)

        elif command=='clear':
            if 'alerts' in TgBot.db and chatId in TgBot.db['alerts']:
                TgBot.db['alerts'].pop(chatId)
            self.sendMessage('Done.',chatId)
        
        elif command.startswith('price') or command.startswith('p'):
            parts = command.split()
            if len(parts) > 3:
                self.sendMessage("Invalid command, enter 2 symbols, eg: BTC USD", chatId)
                return

            fsym = TgBot.DEFAULT_COIN
            if len(parts) >1:
                fsym = parts[1].upper()

            tsym = self.DEFAULT_FIAT
            if len(parts) > 2:
                tsym = parts[2].upper()

            if not self.repository.isPricePairValid(fsym, tsym):
                self.sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
                return

            price = self.get_price(fsym, tsym)
            resp = '1 {} = {} {}'.format(self.get_symbols()[fsym], format_price(price),tsym)
            chartFile = self.repository.get_chart_near(fsym, tsym)
            if chartFile != None:
                self.sendPhoto(chartFile, resp, chatId)
            else:
                self.sendMessage(resp, chatId)
        elif command.startswith('chart') or command.startswith('ch'):
            parts = command.split()
            if len(parts) > 3:
                self.sendMessage("Invalid command, enter 2 symbols, eg: BTC USD", chatId)
                return

            fsym = TgBot.DEFAULT_COIN
            if len(parts) > 1:
                fsym = parts[1].upper()

            tsym = self.DEFAULT_FIAT
            tf = CandleInterval.ONE_HOUR
            if len(parts) > 2:
                tsym = parts[2].upper()                
                if len(parts) > 3 and CandleInterval.has_value(parts[3]):
                    tf = CandleInterval(parts[3])


            chartFile = self.repository.get_chart(fsym, tsym, tf)
            if chartFile != None:
                price = self.get_price(fsym, tsym)
                if self.repository.isPricePairValid(fsym, tsym):
                    resp = '1 {} = {} {}'.format(self.get_symbols()[fsym], format_price(price),tsym)
                else:
                    resp = "Enjoy the binance chart!"
                self.sendPhoto(chartFile, resp, chatId)
            else:
                self.sendMessage(f"no chart for {fsym} {tsym} {tf}", chatId)

        elif command.startswith('lower') or command.startswith('higher'):
            parts = command.upper().split()
            if len(parts) < 3 or len(parts) > 4:
                self.sendMessage("Invalid command", chatId)
                return
            op = parts[0]
            fsym = parts[1]
            if not fsym in self.get_symbols().keys():
                self.sendMessage('Invalid symbol "{}"'.format(fsym), chatId)
                return
            try:
                target = float(parts[2])
            except ValueError:
                self.sendMessage('Invalid number "{}"'.format(parts[2]), chatId)
                return
            tsym = parts[3] if len(parts) > 3 else self.DEFAULT_FIAT
            if tsym == "SAT" or tsym== "SATS":
                target=target/(100.0*1000.0*1000.0)
                tsym="BTC"

            if tsym not in self.repository.TSYMS:
                self.sendMessage('Invalid symbol {}'.format(tsym), chatId)
                return

            if 'alerts' not in TgBot.db:
                TgBot.db['alerts'] = {}
            alerts = TgBot.db['alerts'][chatId] if chatId in TgBot.db['alerts'] else {}
            if fsym in alerts:
                alert = alerts[fsym]
                if op in alert and type(alert[op]) is dict:
                    opObj = alert[op]
                    if tsym in opObj:
                        opObj[tsym].add(target)
                    else:
                        opObj[tsym] = set([target])
                else:
                    alert[op] = {tsym: set([target])}
            else:
                alerts[fsym] = {op: {tsym: set([target])}}
            TgBot.db['alerts'][chatId] = alerts
            msg = 'Notification set for {} {} {} {}.'.format(
                self.get_symbols()[fsym], 'below' if op == 'LOWER' else 'above', format_price(target), tsym)
            self.sendMessage(msg, chatId)
        else:
            self.sendMessage('Unknown command', chatId)

    def processMessage(self, message):
        text = message['text']
        chatId = message['chat']['id']
        if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
            self.handleBotCommand(message)
        # no need to handle non commands
        # else: 
        #     self.sendMessage(f'Invalid command {text}', chatId)

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
                        price = self.get_price(fsym, tsym)
                        for target in targets:
                            if op == lower and price < target or op == higher and price > target:
                                self.sendMessage('{} is {} {} at {} {}'.format(self.get_symbols()[fsym],
                                'below' if op == lower else 'above', format_price(target), format_price(price), tsym), chatId)
                                toRemove.append((fsym, tsym, target, chatId, op))

        for tr in toRemove:
            self.removeAlert(tr[0], tr[1], tr[2], tr[3], tr[4])
    
    def getUpdates(self):
        offset = self.last_update+1
        url = self.getTgUrl('getUpdates')
        r = requests.post(
            url=url, data={'offset': offset, 'limit': 100, 'timeout': 9})
        updates = r.json()
        if not 'ok' in updates or not updates['ok']:
            return None
        return updates['result']

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
            with open(TgBot.DB_FILENAME, 'rb') as fp:
                TgBot.db = pickle.load(fp)
        except:
            self.log("error loading db")
            TgBot.db = {}
        #self.log("db at start: {}".format(TgBot.db))
        self.last_update = TgBot.db['last_update'] if 'last_update' in TgBot.db else 0

    def persist_db(self):
        with open(TgBot.DB_FILENAME, 'wb') as fp:
            #self.log(f"db at save: {TgBot.db}")
            pickle.dump(TgBot.db, fp)