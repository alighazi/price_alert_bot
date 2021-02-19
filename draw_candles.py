import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from candle import Candle
from formating import format_price

class DrawChart:
    IMG_WIDTH = 1280 
    IMG_HEIGHT = 720
    CHART_MARGIN_LEFT = 80
    CHART_MARGIN_BOTTOM = 40
    CHART_MARGIN_TOP = 30
    CHART_PADDING = 5
    CANDLE_PADDING = 2
    FONT_PATH = "font/UbuntuMono-Regular.ttf"

    #open, close, low, high
    #candles=[(30,40,24,44),(40,24,24,55),(24,24,15,35),(24,24,10,24),(24,10,10,24),(10,33,10,33),(33,35,30,40),(30,40,12,44),(50,45,40,50)]

    def validate_candles(self, candles):
        for k in candles:
            c = candles[k]
            assert c.high >= c.low, "error! candle {}={} has high < low!".format(k, c)
            assert c.high >= c.open, "error! candle {}={} has high < open!".format(k, c)
            assert c.high >= c.close, "error! candle {}={} has high below close!".format(k, c)
            assert c.low <= c.high, "error! candle {}={} has low above high!".format(k, c)
            assert c.low <= c.open, "error! candle {}={} has low above open!".format(k, c)
            assert c.low <= c.close, "error! candle {}={} has low above close!".format(k, c)

    def normalize_candle(self, candle, minVal, maxVal):
        ratio = (self.IMG_HEIGHT -  self.CHART_MARGIN_BOTTOM - self.CHART_MARGIN_TOP - self.CHART_PADDING * 2.0) / (maxVal - minVal)
        # (320 - 30 -10) / 55-24 = 9
        bottom = self.IMG_HEIGHT - self.CHART_MARGIN_BOTTOM - self.CHART_PADDING
        return Candle(bottom -  (candle.open - minVal)* ratio, 
        bottom -  (candle.high - minVal)* ratio, 
        bottom -  (candle.low - minVal)* ratio, 
        bottom -  (candle.close - minVal)* ratio, 
        candle.open_time, candle.close_time, candle.volume)

    def draw_chart_frame(self, draw, minVal, maxVal, symbol):
        color=(255,255,255)
        left = self.CHART_MARGIN_LEFT
        right = self.IMG_WIDTH
        bottom = self.IMG_HEIGHT - self.CHART_MARGIN_BOTTOM
        top = 0    
        MARGIN=2
        font = ImageFont.truetype(self.FONT_PATH, 14)
        # valStr = "{:.1f}".format(minVal)
        # size = draw.textsize(str(valStr), font)
        # draw.text((left-size[0]-MARGIN, bottom - size[1]- self.CHART_PADDING - MARGIN), str(valStr), color, font)

        # length = int(math.floor(math.log10(math.floor(maxVal))+1)) if maxVal>=1 else 0
        # precision = 8 - length

        color_bg=(100,100,100)
        LINES=12
        for i in range(0, LINES+1):        
            y = bottom - (i/LINES) * (bottom - top -self.CHART_MARGIN_TOP - self.CHART_PADDING*2) - self.CHART_PADDING
            draw.line([(left, y), (right, y)], color_bg, 1)
            x = left + (i/LINES) * (right - left)
            draw.line([(x, top), (x, bottom)], color_bg, 1)
            val =minVal + (i/LINES) * (maxVal - minVal)
            valStr = format_price(val)
            size = draw.textsize(valStr, font)
            draw.text((left-size[0]-MARGIN, y - size[1]-MARGIN), valStr, color, font)

        draw.line([(left, bottom), (right, bottom)], color, 1)
        draw.line([(left, top), (left, bottom)], color, 1)
        #draw legend
        font_legend = ImageFont.truetype(self.FONT_PATH, 18)
        draw.text((left, top), symbol, (255,255,0), font_legend)


    def draw_candles(self, draw, candles, symbol):
        if len(candles) == 0:
            return #nothing to draw
        self.validate_candles(candles)

        first_candle = candles[next(iter(candles))]
        minVal = first_candle.low
        maxVal = first_candle.high
        for k in candles:
            c = candles[k]
            if c.low < minVal:
                minVal = c.low
            if c.high > maxVal:
                maxVal = c.high

        self.draw_chart_frame(draw, minVal, maxVal, symbol)
        #print('totalMin: {}, max: {}'.format(minVal, maxVal))
        #normalizing the values
        for k in candles:
            candles[k] = self.normalize_candle(candles[k], minVal, maxVal)
            #print('open: {}, close: {}, low: {}, high {}'.format(c.open,c.close,c.low,c.high))
        
        candleWidth = (self.IMG_WIDTH-self.CHART_MARGIN_LEFT-self.CHART_PADDING*2)/len(candles)

        i=0
        for k in candles:
            c = candles[k]
            color = (10,255,25)#GREEN!
            if c.close > c.open:
                color = (255,10,25)#RED!

            #draw the wick
            x = ((i*candleWidth) + candleWidth/2.0) + self.CHART_MARGIN_LEFT + self.CHART_PADDING
            y1= c.low#low
            y2= c.high#high   
            #print("wick from {} to {}".format(y1, y2))
            draw.line([(x,y1), (x,y2)], color, 1)

            #draw the body
            #x = (i*candleWidth+) + self.CHART_MARGIN_LEFT + self.CHART_PADDING
            y1 = c.open#open
            y2 = c.close#close
            if abs(y1 - y2) < 1:
                y2-=(1 - abs(y1 - y2))
            #print("body from {} to {}".format(y1, y2))
            draw.line([(x,y1), (x,y2)], color, int(math.floor(candleWidth)) - self.CANDLE_PADDING*2)
            i+=1

        #TODO draw current price horizontal line
        #TODO draw moving averages (SMA/EMA)
        #TODO draw volume bars

    def save(self, output_path, candles, symbol):
        img = Image.new('RGB', (self.IMG_WIDTH,self.IMG_HEIGHT))
        draw = ImageDraw.Draw(img)
        self.draw_candles(draw, candles, symbol)
        img.save(output_path)

