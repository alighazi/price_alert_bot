import pickle, time, requests
import symbols, math
import json
from datetime import datetime
import jsonpickle

dbFileName = 'db.json'

with open(dbFileName, 'rb') as fp:
    db = pickle.load(fp)

frozen = jsonpickle.encode(db)
print(frozen)
