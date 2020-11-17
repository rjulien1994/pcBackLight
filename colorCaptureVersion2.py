import numpy as np
import cv2
import time
import serial
import struct
from PIL import ImageGrab       #import all necessary library

#ser = serial.Serial('COM3', 250000)

#time.sleep(2)

def captureScreen():
    img = ImageGrab.grab()      #takes screenshot
    return np.array(img)        #returns img in matrix

def fetchSamples(nPixelsHorizontal, nPixelsVertical, precision, image, band = 40):
    
    numPix = nPixelsHorizontal + 2*nPixelsVertical
    screenSize = [len(image[0]), len(image)]
    
    border = screenSize[0] // band
    
    OuterLimits = [[ 0, screenSize[0]],[ 0, screenSize[1]]]
    
    ySize = (OuterLimits[1][1] - OuterLimits[1][0]) // nPixelsVertical
    xSize = (OuterLimits[0][1] - OuterLimits[0][0]) // (nPixelsHorizontal+2)
    
    samples = np.zeros((numPix, precision**2, 3))
    

    for box in range(nPixelsVertical):
        sample = image[OuterLimits[1][1] - (box+1)*ySize: OuterLimits[1][1] - box*ySize, OuterLimits[0][1] - border: OuterLimits[0][1]]
        s = 0
        for p1 in range(precision):
            y = int((0.5+p1)*(ySize // precision))
            for p2 in range(precision):
                x = len(sample[0])- 1 - p2* (border // precision)
                samples[box, s] = sample[y, x, 0:3]
                s += 1
    
    for box in range(1, nPixelsHorizontal + 1):
        sample = image[OuterLimits[1][0] : OuterLimits[1][0] + border, OuterLimits[0][1] - (box+1)*xSize: OuterLimits[0][1] - box*xSize]
        s = 0
        for p1 in range(precision):
            x = int((0.5+p1)*(xSize // precision))
            for p2 in range(precision):
                y = p2* (border // precision)
                samples[box-1 + nPixelsVertical, s] = sample[y, x, 0:3]
                s += 1
                
    for box in range(nPixelsVertical):
        sample = image[OuterLimits[1][0] + box*ySize: OuterLimits[1][0] + (box+1)*ySize, OuterLimits[0][0]: OuterLimits[0][0] + border]
        s = 0
        for p1 in range(precision):
            y = int((0.5+p1)*(ySize // precision))
            for p2 in range(precision):
                x = p2* (border // precision)
                samples[box + nPixelsVertical + nPixelsHorizontal, s] = sample[y, x, 0:3]
                s += 1
    
    return samples

def pixelColors(samples):
   
    samplesPerPixel = len(samples[0])
   
    pixelStrip = np.zeros((len(samples), 3))
   
    for i in range(len(samples)):
        pixelStrip[i] = sum(samples[i])/samplesPerPixel
        
    return pixelStrip

def balanceColor(colorList, colorChange, whiteChange, colorThreshold, whiteThreshold, rgbFocus = [1, 1, 1]):  #dims white and brightens color
    
    for i in range(len(colorList)): #dims the colors close to white
       
        maximum = max(colorList[i])
        minimum = min(colorList[i])
        
        if maximum == 0:
            maximum += 1
           
        ratio = minimum/maximum

        if ratio < colorThreshold:
            colorList[i] = focusColor(colorList[i], rgbFocus[0], rgbFocus[1], rgbFocus[2])
            colorList[i] = np.minimum(colorChange*colorList[i], [255, 255, 255])
            
        elif ratio > whiteThreshold:
            colorList[i] = np.maximum(whiteChange*colorList[i], [0, 0, 0])
   
    return colorList

def focusColor(color, redFocus, greenFocus, blueFocus):     #dims or increase britness of colors
    if color[0] == max(color):
        color = color*redFocus
    elif color[1] == max(color):
        color = color*greenFocus
    elif color[2] == max(color):
        color = color*blueFocus
   
    return color

def filterColor(colorList, redFilter, greenFilter, blueFilter):                         #add or lower a color to each pixels
    for i in range(len(colorList)):
        colorList[i] = [min(colorList[i][0]*redFilter, 255), min(colorList[i][1]*greenFilter, 255), min(colorList[i][2]*blueFilter, 255)]
    return colorList

def timeFade(currentData, pastData, weight):
    currentData = (weight*pastData + (1-weight)*currentData)
   
    return currentData

def pixelBlend(colorStrip, numPix, weight):
    
    newColor = np.zeros((len(colorStrip), 3))
    
    for i in range(len(colorStrip)):
        newColor[i] = (sum(colorStrip[i-numPix: i+1+numPix]) - colorStrip[i])/(numPix*2)
        newColor[i] = (newColor[i]*weight + colorStrip[i]*(1-weight))

    return newColor

def sendData(data, loads):
    toSend = []
   
    for pixel in data:
        for c in pixel:
            if c < 10:
                c = 0
            toSend.append(int(c))
   
    for package in range(len(loads)-1):
        print(toSend[loads[package]: loads[package+1]])
        for b in toSend[loads[package]: loads[package+1]]:
            ser.write(struct.pack('>B', b))
           
        check = 0
       
        while check == 0:
            if ser.read() == struct.pack('>B', package+1):
                check = 1
            elif ser.read() == struct.pack('>B', len(loads)):
                check = 1
                package = len(loads)

def sendData2(data, loads):
    toSend = []
   
    for pixel in data:
        for c in pixel:
            if c < 10:
                c = 0
            toSend.append(int(c))
    
    stimer = time.time()
    package = 0
    
    while stimer + 0.25 > time.time() and package < len(loads)-1:
        if ser.in_waiting > 0:
            package = int(ser.read())
            if package < len(loads)-1:
                for b in toSend[loads[package]: loads[package+1]]:
                    ser.write(struct.pack('>B', b))

        

numPixelsX = 29
numPixelsY = 18

precision = 4               #prend 4^2 = 16 points par zone 
colorBoost = 1.2            #boost luminosite de toute les couleurs a 120%
dimWhite = 0.8              #baisse luminosite blanc a 80%
balanceRGB = [1, 1.1, 1]    #augnmente ou diminue liminositer dependent couleur
filtreRGB = [0.8, 1.2, 1]   #reduit rouge a 80%, augmente vert a 120%, ne change pas blue
fade = 0.3                  #coleur depends a 30% des couleur avant
blend = 0.5                 #couleur depends a 50% des couleur autour 
numPixelsBlend = 2          #analyse 2 pixels a gauche et a droite

img = captureScreen()
samples = fetchSamples(numPixelsX, numPixelsY, precision, img)
strip = pixelColors(samples)

for i in range(10):
#while(True):
   
    pastStrip = strip
   
    img = captureScreen()
    samples = fetchSamples(numPixelsX, numPixelsY, precision, img, band = 40)   
    strip = pixelColors(samples)
    strip = balanceColor(strip, colorBoost, dimWhite, 0.8, 0.8, rgbFocus = balanceRGB)
    strip = filterColor(strip, filtreRGB[0], filtreRGB[1], filtreRGB[2])
    strip = timeFade(strip, pastStrip, fade)
    strip = pixelBlend(strip, numPixelsBlend, blend)
    #print(strip)
    sendData(strip, (0,50,100,150,195))
