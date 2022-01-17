import math, time, requests, pickle, traceback
from datetime import datetime, timedelta


from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from cache import cache
from repository.market import MarketRepository
import config
from formating import format_price
from api.binance_rest import CandleInterval



class CommandHandler:

    def __init__(self, api, repository, db, log):
        self.repository = repository
        self.db = db
        self.api = api
        self.log = log

    def dispatch(self, message):
            text = message['text']
            chatId = message['chat']['id']
            command = text.partition('/')[2]
            self.log.info(f'handling command "{command}"')

            if command == 'start' or command == 'help':
                self.help(chatId, command)
            elif command == 'all' or command == 'top':
                self.getTop(chatId, command)
            elif command == 'alerts':
                self.alerts(chatId, command)
            elif command=='clear':
                self.clear(chatId, command)            
            elif command.startswith('price') or command.startswith('p'):
                self.price(chatId, command)
            elif command.startswith('chart') or command.startswith('ch'):
                self.chart(chatId, command)
            elif command.startswith('lower') or command.startswith('higher'):
                self.higher_lower(chatId, command)
            elif command.startswith('yesterday'):
                self.yesterday(chatId, command)
            elif command.startswith('history'):
                self.history(chatId, command)
            elif command.startswith('dropby'):
                self.dropby(chatId, command)
            elif command.startswith('ath'):
                self.ath(chatId, command)
            elif command.startswith('watch'):
                self.watch(chatId, command)
            else:
                self.api.sendMessage('Unknown command', chatId)

    def clear(self, chatId, command):
        if 'alerts' in self.db and chatId in self.db['alerts']:
            self.db['alerts'].pop(chatId)
        self.api.sendMessage('Done.',chatId)

    def watch(self, chatId, command):
        # command structured
        # /watch btc drop 50% 14 days
        # /watch btc spike 50% 1 month
        # /watch btc drop 5000 2 days
        # /watch btc drop 5000 2 days from ath

        parts = command.split()
        if not (len(parts) in [6,8]):
            self.api.sendMessage("Invalid command, see help", chatId)
            return

        fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT

        op = parts[2].lower()
        if op not in ['drop','spike']:
            self.api.sendMessage("Invalid command, must be drop or spike", chatId)
            return

        target = parts[3]

        # remove % if there is one in target
        if target.endswith('%'):
            target = target[:-1]
        
        # check if target is a number
        try:
            target = float(target)
        except:
            self.api.sendMessage("Invalid command, must be a number", chatId)
            return
        
        # this line never executes if there was something wrong with the target
        target = parts[3]

        # if there is a 4th part, it is the time period
        if len(parts) > 4:
            duration = parts[4]
        
        # if duration is not a number then something is wrong, return error
        try:
            duration = int(duration)
        except:
            self.api.sendMessage("Invalid command, must be a number", chatId)
            return

        # if there is a 5th part, it is the duration type
        if len(parts) > 5:
            duration_type = parts[5]
        else:
            duration_type = 'days'

        # if there is a sixth part it must be "from ath", else error
        if len(parts) > 6:
            if parts[6] != 'from':
                self.api.sendMessage("Invalid command, must be from ath", chatId)
                return
            else:
                from_ath = True
        else:
            from_ath = False
            
        # create an watch dictionar
        watch = {}
        watch['chatId'] = chatId
        watch['fsym'] = fsym
        watch['tsym'] = tsym
        watch['op'] = op
        watch['target'] = target
        watch['duration'] = duration
        watch['duration_type'] = duration_type
        watch['from_ath'] = from_ath

        if 'watchs' not in self.db:
            self.db['watchs'] = []
        self.db['watchs'].append( watch) 
        self.api.sendMessage("Watch added", chatId)
        return



        if not self.repository.isPricePairValid(fsym, tsym):
            self.api.sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
            return

        resp = 'Watching {} {} {}'.format(fsym, op, parts[3])
        self.api.sendMessage(resp, chatId)

    def ath(self, chatId, command):
        parts = command.split()
        if len(parts) > 3:
            self.api.sendMessage("Invalid command, enter 2 symbols, eg: BTC USDT", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) >1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT
        if len(parts) > 2:
            tsym = parts[2].upper()


        if not self.repository.isPricePairValid(fsym, tsym):
            self.api.sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
            return

        ath, athdate = self.repository.get_ath(fsym, tsym)
        
        resp = 'ATH for {} was {} {} on {}'.format(fsym, format_price(ath),tsym,datetime.fromtimestamp( athdate /1000 ).strftime("%Y/%m/%d")  )
        
        self.api.sendMessage(resp, chatId)

             

    def price(self, chatId, command):
        parts = command.split()
        if len(parts) > 3:
            self.api.sendMessage("Invalid command, enter 2 symbols, eg: BTC USDT", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) >1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT
        if len(parts) > 2:
            tsym = parts[2].upper()

        if not self.repository.isPricePairValid(fsym, tsym):
            self.api.sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
            return

        price = self.repository.get_price_if_valid(fsym, tsym)
        ath, athdate = self.repository.get_ath(fsym,tsym)
        resp = '1 {} = {} {} compared to ATH of {}'.format(fsym, format_price(price),tsym, format_price(ath))
        chartFile = self.repository.get_chart_near(fsym, tsym)
        if chartFile != None:
            self.api.sendPhoto(chartFile, resp, chatId)
        else:
            self.api.sendMessage(resp, chatId)

    def yesterday(self, chatId, command):
        parts = command.split()
        if len(parts) > 4:
            self.api.sendMessage("Invalid command, enter 2 symbols, eg: BTC USD", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) > 1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT

        # set ydate variable to yesterdays date  
        ydate = datetime.now() - timedelta(days=1)

        # get the price for that date                
        returnedprice = self.repository.get_day_price(fsym, tsym, ydate)

        print(returnedprice)
        print(type(returnedprice))
        print('.')
        resp = ' price yesterday was {}'.format(format_price(returnedprice))

        self.api.sendMessage(resp, chatId)


    def dropby(self, chatId, command):
        parts = command.split()
        if len(parts) != 5:
            self.api.sendMessage("Invalid comman: /dropby BTC 50% <n> [days|weeks|months|years]", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) > 1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT

        # dropbythreshold from parts[2]
        dropbythreshold = parts[2]

        # if dropbythreshold has a % sign then remove it
        if dropbythreshold.endswith('%'):
            dropbythreshold = dropbythreshold[:-1]

        # if dropbythreshold is not a number then return
        if not dropbythreshold.isdigit():
            self.api.sendMessage("Invalid dropby threshold", chatId)
            return

        # get the current price
        price = self.repository.get_price_if_valid(fsym, tsym)

        # get the historical price
        
        # default duration is 1 day
        duration = 1

        if len(parts) > 3:
            # convert parts[2].upper() from string to integer
            try:
                duration = int(parts[3])
            except ValueError:
                self.api.sendMessage("Invalid command", chatId)
                return


        if len(parts) > 4:
            # get the duration unit from parts[3]
            duration_unit = parts[4].lower()

            # if the duration is weeks or months then muliplay the duration by 7 or 30 respectively
            # if first 3 letters of duration_unit are 'day' then duration is in days
            # if first 3 letters of duration_unit are 'wee' then duration is in weeks
            # if first 3 letters of duration_unit are 'mon' then duration is in months
            if duration_unit[:3] == 'day':
                duration = duration
            elif duration_unit[:4] == 'week':
                duration = duration * 7     
            elif duration_unit[:5] == 'month':
                duration = duration * 30
            elif duration_unit[:4] == 'year':
                duration = duration * 365
            else:
                self.api.sendMessage("Invalid command ", chatId)
                return

        # if the duration is less then one then sendmessage error
        if duration < 1:
            self.api.sendMessage("Invalid duration", chatId)
            return
    
        tsym = config.DEFAULT_FIAT



        # set hdate variable to historical date  
        hdate = datetime.now() - timedelta(days=duration)

        # get the price for that date                
        historicalprice = self.repository.get_day_price(fsym, tsym, hdate)

        pricedifference = historicalprice - price

        # difference as a percentage
        pricedifferencepercentage = (pricedifference / historicalprice) * 100

        # if the difference is less than the dropbythreshold then sendmessage
        if pricedifferencepercentage < float(dropbythreshold):
            resp = 'LESS drop: price dropped by {:.1f} percent, changed {} to {}'.format(pricedifferencepercentage, format_price(historicalprice), format_price(price))
        else:
            resp = 'MORE drop: price dropped by {:.1f} percent, changed {} to {}'.format(pricedifferencepercentage, format_price(historicalprice), format_price(price))
    
        self.api.sendMessage(resp, chatId)

    def history(self, chatId, command):
        parts = command.split()
        if len(parts) > 4:
            self.api.sendMessage("Invalid command, enter /history BTC 5 days", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) > 1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT
        
        # default duration is 1 day
        duration = 1

        if len(parts) > 2:
            # convert parts[2].upper() from string to integer
            try:
                duration = int(parts[2])
            except ValueError:
                self.api.sendMessage("Invalid command, enter /history BTC 5 days", chatId)
                return


        if len(parts) > 3:
            # get the duration unit from parts[3]
            duration_unit = parts[3].lower()

            # if the duration is weeks or months then muliplay the duration by 7 or 30 respectively
            # if first 3 letters of duration_unit are 'day' then duration is in days
            # if first 3 letters of duration_unit are 'wee' then duration is in weeks
            # if first 3 letters of duration_unit are 'mon' then duration is in months
            if duration_unit[:3] == 'day':
                duration = duration
            elif duration_unit[:4] == 'week':
                duration = duration * 7     
            elif duration_unit[:5] == 'month':
                duration = duration * 30
            elif duration_unit[:4] == 'year':
                duration = duration * 365
            else:
                self.api.sendMessage("Invalid command, enter /history BTC <n> [days|weeks|months|years]", chatId)
                return

        # if the duration is less then one then sendmessage error
        if duration < 1:
            self.api.sendMessage("Invalid duration", chatId)
            return
    
        tsym = config.DEFAULT_FIAT



        # set hdate variable to historical date  
        hdate = datetime.now() - timedelta(days=duration)

        # get the price for that date                
        returnedprice = self.repository.get_day_price(fsym, tsym, hdate)

        print(returnedprice)
        print(type(returnedprice))
        print('.')

        # set printablehdate to hdate formatted as long date
        printablehdate = hdate.strftime('%B %d, %Y')

        resp = ' price {} days ago on {} was {}'.format(duration, printablehdate ,format_price(returnedprice))

        self.api.sendMessage(resp, chatId)


    def chart(self, chatId, command):
        parts = command.split()
        if len(parts) > 4:
            self.api.sendMessage("Invalid command, enter 2 symbols, eg: BTC USD", chatId)
            return

        fsym = config.DEFAULT_COIN
        if len(parts) > 1:
            fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT
        tf = CandleInterval.ONE_HOUR
        if len(parts) > 2:
            tsym = parts[2].upper()                
            if len(parts) > 3 and CandleInterval.has_value(parts[3]):
                tf = CandleInterval(parts[3])


        chartFile = self.repository.get_chart(fsym, tsym, tf)
        if chartFile != None:
            price = self.repository.get_price_if_valid(fsym, tsym)
            if self.repository.isPricePairValid(fsym, tsym):
                resp = f'{fsym} = {format_price(price)} {tsym}'
            else:
                resp = "Enjoy the binance chart!"
            self.api.sendPhoto(chartFile, resp, chatId)
        else:
            self.api.sendMessage(f"no chart for {fsym} {tsym} {tf}", chatId)

    def higher_lower(self, chatId, command):
        parts = command.upper().split()
        if len(parts) < 3 or len(parts) > 4:
            self.api.sendMessage("Invalid command", chatId)
            return
        op = parts[0]
        fsym = parts[1]
        try:
            target = float(parts[2])
        except ValueError:
            self.api.sendMessage('Invalid number "{}"'.format(parts[2]), chatId)
            return
        tsym = parts[3] if len(parts) > 3 else config.DEFAULT_FIAT
        if tsym == "SAT" or tsym== "SATS":
            target=target/(100.0*1000.0*1000.0)
            tsym="BTC"
        if tsym == "USD":
            tsym = "USDT"


        if not self.repository.isPricePairValid(fsym, tsym):
            self.api.sendMessage(f"Invalid pair {fsym}, {tsym}", chatId)
            return

        if 'alerts' not in self.db:
            self.db['alerts'] = {}
        alerts = self.db['alerts'][chatId] if chatId in self.db['alerts'] else {}
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
        self.db['alerts'][chatId] = alerts
        msg = f'Notification set for {fsym} {"below" if op == "LOWER" else "above"} {format_price(target)} {tsym}.'
        self.api.sendMessage(msg, chatId)

    @cache("cmd.Help", 10)
    def help(self, chatId, command):
        self.log.debug("reading help file")
        with open(config.HELP_FILENAME, 'rb') as fp:
            resp = fp.read()
        self.api.sendMessage(resp, chatId, "Markdown")

    def getTop(self, chatId, command):
        #msg =  self.repository.get_top_coins()
        msg = "Not available temporarily"
        self.api.sendMessage(msg, chatId, parse_mode="MarkdownV2")
    
    def alerts(self, chatId, command):
        if 'alerts' in self.db and chatId in self.db['alerts']:
            alerts=self.db['alerts'][chatId]
            msg = 'Current alerts:\n'
            for fsym in alerts:
                for op in alerts[fsym]:
                    for tsym in alerts[fsym][op]:
                        for target in alerts[fsym][op][tsym]:
                            msg=f'{msg}{fsym} {op} {target} {tsym}\n'
            self.api.sendMessage(msg, chatId)
        else:
            self.api.sendMessage('No alert is set',chatId)


    CommandMap = {
        "start":    help,
        "help":     help,
        "all":      getTop,
        "top":      getTop,
        "alerts":   alerts,
        "clear":    clear,
        "price":    price,    
        "p":        price,
        "chart":    chart,
        "ch":       chart,
        "higher":   higher_lower,
        "lower":    higher_lower
    }