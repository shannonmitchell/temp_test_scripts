#!/usr/bin/python 

import os
import cv2
import sys
import time
import numpy
import urllib
import pickle
import argparse
#import matplotlib
from matplotlib import pyplot as plt



###############
# Global Vars
###############

# global template related vars
templates = []
t_index = 0

# global vars for selecting 4 points
count = 0
points = list()

# set up working space image vars
findspotimg = []
findspotclean = []

# locate of config path for feeds
feeds_path = "./feeds"

# set current feed name and url
session_feed_name = ''
session_feed_url = ''

############################
# Create a new feed config
############################
def createFeed(feedname='', feedurl=''):

    # Make sure the local 'feeds' directory
    global feeds_path
    if not os.path.exists(feeds_path):
        print "Creating %s" % feeds_path
        os.makedirs(feeds_path)

    # get the feed name
    if feedname == '':
        feedname = raw_input("Feed Name(alpha-numeric no spaces): ")

    # get the url
    if feedurl == '':
        feedurl = raw_input("Feed URL: ")

    # create the feed directory and url config file
    feedpath = "%s/%s" % (feeds_path, feedname)
    if not os.path.exists(feedpath):
        print "Creating %s" % feedpath
        os.makedirs(feedpath)

    # create the url config file
    urlconfig = "%s/url" % (feedpath)
    if not os.path.exists(feedurl):
        print "Creating %s" % feedurl
        urlfile = open(urlconfig, 'w')
        urlfile.write(feedurl)
        urlfile.close()

    # return the feed name and url for current use
    return [feedname, feedurl]

    

###############
# Load Config
###############
def loadConfig(feedname=''):

    # Make sure the local 'feeds' directory
    global feeds_path
    if not os.path.exists(feeds_path):
        print "Creating %s" % feeds_path
        os.makedirs(feeds_path)

        # If none exist, create one
        feedinfo = createFeed()
        feedname = feedinfo[0]

    # If no feed names provided yet, lets check and prompt the user
    while True:
        feedlist = os.listdir(feeds_path)
        x = 0
        feedarr = []
        for curdir in feedlist:
            feedarr.append(curdir)
            print "%s: %s" % (x, curdir)
            x = x + 1
        print "n: new feed"
        print "x: exit"
        entry = raw_input("Select a feed: ")
        if entry == 'x':
            sys.exit(0)
        if entry == 'n':
            feedinfo = createFeed()
            feedname = feedinfo[0]
            break
        else:
            feedname = feedarr[int(entry)]
            break
    
    # Get the provided feed's url
    feedpath = "%s/%s" % (feeds_path, feedname)
    urlconfig = "%s/url" % (feedpath)
    if os.path.exists(urlconfig):
        urlfile = open(urlconfig, 'r')
        feedurl = urlfile.read()
        urlfile.close
    else:
        feedinfo = createFeed(feedname=feedname)
        feedname = feedinfo[0]
        feedurl = feedinfo[1]
   
    # Pull templates 
    templatedata = []
    templatedata = loadTemplates(feedname)

    # return the feed name and url for current use
    return [feedname, feedurl, templatedata]
    

##################
# Load Templates
##################
def loadTemplates(feedname):
    curtemplates = []

    template_loc = "%s/%s/templates" % (feeds_path, feedname)
    if not os.path.exists(template_loc):
        return curtemplates
    else:
        templatefile = open(template_loc, 'rb')
        curtemplates = pickle.load(templatefile)
        templatefile.close()

    return curtemplates
  

##################
# Save Templates
##################
def saveTemplates(feed_name):

    global feeds_path
    global templates

    template_loc = "%s/%s/templates" % (feeds_path, feed_name)

    # go through and just dump the templates var via pickle for now
    print "Saving templates to %s" % template_loc
    templatefile = open(template_loc, 'wb')
    pickle.dump(templates, templatefile, pickle.HIGHEST_PROTOCOL)
    templatefile.close()


###########################################################
# Scan through the template and draw out polygons for all
###########################################################
def fillAllTemplates(curimg):
    for template in templates:
        cv2.fillConvexPoly(curimg, template['polypoints'], (255, 255, 255))

###########################################################
# Scan through the template and draw out lines for all
###########################################################
def lineAllTemplates(curimg):
    green = (0, 255, 0)
    red = (255, 0, 255)
    curcolor = red
    x = 0
    for template in templates:
        curpoints = template['points']
        if 'hascar' in template:
            if template['hascar'] == 1:
                curcolor = green
            else:
                curcolor = red
        cv2.line(curimg, curpoints[0], curpoints[1], curcolor, 2)
        cv2.line(curimg, curpoints[1], curpoints[2], curcolor, 2)
        cv2.line(curimg, curpoints[2], curpoints[3], curcolor, 2)
        cv2.line(curimg, curpoints[3], curpoints[0], curcolor, 2)


        h, w = curimg.shape[:2]
        cv2.putText(img = curimg, 
                text = "%d" % (x),
                org = (curpoints[0][0] + 20, curpoints[0][1] + 20), 
                fontFace = cv2.FONT_HERSHEY_DUPLEX, 
                fontScale = .5, 
                color = (255,0,0),
                thickness = 1)
        x = x + 1

######################################################################
# Take the width, height and a set of points.  Create a blank image
# with a white template from the points. Store it as well as other
# data into a global templates var for use by other functions.
######################################################################
def createTemplateFromPoints(curimg_h, curimg_w, curpoints):

    # init global vars
    global templates
    global t_index
 
    # Create a blank image for the template
    blankimg = numpy.zeros((curimg_h, curimg_w, 3), numpy.uint8)

    # convert points to an array the poly functions understand
    pg_points = []
    for point in points:
        pg_points.append([point[0],point[1]])
    

    # fill in a polygon
    spacepoints = numpy.array([pg_points], numpy.int32)
    cv2.fillConvexPoly(blankimg, spacepoints, (255, 255, 255))

    # Create a template(using an index for now)
    curdata = {}
    curdata['points'] = curpoints
    curdata['template'] = blankimg.copy()
    curdata['polypoints'] = spacepoints
    curdata['drawmain'] = 0
    templates.insert(t_index, curdata)
    t_index = t_index + 1



###############################################################################################
# Track clicks so things are visible to the user.  Store the template data after the 4th click
###############################################################################################
def processClick(event, x, y, flags, param):

    # define globals(to clean up the image for the user between defining spaces)
    global findspotimg
    global findspotclean

    # define globals(to track state of previous clicks between function calls)
    global count
    global points

    # A mouse button was pressed
    if event == cv2.EVENT_LBUTTONDOWN:

        # Append the current points to the global points var 
        pval = (x, y)
        points.append(pval)

        # Curcle it on the 'findspot' named window to let the user know
        cv2.circle(findspotimg, (x, y), 8, (255, 0, 0), 2)
        cv2.imshow('findspot', findspotimg)

        # increment the cound between each click
        count += 1

        # on the 4th click process the points
        if count == 4:

            # get the width and height
            h, w = findspotimg.shape[:2]

            # let the user know we have 4 points on the terminal
            print "We have 4 points!!"

            # connect and draw the points
            cv2.line(findspotimg, points[0], points[1], (0, 255, 0), 2)
            cv2.line(findspotimg, points[1], points[2], (0, 255, 0), 2)
            cv2.line(findspotimg, points[2], points[3], (0, 255, 0), 2)
            cv2.line(findspotimg, points[3], points[0], (0, 255, 0), 2)

            # redraw the screen
            cv2.imshow('findspot', findspotimg)
            cv2.waitKey(1) # force a redraw
            print points

            # Sleep a few
            time.sleep(1)

            # Create a template from the points 
            createTemplateFromPoints(h, w, points)

            # Clean the findspotimg
            findspotimg = findspotclean.copy()

            # clean the screen after giving the user time to see it
            #fillAllTemplates(findspotimg)
            lineAllTemplates(findspotimg)
            cv2.imshow('findspot', findspotimg)
            cv2.waitKey(1) # force a redraw

            # reset the values for the next run of 4
            count = 0
            points = list()




##########################################################################
# Create a separate image to allow the user to click out parking spaces
##########################################################################
def findParkingSpace(jpg, feed_name):


    # Set up global vars
    global findspotimg
    global findspotclean
    global templates

    # Display a single frame to use for reference
    findspotimg = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8),cv2.IMREAD_COLOR)
    findspotclean = findspotimg.copy()

    # put in instructions
    h, w = findspotimg.shape[:2]
    cv2.putText(img = findspotimg, 
                text = "x: exit, s: save and exit, c: clear spaces",
                org = (0,0 + 10), 
                fontFace = cv2.FONT_HERSHEY_DUPLEX, 
                fontScale = .5, 
                color = (0,0,255),
                thickness = 1)

    cv2.imshow('findspot', findspotimg)

    # If templates is already populated, add the lines for it
    if templates != []:
        lineAllTemplates(findspotimg)
        cv2.imshow('findspot', findspotimg)
        cv2.waitKey(1) # force a redraw

    # Set a mouse callback to select the spaces
    cv2.setMouseCallback('findspot', processClick)

    # Loop through and wait for key presses. For each run a process click function.
    while True:
        key = cv2.waitKey(0) & 0xff
        # Exit on ESC and 'x'
        if key == 27 or key == ord('x'):
            cv2.destroyWindow('findspot')
            break
        # Clear all templates
        if key == ord('c'):
            templates = []
            findspotimg = findspotclean.copy()
            cv2.imshow('findspot', findspotimg)
        # Save current template configuration
        if key == ord('s'):
            saveTemplates(feed_name)
            cv2.destroyWindow('findspot')
            break

##########################################################    
# Start pulling down the video and processing the frames
##########################################################    
def processStream(feed_name, feed_url):

    # not much hear now, but may need to work with different stream types
    stream = urllib.urlopen(feed_url)
    bytes=''

    # Loop through and process camera frames
    while True:

        # read jpg from stream
        bytes += stream.read(16384)
        a = bytes.find('\xff\xd8')
        b = bytes.find('\xff\xd9')
        if a != -1 and b != -1:
            jpg = bytes[a:b+2]
            bytes= bytes[b+2:]
            
            # get current color frame 
            curframe = cv2.imdecode(numpy.fromstring(jpg, dtype=numpy.uint8),cv2.IMREAD_COLOR)

            # mark out any lines
            lineAllTemplates(curframe)

            # put in instructions
            h, w = curframe.shape[:2]
            cv2.putText(img = curframe, 
                        text = "x: exit, h: checkspots, p: make spaces",
                        org = (0,0 + 10), 
                        fontFace = cv2.FONT_HERSHEY_DUPLEX, 
                        fontScale = .5, 
                        color = (0,0,255),
                        thickness = 1)

            # display the frame
            cv2.imshow('original', curframe)


        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('x'):
            cv2.destroyWindow('original')
            break
        if key == ord('p'):
            print "Sets run the parking space selector while blocking"
            findParkingSpace(jpg, feed_name)

        if key == ord('h'):
            print "Show histogram's for slots"
            updateHistograms(curframe)


    # destroy if we break out of the loop
    cv2.destroyAllWindows()


##########################################################################
# Get histogram info for spots and check if a car is in the spot
##########################################################################
def updateHistograms(curimg):

    # Set up global vars
    global templates

    # thresholds
    triggerlimit = 10 # value to look for to find beginning and end of spikes
    rangestart = 0    # start reading histogram from
    #rangestop = 140   # stop reading histogram here and ignore upper values
    rangestop = 255   # stop reading histogram here and ignore upper values
    concval = 700     # empty spots will have a larger concentration of certain colors
    widthlimit = 41   # The limit for the width of the larges spike. If lower then this it looks like a free space.

    # Parse through each template and get a mask from the current image
    x = 0
    for template in templates:
        maskimg = template['template']
        curgray = cv2.cvtColor(curimg,cv2.COLOR_BGR2GRAY)
        maskgray = cv2.cvtColor(maskimg,cv2.COLOR_BGR2GRAY)
        histr = cv2.calcHist([curgray],[0], maskgray, [256], [0, 256])
        template['hist'] = histr
        #print histr

        lwranges = []
        findlower = 1
        findupper = 0
        curlower = 0
        curhigher = 0
        highestconcentration = 0
        for i in range(rangestart, rangestop):
            #print "i: %s  findlower: %s findupper: %s" % (i, findlower, findupper)
            if histr[i] > highestconcentration:
                highestconcentration = histr[i]
            if findlower == 1 and histr[i] > triggerlimit:
                #print "found lower %s" % i
                curlower = i
                findlower = 0
                findupper = 1
                continue
            if findupper == 1 and histr[i] < triggerlimit:
                #print "found upper %s" % i
                curupper = i
                findlower = 1
                findupper = 0
                #print currange
                lwranges.append([curlower, curupper])
                continue

        highestrange = 0
        print lwranges
        for ulrange in lwranges:
            currange = ulrange[1] - ulrange[0]
            #print "cur: %s  high: %s" % (currange, highestrange)
            if currange > highestrange:
                highestrange = currange
        print "Highest range in historgram above %s is %s" % (triggerlimit, highestrange)
        print "Highest concentration of color is %s" % highestconcentration

        if highestconcentration > concval and highestrange < widthlimit:
            print "hc: %s con: %s setting to red. highestrange is %s" % (highestconcentration, concval, highestrange)
            template['hascar'] = 0
        else:
            print "hc: %s con: %s setting to green. highestrange is %s" % (highestconcentration, concval, highestrange)
            template['hascar'] = 1
                
        #print histr[i]

        #imgname = "hist%d" % x
        #cv2.imshow(imgname, maskgray)
        #x = x + 1
        #cv2.waitKey(1) # force a redraw

        plt.plot(histr)
        plt.xlim([0, 256])
        plt.show()
       

        

######################
# Da shit starts here
######################
def main():

    global templates

    configinfo = loadConfig()
    templates = configinfo[2]
    processStream(configinfo[0], configinfo[1])


if __name__ == '__main__':
  main()
