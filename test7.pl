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
def findWhite(curmat, x1, y1, x2, y2, minval):

  # store the line info for a return
  retinfo = {}

  # Get the width and height
  height, width = curmat.shape
  print "height: %s width: %s" % (height, width)

  # Lets find the slope intercept equasion's slope and y intercept
  m = slope(x1, y1, x2, y2)
  print "m is %s" % m
  retinfo['slope'] = m
  b = yintercept(m, x2, y2)
  retinfo['yintercept'] = b
  print "b is %s" % b


  ## Limit values to within the mat to allow for scans ##

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
 

  ## Parse the values along the line and find segments over min ##
  curval = 0
  lastval = 0
  curstart = [0, 0]
  curend = [0, 0]
  for curx in range(0, width):

    # Find y using the slope intercept form
    cury = int(findslopey(curx, m, b))

    #print "cx: %s cy: %s" % (curx, cury)
    # Stop if y gets higher than the height
    if cury >= height:
      break

    # Get the color value from the mat
    colorval = curmat[cury,curx]
   
    # Set the cur value
    curval = colorval

    # If the last value was lower than the curvalue mark it as a start
    if curval > lastval:
      curstart = [curx, cury] 

    # If the last value is greater than the current value mark an end and process
    if curval < lastval:
      curend = [curx, cury]

      # Check that the difference is greater than the provided min
      curdiff = curend[0] - curstart[0]
      if curdiff >= minval:
        print "Found a line segment greater than %s" % minval
        if 'lines' not in retinfo:
          retinfo['lines'] = []
        retinfo['lines'].append([curstart, curend])
        print retinfo['lines']

    # Set the last value for next run
    lastval = curval

  # return the form info and segments
  return retinfo
  
  

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

    lineinfo = findWhite(thresh, x1, y1, x2, y2, 10)
    print lineinfo
    cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)

     
    curcolor = 0
    for line in lineinfo['lines']:
      print "creating line"
      if curcolor == 0:
        linecolor = (0,255,0)
        curcolor = 1
      elif curcolor == 1:
        linecolor = (255,0,0)
        curcolor = 0
 
      cv2.line(img, tuple(line[0]), tuple(line[1]),linecolor,2)
    break




  # Display and wait
  cv2.imshow("gray", gray)
  cv2.imshow("edges", edges)
  cv2.imshow("thresh", thresh)
  cv2.imshow("houghlines", img)
  cv2.waitKey(0)


if __name__ == '__main__':
  main()
