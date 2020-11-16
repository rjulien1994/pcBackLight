import numpy as np
import cv2
import time
import math
import serial
import struct
from PIL import ImageGrab       #import all necessary library

def round_up(n, decimals=0):      #function to round up any value
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

ser = serial.Serial('COM3', 250000)

time.sleep(2) #the arduino reboots when serial com initiated

ledWidth = 14           # number of led for length of screen
ledHeight = 7           # number of led for width of screen
totalLed = 2*(ledWidth+ledHeight);

screenSize = (1920, 1080)   #number of pixels in screen
precision = 20              #so you analyse one pixel out of precision squared

start = time.time()*1000    #store time to see how long one frame takes

dataload = (30,30,30,36)

box = (screenSize[0]/ledWidth, screenSize[1]/(ledHeight+2))     #number of pixel per box 

#for lop in range(50):
while(True):
    

    img = ImageGrab.grab()      #takes screenshot
    img_array = np.array(img)   #convert img into matrix

    

    sampleW = np.zeros((ledWidth,2,3))  #Make room to store top and bottom screen color value
    count = round_up(box[0]/precision)*round_up(box[1]/precision);

    for section in range(ledWidth):                                         #for each led making the top and bottom backlight
        for x in range(int(section*box[0]), int((section+1)*box[0]), precision):    #horizontal shift
            for y in range(0, int(box[1]), precision):                              #vertical shift
                sampleW[section, 0] = sampleW[section, 0] + img_array[y, x]         #top of screen
                sampleW[section, 1] = sampleW[section, 1] + img_array[int(y + box[1]*(ledHeight+1)), x] #bottom of screen


    sampleW = sampleW/count  #get each sample avg

    sampleH = np.zeros((ledHeight,2,3))  #Make room to store top and bottom screen color value


    for section in range(ledHeight):                                         #for each led making the top and bottom backlight
        for y in range(int((section+1)*box[1]), int((section+2)*box[1]), precision):    #vertical shift
            for x in range(0, int(box[0]), precision):                              #horizontal shift
                sampleH[section, 0] = sampleH[section, 0] + img_array[y, x]         #left of screen
                sampleH[section, 1] = sampleH[section, 1] + img_array[y, int(x + box[0]*(ledWidth-1))] #right of screen

            
    sampleH = sampleH/count  #get each sample avg

    result = np.zeros(int(ledHeight*2*3 + ledWidth*2*3))    #creates array for output data

    for i in range(ledWidth):       #transform "square" inti string data for light strips
        for j in range(3):
            result[3*i+j] = int(sampleW[i,0,j])
            result[(ledHeight+ledWidth+i)*3+j] = int(sampleW[ledWidth-1-i,1,j])

    for i in range(ledHeight):
        for j in range(3):
            result[ledWidth*3+3*i+j] = int(sampleH[i,1,j])
            result[(ledHeight+2*ledWidth+i)*3+j] = int(sampleH[ledHeight-1-i,0,j])

    output = np.uint8(result)       #gets rid of unecessary space storage

    

    transfer = 0
    dataSent = 0

    while transfer < 1:
        check = struct.pack('>B', 0);
        while check == struct.pack('>B', 0):
            check = ser.read()
        
            for package in range(1,5):
                if check == struct.pack('>B', package):
                    for i in range(dataload[package - 1]):
                        ser.write(struct.pack('>B',output[i+dataSent]))
                    dataSent = dataSent + dataload[package - 1]

            if check == struct.pack('>B', 5):
                transfer = 1
    
                
    
clock = int(time.time()*1000 - start)
