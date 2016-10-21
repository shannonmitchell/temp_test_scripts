#!/usr/bin/python 

import cv2
import numpy
import urllib

cascade = cv2.CascadeClassifier("cars/cars.xml")

stream=urllib.urlopen('http://80.14.234.191:81/mjpg/video.mjpg')
bytes=''

fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
#fgbggmg = cv2.createBackgroundSubtractorGMG2()

while True:
	bytes += stream.read(16384)
	a = bytes.find('\xff\xd8')
	b = bytes.find('\xff\xd9')
	if a != -1 and b != -1:
		jpg = bytes[a:b+2]
		bytes= bytes[b+2:]
		i = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8),cv2.IMREAD_COLOR)

        
		gray = cv2.cvtColor(i, cv2.COLOR_BGR2GRAY)
		#cars = cascade.detectMultiScale(gray, 1.3, 3)
		#ret,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                fgmask = fgbg.apply(gray)
                #fgmaskgmg = fgbg.apply(gray)
		
		#for (x,y,w,h) in cars:
		#	cv2.rectangle(i, (x,y), (x+w,y+h), (0,0,255), 2)

		#cv2.imshow('thresh', thresh)
		cv2.imshow('fgmask', fgmask)
		#cv2.imshow('fgmaskgmg', fgmaskgmg)
		cv2.imshow('gray', gray)
		cv2.imshow('original', i)
		cv2.imwrite('video-file.jpg', i)
		if cv2.waitKey(1) & 0xff == 27:
			break
			
cv2.destroyAllWindows()
