import traceback
import time
import datetime
import tg_bot
from cache import cache


def main():
    tgbot = tg_bot.TgBot()
    tgbot.init()
    # main loop
    loop = True
    while loop:    
        try:
            #print(f"{datetime.datetime.today()} Getting updates…")
            updates = tgbot.getUpdates()       
            if updates is None:
                print('update request failed \n{}'.format(updates))
            else:
                tgbot.processUpdates(updates)

            try:
                tgbot.processAlerts()
            except:
                traceback.print_exc()
        except KeyboardInterrupt:
            print("W: interrupt received, stopping…")
            loop = False
        except:            
            traceback.print_exc()      
            loop = False

        tgbot.persist_db()
        cache.persist()
        time.sleep(1)


if __name__ == "__main__":
    main()