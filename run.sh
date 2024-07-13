source venv/bin/activate
mkdir -p log data
logfile="price.log"
if [ -f "$logfile" ] 
then mv "$logfile" "$logfile.$(date +%F-%T)"
fi
python3 tg_bot_service.py

