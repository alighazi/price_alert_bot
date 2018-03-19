import pickle, time, requests
import symbols, math
import json
from datetime import datetime

def getTop():
    url = "https://api.coinmarketcap.com/v1/ticker/?limit=1000"
    r = requests.get(url)
    out=''
    for coin in r.json():
        out += "('{}','{}'),".format(coin['symbol'], coin['name'])
    print(out)
    return out


print(list(symbols.symbols.keys()).index('STORM'))

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

def getPrice(a,b):
    return 110

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
                            print('{} is {} {} {} at {}'.format(symbols.name(fsym), 'below' if op == lower else 'above' ,target, tsym, price) + chatId)
                            toRemove.append((fsym,tsym, target, chatId,op))

    for tr in toRemove:
        removeAlert(tr[0],tr[1],tr[2],tr[3],tr[4])    


