import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 

IMG_WIDTH = 640 
IMG_HEIGHT = 480
CHART_MARGIN_LEFT = 40
CHART_MARGIN_BOTTOM = 40
CHART_MARGIN_TOP = 30
CHART_PADDING = 5
CANDLE_PADDING = 2
FONT_PATH = "font/UbuntuMono-Regular.ttf"

img = Image.new('RGB', (IMG_WIDTH,IMG_HEIGHT))
draw = ImageDraw.Draw(img)
# draw.text((x, y),"Sample Text",(r,g,b))
#draw.text((0, 0),"baba kosts! vaghean",(255,255,255),font=font)

#open, close, min, high
candles=[(30,40,24,44),(40,24,24,55),(24,24,15,35),(24,24,10,24),(24,10,10,24),(10,33,10,33),(33,35,30,40),(30,40,12,44),(50,45,40,50)]

def validate_candles(candles):
    for i in range(0, len(candles)):
        c = candles[i]
        if c[3] < c[2]:
            print("error! candle {}={} has high below low!".format(i, c))
            return False
        if c[3] < c[0]:
            print("error! candle {}={} has high below open!".format(i, c))
            return False
        if c[3] < c[1]:
            print("error! candle {}={} has high below close!".format(i, c))
            return False
        if c[2] > c[3]:
            print("error! candle {}={} has min above high!".format(i, c))
            return False
        if c[2] > c[0]:
            print("error! candle {}={} min high above open!".format(i, c))
            return False
        if c[2] > c[1]:
            print("error! candle {}={} min high above close!".format(i, c))
            return False

def normalize_candle(candle, minVal, maxVal):
    ratio = (IMG_HEIGHT -  CHART_MARGIN_BOTTOM - CHART_MARGIN_TOP - CHART_PADDING * 2.0) / (maxVal - minVal)
    # (320 - 30 -10) / 55-24 = 9
    bottom = IMG_HEIGHT - CHART_MARGIN_BOTTOM - CHART_PADDING
    return ((bottom -  (candle[0] - minVal)* ratio),
            (bottom -  (candle[1] - minVal)* ratio),
            (bottom -  (candle[2] - minVal)* ratio),
            (bottom -  (candle[3] - minVal)* ratio))

def draw_chart_frame(draw, minVal, maxVal):
    color=(255,255,255)
    left = CHART_MARGIN_LEFT
    right = IMG_WIDTH
    bottom = IMG_HEIGHT - CHART_MARGIN_BOTTOM
    top = 0    
    MARGIN=2
    font = ImageFont.truetype(FONT_PATH, 10)
    # valStr = "{:.1f}".format(minVal)
    # size = draw.textsize(str(valStr), font)
    # draw.text((left-size[0]-MARGIN, bottom - size[1]- CHART_PADDING - MARGIN), str(valStr), color, font)

    color_bg=(100,100,100)
    LINES=12
    for i in range(0, LINES+1):        
        y = bottom - (i/LINES) * (bottom - top -CHART_MARGIN_TOP - CHART_PADDING*2) - CHART_PADDING
        draw.line([(left, y), (right, y)], color_bg, 1)
        x = left + (i/LINES) * (right - left)
        draw.line([(x, top), (x, bottom)], color_bg, 1)
        val =minVal + (i/LINES) * (maxVal - minVal)
        valStr = "{:.1f}".format(val)
        size = draw.textsize(valStr, font)
        draw.text((left-size[0]-MARGIN, y - size[1]-MARGIN), valStr, color, font)

    draw.line([(left, bottom), (right, bottom)], color, 1)
    draw.line([(left, top), (left, bottom)], color, 1)


def draw_candles(draw, candles):
    if len(candles) == 0:
        return #nothing to draw
    if validate_candles(candles) == False:
        return
    minVal=candles[0][2]
    maxVal=candles[0][3]
    for c in candles:
        if c[2] < minVal:
            minVal = c[2]
        if c[3] > maxVal:
            maxVal = c[3]

    draw_chart_frame(draw, minVal, maxVal)
    print('totalMin: {}, max: {}'.format(minVal, maxVal))
    #normalizing the values
    for i in range(0, len(candles)):
        candles[i] = normalize_candle(candles[i], minVal, maxVal)
    
    candleWidth = (IMG_WIDTH-CHART_MARGIN_LEFT-CHART_PADDING*2)/len(candles)

    for c in candles:
        print('open: {}, close: {}, low: {}, high {}'.format(c[0],c[1],c[2],c[3]))

    for i in range(0, len(candles)):
        c = candles[i]
        color = (10,255,25)#GREEN!
        if c[1] < c[0]:
            color = (255,10,25)#RED!

        #draw the wick
        x = ((i*candleWidth) + candleWidth/2.0) + CHART_MARGIN_LEFT + CHART_PADDING
        y1= c[2]#min
        y2= c[3]#high   
        print("wick from {} to {}".format(y1, y2))
        draw.line([(x,y1), (x,y2)], color, 1)

        #draw the body
        #x = (i*candleWidth+) + CHART_MARGIN_LEFT + CHART_PADDING
        y1 = c[0]#open
        y2 = c[1]#close
        if y1 == y2:
            y2-=1
        print("body from {} to {}".format(y1, y2))
        draw.line([(x,y1), (x,y2)], color, int(math.floor(candleWidth)) - CANDLE_PADDING*2)

    
draw_candles(draw,candles)
img.save('wolf.png')

