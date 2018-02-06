import sys, math, time, requests
import pickle
import symbols

tgToken = '404889667:AAEZAEMoqItZw0M9IMjGO1OtTp17eMZdqp4'
dbFileName = 'db.json'
CacheDuration=10 #seconds
try:
    with open(dbFileName, 'rb') as fp:
        db = pickle.load(fp)
except:
    db = {}
DefaultFiat = "EUR"
print ("db at start")
print(db)
last_update = db['last_update'] if 'last_update' in db else 0

def isPricePairValid(fsym, tsym):
    return fsym in symbols.allFsyms and tsym in symbols.allTsyms

def getPrice(fsym, tsym):
    if ('last_price_query' not in db) or (time.time() - db['last_price_query']>CacheDuration):
        url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms={}".format(','.join(symbols.allFsyms),','.join(symbols.allTsyms))
        r = requests.get(url)
        db['prices']=r.json()
        db['last_price_query']=time.time()

    if isPricePairValid(fsym,tsym):
        return db['prices'][fsym][tsym]


def getTop():
    if ('last_top_query' not in db) or (time.time() - db['last_top_query']>CacheDuration):    
        url = "https://api.coinmarketcap.com/v1/ticker/?limit=32"
        r = requests.get(url)
        out = "`"
        for coin in r.json():
            out = out+coin['rank']+': ' + coin['symbol']+' '+coin['price_usd'] + \
                '$\t'+coin['price_btc']+'BTC\t'+str(math.floor(float(coin['market_cap_usd'])))+'$\n'
        out = out+'`'
        db['top']=out

    return db['top']


def getTgUrl(methodName):
    return 'https://api.telegram.org/bot{}/{}'.format(tgToken, methodName)


def getUpdates(offset):
    url = getTgUrl('getUpdates')
    r = requests.post(
        url=url, data={'offset': offset, 'limit': 100, 'timeout': []})
    return r


def sendMessage(msg, chatid, parse_mode=None):
    url = getTgUrl('sendMessage')
    r = requests.post(url=url, data={
        'chat_id': chatid,
        'text': msg,
        'parse_mode': parse_mode
    })
    return r


def handleBotCommand(message):
    text = message['text']
    chatId = message['chat']['id']
    command = text.partition('/')[2]
    print('handling command {}...'.format(command))

    if command == 'start' or command == 'help':
        resp = """
Hi, welcome to the Crypto price notification bot
Set alerts on your favorite crypto currencies. Get notified and earn $$$"""
        sendMessage(resp, chatId)

    elif command == 'all':
        resp = getTop()
        sendMessage(resp, chatId, 'Markdown')

    elif command.startswith('price'):
        parts = command.split()
        if len(parts)<2:
            sendMessage("Invalid command", chatId)
            return
        fsym = parts[1]
        tsym = DefaultFiat
        if len(parts) > 2:
            tsym = parts[2]        
        tsym = tsym.upper()
        fsym = fsym.upper()
        if not isPricePairValid(fsym,tsym):
            sendMessage("Invalid command", chatId)
            return
            
        price = getPrice(fsym, tsym)
        resp = '1 {} = {} {}'.format(symbols.name(fsym), price, tsym)
        sendMessage(resp, chatId)

    elif command.startswith('lower') or command.startswith('higher'):        
        parts = command.split()
        if len(parts) < 3 or len(parts) > 4:
            sendMessage("Invalid command", chatId)
            return
        op=parts[0]
        fsym = parts[1].upper()
        if not fsym in symbols.symbols:
            sendMessage("Invalid symbol {}".format(fsym), chatId)
            return
        try:
            target = float(parts[2])
        except ValueError:
            sendMessage("Invalid number {}".format(parts[2]), chatId)
            return
        tsym = parts[3].upper() if len(parts) > 3 else DefaultFiat
        if 'alerts' not in db:
            db['alerts']={} 
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
        msg = 'Done! you will get notification once {} goes {} {} {}.'.format(
            symbols.symbols[fsym], 'under' if op == 'lower' else 'above' ,target, tsym)
        sendMessage(msg, chatId)
    else:
        sendMessage('Unknown command',chatId)


def processMessage(message):
    text = message['text']
    chatId = message['chat']['id']
    if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
        handleBotCommand(message)
    else:
        sendMessage('Invalid command',chatId)

def removeAlert(fsym, tsym, target, chatId, op):
    alerts=db['alerts']
    alerts[chatId][fsym][op][tsym].remove(target)
    if len(alerts[chatId][fsym][op][tsym])==0:
        alerts[chatId][fsym][op].pop(tsym)
        if len(alerts[chatId][fsym][op])==0:
            alerts[chatId][fsym].pop(op)
            if len(alerts[chatId][fsym])==0:
                alerts[chatId].pop(fsym)
                if len(alerts[chatId])==0:
                    alerts.pop(chatId)

def processAlerts():
    if 'alerts' not in db:
        return
    higher='higher'
    lower='lower'
    alerts=db['alerts']
    toRemove=[]
    for chatId in alerts:
        for fsym in alerts[chatId]:
            ops=alerts[chatId][fsym]
            for op in ops:
                tsyms=ops[op]
                for tsym in tsyms:
                    targets=tsyms[tsym]
                    price=getPrice(fsym, tsym)
                    for target in targets:
                        if op == lower and price<target or op == higher and price>target:
                            sendMessage('{} is {} {} {} at {}'.format(symbols.name(fsym), 'below' if op == lower else 'above' ,target, tsym, price), chatId)
                            toRemove.append((fsym,tsym, target, chatId,op))

    for tr in toRemove:
        removeAlert(tr[0],tr[1],tr[2],tr[3],tr[4])   

#main loop
while True:
    updates = getUpdates(last_update+1)
    print(updates.text)
    updates = updates.json()

    if not updates['ok']:
        print('request failed \n{}'.format(updates))

    for update in updates['result']:
        print('processing {}...'.format(update['update_id']))
        message = update['message'] if 'message' in update else update['edited_message']
        processMessage(message)
        last_update=update['update_id']
        db['last_update'] = last_update

    processAlerts()

    with open(dbFileName, 'wb') as fp:
        pickle.dump(db, fp)
    time.sleep(5)
