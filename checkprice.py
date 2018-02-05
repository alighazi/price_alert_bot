import requests
import sys
import pickle
import symbols

tgToken = '404889667:AAEZAEMoqItZw0M9IMjGO1OtTp17eMZdqp4'
dbFileName='db.json'
try:
    with open(dbFileName,'rb') as fp:
        db=pickle.load(fp)
except:
    db={}
DefaultFiat = "EUR"


def getPrice(fsym, tsym):
    url = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}".format(
        fsym, tsym)
    r = requests.get(url)
    print(url+'  '+r.text)
    return r.json()[tsym]


def getTop():
    url = "https://api.coinmarketcap.com/v1/ticker/?limit=32"
    r = requests.get(url)
    out = "`"
    for coin in r.json():
        out = out+coin['rank']+': ' + coin['symbol']+' '+coin['price_usd'] + \
            '$\t'+coin['price_btc']+'BTC\t'+coin['market_cap_usd']+'$\n'
    out = out+'`'
    print(out)
    return out


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
        fsym = parts[1]
        tsym = DefaultFiat
        if len(parts) > 2:
            tsym = parts[2]
        tsym = tsym.upper()
        fsym = fsym.upper()
        price = getPrice(fsym, tsym)
        resp = '1 {} = {} {}'.format(symbols.name(fsym), price, tsym)
        sendMessage(resp, chatId)

    elif command.startswith('lower'):
        parts = command.split()
        if len(parts) < 3 or len(parts) > 4:
            sendMessage("invalid command", chatId)
            return
        fsym = parts[1]
        if not fsym in symbols.symbols:
            sendMessage("invalid symbol", chatId)
            return
        try:
            target = int(parts[2])
        except ValueError:
            sendMessage("invalid symbol", chatId)
            return
        tsym = parts[3] if len(parts) > 3 else DefaultFiat
        alerts = db.get(chatId) or {}


def processMessage(message):
    text = message['text']
    chatId = message['chat']['id']
    if('entities' in message and message['entities'][0]['type'] == 'bot_command'):
        handleBotCommand(message)


last_update = db['last_update'] if 'last_update' in db  else 0
#price = getPrice("ETH", "EUR")
# print(price)
# t=getTop()


def dsendMessage(s, c):
    print(s+c)


def test_lower(command):
    parts = command.split()
    chatId = 123
    if len(parts) < 3 or len(parts) > 4:
        dsendMessage("invalid command", chatId)
        return
    fsym = parts[1]
    if not fsym in symbols.symbols:
        dsendMessage("invalid symbol", chatId)
        return
    try:
        target = int(parts[2])
    except ValueError:
        dsendMessage("invalid symbol", chatId)
        return
    tsym = parts[3] if len(parts) > 3 else DefaultFiat
    alerts = db[chatId] if chatId in db else {}
    if fsym in alerts:
        alerts[fsym]['lower'] = '{} {}'.format(target, tsym)
    else:
        alerts[fsym] = {'lower': '{} {}'.format(target, tsym)}
    db[chatId]= alerts


def test_higher(command):
    parts = command.split()
    chatId = 123
    if len(parts) < 3 or len(parts) > 4:
        dsendMessage("invalid command", chatId)
        return
    fsym = parts[1]
    if not fsym in symbols.symbols:
        dsendMessage("invalid symbol", chatId)
        return
    try:
        target = int(parts[2])
    except ValueError:
        dsendMessage("invalid symbol", chatId)
        return
    tsym = parts[3] if len(parts) > 3 else DefaultFiat
    alerts = db[chatId] if chatId in db else {}
    if fsym in alerts:
        alerts[fsym]['higher'] = '{} {}'.format(target, tsym)
    else:
        alerts[fsym] = {'higher': '{} {}'.format(target, tsym)}

    db[chatId] = alerts


# test_lower("lower ZEC 99 USD")
# test_lower("lower BTC 2000 EUR")
# test_lower("lower ETH 30000 SEC")
# test_lower("lower LTC 400")
# test_higher("higher ZEC 500 USD")
# test_higher("higher BTC 6000 EUR")
# test_higher("higher ETH 70000 SEC")
# test_higher("higher LTC 800")
print(db[123])

updates = getUpdates(last_update+1)
print(updates.text)
updates = updates.json()

if not updates['ok']:
    print('request failed \n{}'.format(updates))
    sys.exit()

for update in updates['result']:
    print('processing {}...'.format(update['update_id']))
    message = update['message'] if 'message' in update else update['edited_message']
    processMessage(message)
    db['last_update']= update['update_id']

with open(dbFileName, 'wb') as fp:
    pickle.dump(db, fp)
