logfile="nohup.out"
if [ -f "$logfile" ] 
then mv "$logfile" "$logfile.$(date +%F-%T)"
fi

nohup python3 checkprice.py &