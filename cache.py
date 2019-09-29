import pickle
from pathlib import Path
from time import time, sleep
from datetime import datetime

class cache:
    cache = {}
    FILENAME="cache.pickle"
    LOADED = False
    def __init__(self, key, secs, per_args = []):
        if not cache.LOADED:
            my_file = Path(cache.FILENAME)
            if not cache.LOADED and my_file.is_file():
                try:
                    with open(cache.FILENAME, 'rb') as fp:
                        cache.cache = pickle.load(fp)
                        print(f"opened cache db: {len(cache.cache)} entries")
                        cache.LOADED = True
                except:
                    print("failed to load cache file,")
                    cache.LOADED = False

        self.__secs = secs
        self.__key = key
        self.__per_args = per_args
 
    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            key = self.__key
            for arg_pos in self.__per_args:
                key +="|"+args[arg_pos]
            if key in cache.cache:
                entry = cache.cache[key]
                print(f"cache found for key: {key}")
                if entry[0] + self.__secs >= time():
                    print("valid! returning!")
                    return entry[1]
                else:
                    print("expired!")
            
            returnValue = fn(*args, **kwargs)
            if returnValue== None:
                print(f"warning, None return! key: {key}")
            cache.cache[key] = [time(), returnValue]
            return returnValue        
 
        return wrapped
    
    @staticmethod
    def persist():
        with open(cache.FILENAME, 'wb') as fp:
            print(f"persisting cache: {len(cache.cache)} entries")
            pickle.dump(cache.cache, fp)

    @staticmethod
    def invalidate(key):
        if key in cache.cache:
            del cache.cache[key]
