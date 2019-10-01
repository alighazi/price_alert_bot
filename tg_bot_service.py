import traceback, time
import tg_bot

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
    time.sleep(1)

