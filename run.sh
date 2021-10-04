cd /home/rcl/price_alert_bot
pwd
source venv/bin/activate
logfile="price.log"
if [ -f "$logfile" ] 
then mv "$logfile" "$logfile.$(date +%F-%T)"
fi
python3 tg_bot_service.py 
