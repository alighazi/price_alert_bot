import pickle, time, requests
import symbols, math

a=float('123.343')

print(str(math.floor(a)))

def getTop():
    url = "https://api.coinmarketcap.com/v1/ticker/?limit=64"
    r = requests.get(url)
    out=''
    for coin in r.json():
        out = out +"'"+ coin['symbol']+"',"
    print(out)
    return out
l=['BTC','ETH','XRP','BCH','ADA','LTC','NEO','XLM','EOS','XEM','MIOTA','DASH','XMR','TRX','USDT','LSK','VEN','ETC','ICX','QTUM','BTG','XRB','PPT','ZEC','OMG','STEEM','BNB','BCN','SNT','XVG','SC','STRAT','BTS','WTC','MKR','AE','VERI','KCS','REP','ZRX','WAVES','DOGE','DCR','RHOC','HSR','DGD','KNC','ARDR','DRGN','KMD','GAS','ZIL','BAT','ARK','PLR','ETN','LRC','R','DCN','DGB','ELF','PIVX','ZCL','GBYTE']
b=','.join(l)
print(b)
print(time.time()-1517948474.317732)
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

