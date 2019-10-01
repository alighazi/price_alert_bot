import traceback, time
import tg_bot
import tg_bot_service
from cache import cache

tgbot= tg_bot.TgBot()
tgbot.init()

#main loop
loop=True
while loop:    
    try:
        updates = tgbot.getUpdates()        
        if updates == None:
            print('update request failed \n{}'.format(updates))
        else:
            tgbot.processUpdates(updates)

        try:
            tgbot.processAlerts()
        except:
            traceback.print_exc()
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        loop=False
    except:
        traceback.print_exc()      

    tgbot.persist_db()
    cache.persist()
    time.sleep(1)

