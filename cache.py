import pickle
from pathlib import Path
from time import time, sleep
from datetime import datetime
import logger_config

class cache:
    cache = {}
    FILENAME="data/cache.pickle"
    LOADED = False
    log = logger_config.instance
    def __init__(self, key, secs, per_args = []):
        if not cache.LOADED:
            my_file = Path(cache.FILENAME)
            if not cache.LOADED and my_file.is_file():
                try:
                    with open(cache.FILENAME, 'rb') as fp:
                        cache.cache = pickle.load(fp)
                        self.log.debug(f"opened cache db: {len(cache.cache)} entries")
                        cache.LOADED = True
                except:
                    self.log.error("failed to load cache file,")
                    cache.LOADED = False

        self.__secs = secs
        self.__key = key
        self.__per_args = per_args
 
    def __call__(self, fn):
        def wrapped(*args, **kwargs):
            key = self.__key
            for arg_pos in self.__per_args:
                if arg_pos >= len(args):
                    raise IndexError(f"the {arg_pos}th argument not found in the invocation of the method: {fn}. make sure you are calling the method with the right number of the arguments")
                key +="|"+ str(args[arg_pos])
            if key in cache.cache:
                entry = cache.cache[key]
                if entry[0] + self.__secs >= time():
                    return entry[1]
                else:
                    self.log.debug(f"cache expired for key: {key}")
            
            returnValue = fn(*args, **kwargs)
            if returnValue== None:
                self.log.warn(f"'None' return! key: {key}")
            cache.cache[key] = [time(), returnValue]
            return returnValue        
 
        return wrapped
    
    @staticmethod
    def persist():
        with open(cache.FILENAME, 'wb') as fp:
            pickle.dump(cache.cache, fp)

    @staticmethod
    def invalidate(key):
        if key in cache.cache:
            del cache.cache[key]
