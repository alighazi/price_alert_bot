from math import floor, log10

def format_price(price):
    precision = max(0,min(-floor(log10(price))+2,8))       
    return f'{price:.{precision}f}'