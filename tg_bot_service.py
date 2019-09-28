import traceback, time
import tg_bot

tgbot= tg_bot.TgBot()
tgbot.init()

#main loop
loop=True
while loop:
    
    try:
        updates = tgbot.getUpdates()        
    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
        loop=False
    except:
        traceback.print_exc()      

    if updates == None:
        print('update request failed \n{}'.format(updates))
    else:
        for update in updates:
            print('processing {}...'.format(update['update_id']))
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

    tgbot.persist_db()
    time.sleep(1)

