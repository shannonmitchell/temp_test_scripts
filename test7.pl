#!/usr/bin/python

import cv2
import numpy


def slope (x1, y1, x2, y2):
    x3 = (x2 - x1)
    y3 = (y2 - y1)
    print "%s / %s" % (y3, x3)

    m = (float(y3)/float(x3))
    return m

def yintercept(m, x2, y2):
    b = y2 - (m*x2)
    return b 

def findslopey(x, m, b):
    y = (m * x) + b
    return y

def findslopex(y, m, b):
    x = ((y - b) / m)
    return x
    

# Find the white in the image
def findWhite(curmat, x1, y1, x2, y2):
  height, width = curmat.shape
  print "height: %s width: %s" % (height, width)

  # Lets find the slope intercept equasion's slope and y intercept
  m = slope(x1, y1, x2, y2)
  print "m is %s" % m
  b = yintercept(m, x2, y2)
  print "b is %s" % b

  # If x1 is less than zero lets make it zero and find y
  if x1 < 0:
    yret = findslopey(0, m, b)
    print "when x = 0 y is: %s" % yret
    x1 = 0
    y1 = yret

  # If y1 is less than zero, lets make the needed adjustments
  if y1 < 0:
    m = slope(x1, y1, x2, y2)
    b = yintercept(m, x2, y2)
    xret = findslopex(0, m, b)
    print "when y = 0 x is: %s" % xret
    x1 = xret
    y1 = 0

  # if x2 > width lets make it the width and find y
  if x2 > width:
    yret = findslopey(width, m, b)
    print "when x = %s y is: %s" % (width, yret)
    x2 = width
    y2 = yret
  
  # if y2 > height lets make it the height and find x
  if y2 > height:
    xret = findslopey(height, m, b)
    print "when y = %s x is: %s" % (height, xret)
    x2 = xret
    y2 = height
 
  for curx in range(0, width):
    cury = findslopey(curx, m, b)
    #print "cx: %s cy: %s" % (curx, cury)
    if cury > height:
      break
    print curmat[cury,curx]
  

def main():

  # Clean up the image.
  img = cv2.imread('pl.jpg')
  gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
  ret,thresh = cv2.threshold(gray,190,255,cv2.THRESH_BINARY)
  edges = cv2.Canny(thresh,50,150,apertureSize = 3)



  # Detect the lines
  lines = cv2.HoughLines(edges,1,numpy.pi/180,110)
  for rho,theta in lines[0]:
    #print rho
    #print theta
    a = numpy.cos(theta)
    b = numpy.sin(theta)
    x0 = a*rho
    y0 = b*rho
    x1 = int(x0 + 2000*(-b))
    y1 = int(y0 + 2000*(a))
    x2 = int(x0 - 2000*(-b))
    y2 = int(y0 - 2000*(a))

    findWhite(thresh, x1, y1, x2, y2)
    cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)
    break




  # Display and wait
  cv2.imshow("gray", gray)
  cv2.imshow("edges", edges)
  cv2.imshow("thresh", thresh)
  cv2.imshow("houghlines", img)
  cv2.waitKey(0)


if __name__ == '__main__':
  main()
