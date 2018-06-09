import sys, math, time, requests, pickle, traceback
from datetime import datetime
import collections
import symbols

TG_TOKEN = '404889667:AAEZAEMoqItZw0M9IMjGO1OtTp17eMZdqp4'
DB_FILENAME = 'db.json'
CACHE_DURATION = 10  # seconds
DEFAULT_FIAT = "USD"
PARTITION_SIZE= 45
TSYMS = ['BTC','USD','EUR','SEK','IRR','JPY','CNY','GBP','CAD','AUD','RUB','INR','USDT','ETH']

def log(str):
    print('{} - {}'.format(datetime.today(), str))

def isPricePairValid(fsym, tsym):
    return fsym in get_symbols().keys() and tsym in TSYMS

def get_symbols(update=False):
    last_symbol_update= db['last_symbol_update'] if 'last_symbol_update' in db else 0
    if time.time()-last_symbol_update < CACHE_DURATION:
        return db['symbols']
    if update or 'symbol' not in db:
        print('loading symbols from network')
        url = "https://min-api.cryptocompare.com/data/top/totalvol?limit=1000&tsym=USD"
        r = requests.get(url)
        syms = collections.OrderedDict()
        data = r.json()["Data"]
        for coin in data:
            syms[coin["CoinInfo"]["Internal"]]= coin["CoinInfo"]["FullName"]
        db['last_symbol_update'] = time.time()
        db['symbols']=syms
        return syms

def get_price(fsym, tsym):
    symbols=get_symbols(True)
    index=list(symbols.keys()).index(fsym)
    partition= index//PARTITION_SIZE

    if 'last_price_queries' not in db:
        db['last_price_queries']={}    
    last_price_queries=db['last_price_queries']

    if 'price_partitions' not in db:
        db['price_partitions']={}
    price_partitions=db['price_partitions']                

    print('index: {}, partition: {}, fsym: {}, tsym: {}'.format(index,partition, fsym,tsym))

    if (partition not in last_price_queries) or (time.time() - last_price_queries[partition]> CACHE_DURATION):
        index_start = max(0, partition * PARTITION_SIZE - 2)
        index_end = index_start + PARTITION_SIZE
        fsyms = list(symbols.keys())[index_start : index_end]
        url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}".format(','.join(fsyms), ','.join(TSYMS))
        r = requests.get(url)
        price_partitions[partition]= r.json()
        last_price_queries[partition] = time.time()

    if isPricePairValid(fsym, tsym):
        return price_partitions[partition][fsym][tsym]


def getTop():
    if ('last_top_query' not in db) or (time.time() - db['last_top_query'] > CACHE_DURATION):
        url = "https://api.coinmarketcap.com/v1/ticker/?limit=32"
        r = requests.get(url)
        out = "`"
        for coin in r.json():
            cap_f=math.floor(float(coin['market_cap_usd']))
            cap_s=''
            if cap_f>1000*1000*1000:
                cap_s='${:.3f}B\n'.format(cap_f/(1000*1000*1000))
            else:
                cap_s='${:.3f}M\n'.format(cap_f/(1000*1000))
                
            out = out+coin['rank']+': ' + coin['symbol']+' '+coin['price_usd'] + \
                '$\t'+coin['price_btc']+'BTC\t' + cap_s
        out = out+'`'
        db['top'] = out
        db['last_top_query'] = time.time()
    else:
        log('reading from the cache')

    return db['top']

def getTgUrl(methodName):
    return 'https://api.telegram.org/bot{}/{}'.format(TG_TOKEN, methodName)

def getUpdates(offset):
    url = getTgUrl('getUpdates')
    r = requests.post(
        url=url, data={'offset': offset, 'limit': 100, 'timeout': 9})
    return r

def sendMessage(msg, chatid, parse_mode=None):
    url = getTgUrl('sendMessage')
    r = requests.post(url=url, data={
        'chat_id': chatid,
        'text': msg,
        'parse_mode': parse_mode
    })
    return r

def format_price(price, tsym):
    if tsym=="BTC" or tsym=="ETH":
        return '{:.8f}'.format(price)
    
    return '{:.2f}'.format(price)
    

def handleBotCommand(message):
    text = message['text']
    chatId = message['chat']['id']
    command = text.partition('/')[2]
    log('handling command "{}"...'.format(command))

    if command == 'start' or command == 'help':
        resp = """
Hi, welcome to the Crypto price notification bot
Set alerts on your favorite crypto currencies. Get notified and earn $$$"""
        sendMessage(resp, chatId)

    elif command == 'all' or command == 'top':
        resp = getTop()
        sendMessage(resp, chatId, 'Markdown')

    elif command == 'alerts':
        if 'alerts' in db and chatId in db['alerts']:
            alerts=db['alerts'][chatId]
            msg='Current alerts:\n'
            for fsym in alerts:
                for op in alerts[fsym]:
                    for tsym in alerts[fsym][op]:
                        for target in alerts[fsym][op][tsym]:
                            msg='{}{} {} {} {}\n'.format(msg, get_symbols()[fsym], op, target,tsym)
            sendMessage(msg, chatId)
        else:
            sendMessage('No alert is set',chatId)

    elif command=='clear':
        if 'alerts' in db and chatId in db['alerts']:
            db['alerts'].pop(chatId)
        sendMessage('Done.',chatId)
    
    elif command.startswith('price'):
        parts = command.upper().split()
        if len(parts) < 2:
            sendMessage("Invalid command", chatId)
            return
        fsym = parts[1]
        tsym = DEFAULT_FIAT
        if len(parts) > 2:
            tsym = parts[2]
        if not isPricePairValid(fsym, tsym):
            sendMessage("Invalid symbols {} {}".format(fsym,tsym), chatId)
            return

        price = get_price(fsym, tsym)
        resp = '1 {} = {} {}'.format(get_symbols()[fsym], format_price(price, tsym),tsym)
        sendMessage(resp, chatId)

    elif command.startswith('lower') or command.startswith('higher'):
        parts = command.upper().split()
        if len(parts) < 3 or len(parts) > 4:
            sendMessage("Invalid command", chatId)
            return
        op = parts[0]
        fsym = parts[1]
        if not fsym in get_symbols().keys():
            sendMessage('Invalid symbol "{}"'.format(fsym), chatId)
            return
        try:
            target = float(parts[2])
        except ValueError:
            sendMessage('Invalid number "{}"'.format(parts[2]), chatId)
            return
        tsym = parts[3] if len(parts) > 3 else DEFAULT_FIAT
        if tsym == "SAT" or tsym== "SATS":
            target=target/(100.0*1000.0*1000.0)
            tsym="BTC"

        if tsym not in TSYMS:
            sendMessage('Invalid symbol {}'.format(tsym), chatId)
            return

        if 'alerts' not in db:
            db['alerts'] = {}
        alerts = db['alerts'][chatId] if chatId in db['alerts'] else {}
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
        db['alerts'][chatId] = alerts
        msg = 'Notification set for {} {} {} {}.'.format(
            get_symbols()[fsym], 'below' if op == 'LOWER' else 'above', format_price(target, tsym), tsym)
        sendMessage(msg, chatId)
    else:
        sendMessage('Unknown command', chatId)

def processMessage(message):
    text = message['text']
    chatId = message['chat']['id']
    if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
        handleBotCommand(message)
    else:
        sendMessage('Invalid command', chatId)

def removeAlert(fsym, tsym, target, chatId, op):
    alerts = db['alerts']
    alerts[chatId][fsym][op][tsym].remove(target)
    if len(alerts[chatId][fsym][op][tsym]) == 0:
        alerts[chatId][fsym][op].pop(tsym)
        if len(alerts[chatId][fsym][op]) == 0:
            alerts[chatId][fsym].pop(op)
            if len(alerts[chatId][fsym]) == 0:
                alerts[chatId].pop(fsym)
                if len(alerts[chatId]) == 0:
                    alerts.pop(chatId)

def processAlerts():
    if 'alerts' not in db:
        return
    higher = 'HIGHER'
    lower = 'LOWER'
    alerts = db['alerts']
    toRemove = []
    for chatId in alerts:
        for fsym in alerts[chatId]:
            ops = alerts[chatId][fsym]
            for op in ops:
                tsyms = ops[op]
                for tsym in tsyms:
                    targets = tsyms[tsym]
                    price = get_price(fsym, tsym)
                    for target in targets:
                        if op == lower and price < target or op == higher and price > target:
                            sendMessage('{} is {} {} at {} {}'.format(get_symbols()[fsym],
                             'below' if op == lower else 'above', format_price(target, tsym), format_price(price, tsym), tsym), chatId)
                            toRemove.append((fsym, tsym, target, chatId, op))

    for tr in toRemove:
        removeAlert(tr[0], tr[1], tr[2], tr[3], tr[4])

try:
    with open(DB_FILENAME, 'rb') as fp:
        db = pickle.load(fp)
except:
    db = {}
log("db at start:\n {}".format(db))
last_update = db['last_update'] if 'last_update' in db else 0

main loop
loop=True
while loop:
    
    try:
        updates = getUpdates(last_update+1)        
        updates = updates.json()
    except KeyboardInterrupt:
        log("W: interrupt received, stopping…")
        loop=False
    except:
        traceback.print_exc()      

    if not 'ok' in updates or not updates['ok']:
        log('update request failed \n{}'.format(updates))
    else:
        for update in updates['result']:
            log('processing {}...'.format(update['update_id']))
            message = update['message'] if 'message' in update else update['edited_message']
            try:
                processMessage(message)
                last_update = update['update_id']
                db['last_update'] = last_update
            except:
                traceback.print_exc()

    try:
        processAlerts()
    except:
        traceback.print_exc()

    with open(DB_FILENAME, 'wb') as fp:
        pickle.dump(db, fp)
    time.sleep(1)

