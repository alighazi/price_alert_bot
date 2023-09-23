import math, time, requests, pickle, traceback
from datetime import datetime, timedelta


from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from cache import cache
from repository.market import MarketRepository
import config
from formating import format_price
from api.binance_rest import CandleInterval

from utils import get_id
from utils import human_format_seconds
from utils import is_valid_number_or_percentage

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
            elif command.startswith('showwatches'):
                self.showwatches(chatId, command)
            elif command.startswith('clearwatches'):
                self.clearwatches(chatId, command)
            elif command.startswith('delete'):
                self.delete(chatId, command)
            else:
                self.api.sendMessage('Unknown command', chatId)

    def delete(self, chatId, command):
        parts = command.split()
        # self.log.debug('Delete command')
        
        if len(parts) == 1:  # list all the watches and alerts with an ID
            # self.log.debug('Delete listing')
            deleteList  = "Here are the alerts and watches you can delete: \n \n"
            
                # first list all the alerts that belong to this user, and give a 4 letter ID which is the first three letters of a hash of the item
                # this is so that the user can delete the alert by typing the ID
                # this is not a security measure, it is just to make it easier for the user to delete the alerts
                # if the user is not logged in, the ID will be the same as the alert ID, so
            if 'alerts' in self.db and chatId in self.db['alerts']:
                alerts=self.db['alerts'][chatId]
                for fsym in alerts:
                    for op in alerts[fsym]:
                        for tsym in alerts[fsym][op]:
                            for target in alerts[fsym][op][tsym]:
                                hashOfAlert = get_id(chatId, target)[:4]
                                alertString = f'{fsym} {op} {target} {tsym}\n' 
                                deleteList += f'ID={hashOfAlert} : {alertString} \n'
            else:
                deleteList += 'No alert is set \n\n'

            # now the watches
            if 'watches' in self.db:
                for watch in self.db['watches']:
                    if watch['chatId'] == chatId:
                        hashOfWatch = str(get_id(chatId,watch)[:4])
                        # persistString is either blank or the word "persistent" followed by the notification frequency
                        if 'persistent' in watch and watch['persistent']:
                            persistString =f'persistent {human_format_seconds(watch["notify_frequency"])}'
                        else:
                            persistString = ''
                        
                        watchString = f'{watch["fsym"]} {watch["op"]} {watch["target"]} {watch["duration"]} {watch["duration_type"]} {persistString}'
                        deleteList += f'ID={hashOfWatch} : {watchString} \n'
                        
            else:
                deleteList += '\n No watches  \n'


            deleteList += ' \nTo delete an alert or watch, type /delete <ID>'
            

            self.api.sendMessage(deleteList, chatId)

        elif len(parts) == 2: # delete a specific watch or alert
            # get the id and make sure it is a 4 digit hex value
            deleteID = parts[1]
            if len(deleteID)!= 4:
                self.api.sendMessage("Invalid ID, must be 4 characters long", chatId)
                return
            
            # if it is not valid hex then error and return
            try:
                int(deleteID, 16)
            except:
                self.api.sendMessage("Invalid ID, must be 4 hex characters long", chatId)
                return           


# here we scan through all of them and find the one to delete
            if 'alerts' in self.db and chatId in self.db['alerts']:
                alerts=self.db['alerts'][chatId]
                for fsym in alerts:
                    for op in alerts[fsym]:
                        for tsym in alerts[fsym][op]:
                            for target in alerts[fsym][op][tsym]:
                                alertString = f'{fsym} {op} {target} {tsym}\n' 
                                hashOfAlert = get_id(chatId, target)[:4]
                                if deleteID == hashOfAlert:
                                    self.db['alerts'][chatId][fsym][op][tsym].remove(target)
                                    self.api.sendMessage(f'Alert deleted {alertString}', chatId)
                                    self.log.info(f'Alert deleted {alertString}')
                                    return

            # now the watches
            if 'watches' in self.db:
                for watch in self.db['watches']:
                    if watch['chatId'] == chatId:
                        watchString = f'{watch["fsym"]} {watch["op"]} {watch["target"]} {watch["duration"]} {watch["duration_type"]}'
                        hashOfWatch = get_id(chatId, watch)[:4]
                        if str(deleteID) == str(hashOfWatch):
                            self.db['watches'].remove(watch)
                            self.api.sendMessage(f'Watch deleted {watchString}', chatId)
                            self.log.info(f'Watch deleted {watchString}')
                            return
                        
            self.api.sendMessage('Delete ID not found', chatId)
            
        else:
            self.api.sendMessage('Invalid delete command, use /delete for list of ids or /delete <id> to delete ', chatId)
            return




    def clear(self, chatId, command):
        if 'alerts' in self.db and chatId in self.db['alerts']:
            self.db['alerts'].pop(chatId)
        self.api.sendMessage('Done.',chatId)


    def clearwatches(self, chatId, command):
        if 'watches' not in self.db:
            self.api.sendMessage("No watches", chatId)
            return

        for watch in self.db['watches']:
            if watch['chatId'] == chatId:
                self.db['watches'].remove(watch)

        self.api.sendMessage("Done.", chatId)

    def showwatches(self, chatId, command):
        if 'watches' not in self.db or len(self.db['watches']) == 0:
            self.api.sendMessage("No watches", chatId)
            return

        msg = ''
        for watch in self.db['watches']:
            if watch['chatId'] == chatId:
                # persistString is either empty or it the word "persistent" followed by the notify_frequency duration
                persistString = ''
                if 'persistent' in watch and watch['persistent']:
                    persistString =f'persistent repeating every {human_format_seconds(watch["notify_frequency"])}'
                msg += '{} {} {} {} {} {}\n'.format(watch['fsym'], watch['op'], watch['target'], watch['duration'], watch['duration_type'], persistString)
        
                
        self.api.sendMessage(msg, chatId)

    def watch(self, chatId, command):
        # command structured

        # ( 0     1   2    3   4  5     6             7 )
        # /watch btc drop 50% 14 days            (6 parts)
        # /watch btc rise 50% 1 month            (6 parts)
        # /watch btc rise 50% 1 month persistent            (7 parts)
        # /watch btc drop 5000 2 days            (6 parts)
        # /watch btc drop 5000 from ath            (6 parts)
        # /watch btc drop 5000 from ath persistent {hourly|daily|weekly|minute}            (7/8 parts)
        # /watch btc stable 1% 1 week persistent              (7 parts)
        # /watch btc stable 1% 1 week persistent weekly            (8 parts)
        # ( 0     1   2    3   4  5     6             7 )


        # not yet implemented
        # ( 0     1   2    3   4  5     6             7   8)        
        # /watch btc stable 1% 1 week persistent weekly monday           (9 parts)
        # /watch btc stable 1% 1 week persistent daily 10:00           (9 parts)


        frequency_mapping = {
            'weekly': 7 * 24 * 60 * 60,
            'daily': 24 * 60 * 60,
            'hourly': 60 * 60,
            'minute': 60
        }

        parts = command.lower().split()
        if not (len(parts) in [6,7,8]): # if you don't specify period it is days

            self.api.sendMessage("Invalid command, see help", chatId)
            return
        

        fsym = parts[1].upper()

        tsym = config.DEFAULT_FIAT

        notify_frequency = 24 * 60 * 60 # default is daily

        op = parts[2].lower()
        if op not in ['drop','rise', 'stable']:
            self.api.sendMessage("Invalid command, must be drop, rise or stable", chatId)
            return


        if not is_valid_number_or_percentage(parts[3]):
            self.api.sendMessage("Invalid command, must be a number", chatId)
            return
        
        # this line never executes if there was something wrong with the target
        target = parts[3]


        # part 4 is always a number, unless it is "from"
        duration = parts[4]
        # if duration is not a number then something is wrong, return error unless it is "from"
        if duration.lower() == 'from':
            if parts[5].lower() == 'ath':
                from_ath = True
                # rise from ath makes no sense and should error
                if op == 'rise':
                    self.api.sendMessage("Invalid command, rise from ath makes no sense", chatId)
                    return
            else:
                self.api.sendMessage("Invalid command, must be from ath", chatId)
                return
        else:
            from_ath = False    

            try:
                duration = int(duration)
            except:
                self.api.sendMessage("Invalid command, must be a number or from ath", chatId)
                return

        # if there is a 6th part, it is the duration type
        if len(parts) > 5:
            duration_type = parts[5]
        else:
            duration_type = 'days'


        # if there are 6 or 7 parts and the last part starts 'persist' then persistence is true
        persistence = False
        if len(parts) in [7, 8]:
            if (parts[6].lower().startswith('persist')):
                persistence = True
                notify_frequency = 24 * 60 * 60 # 24 hours
                if len(parts) in [8]:
                    if parts[7] in frequency_mapping:
                        notify_frequency = frequency_mapping[parts[7]]
                    else:
                        self.api.sendMessage("Invalid frequency, must be minute, hourly, daily, weekly", chatId)
                        return
            else:
                self.api.sendMessage("Badly formed command, are you trying to watch persistently? Try `/watch btc stable 5% 1 week persist daily` to be informed daily if btc has been stable for a week within a 5% +/- range ", chatId)
                return



        if not self.repository.isPricePairValid(fsym, tsym):
            self.api.sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
            return
        
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
        watch['persistent'] = persistence

        watch['notify_frequency']  = notify_frequency
        watch['last_notify'] = 0 # Zero epoch



        if 'watches' not in self.db:
            self.db['watches'] = []


        self.db['watches'].append( watch) 
        # self.api.sendMessage("Watch added", chatId)

        resp = 'Watching {} {} {} {} {} {} {}'.format(fsym, op, parts[3], parts[4], parts[5], parts[6], parts[7])

        self.api.sendMessage(resp, chatId)
        return

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