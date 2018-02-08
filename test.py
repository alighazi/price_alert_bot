import pickle, time, requests
import symbols, math
from datetime import datetime

def getTop():
    url = "https://api.coinmarketcap.com/v1/ticker/?limit=64"
    r = requests.get(url)
    out=''
    for coin in r.json():
        out = out +"'"+ coin['symbol']+"',"
    print(out)
    return out
l=['BTC','ETH','XRP','BCH','ADA','LTC','NEO','XLM','EOS','XEM','MIOTA','DASH','XMR','TRX','USDT','LSK','VEN','ETC','ICX','QTUM','BTG','XRB','PPT','ZEC','OMG','STEEM','BNB','BCN','SNT','XVG','SC','STRAT','BTS','WTC','MKR','AE','VERI','KCS','REP','ZRX','WAVES','DOGE','DCR','RHOC','HSR','DGD','KNC','ARDR','DRGN','KMD','GAS','ZIL','BAT','ARK','PLR','ETN','LRC','R','DCN','DGB','ELF','PIVX','ZCL','GBYTE']

# filename='db.json'

# try:
#     with open(filename,'rb') as fp:
#         db=pickle.load(fp)
# except:
#     db={}

# print(db)
# db[123]={"new":db}

# with open(filename, 'wb') as fp:
#     pickle.dump(db, fp)

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

db={}
db['alerts']={'123':{'BTC':{'lower':{'EUR':set([600])}}, 'ETH':{'lower':{'USD':set([200]), 'EUR':set([250]), 'SEK':set([10,100,150])}, 'higher':{'USD':set([100])}}}}

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


processAlerts()


print(datetime.today())