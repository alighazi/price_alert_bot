import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from datetime import datetime
import config


class TgApi:
    TG_BASE_URL = "https://api.telegram.org"
    def __init__(self, log):
        self.log = log
        self.request_session = requests.Session()
        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])
        self.request_session.mount(TgApi.TG_BASE_URL, HTTPAdapter(max_retries=retries))

    def getTgUrl(self, methodName):
        return f'{TgApi.TG_BASE_URL}/bot{config.TG_TOKEN}/{methodName}'

    def sendMessage(self, msg, chatid, parse_mode=None):
        self.log.debug(f"sending msg to {chatid} '{msg}'")
        url = self.getTgUrl('sendMessage')
        r = requests.post(url=url, data={
            'chat_id': chatid,
            'text': msg,
            'parse_mode': parse_mode
        })
        return r

    def sendPhoto(self, fileName, caption, chatid, parse_mode=None):
        files = {'photo': open(fileName, 'rb')}
        url = self.getTgUrl('sendPhoto')
        r = self.request_session.post(url=url, data={
            'chat_id': chatid,
            'caption': caption,
            'parse_mode': parse_mode,
        }, files= files)
        return r

    def getUpdates(self, last_update):
        offset = last_update+1
        url = self.getTgUrl('getUpdates')
        r = self.request_session.post(
            url=url, data={'offset': offset, 'limit': 100, 'timeout': 9})
        updates = r.json()
        if not 'ok' in updates or not updates['ok']:
            return None
        return updates['result']