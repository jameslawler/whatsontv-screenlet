#!/usr/bin/env python

#  XMLTV (c) JamesL 2007

import xml.dom.minidom
import time
import datetime

#---------------------------------------------------------
# Class: XMLTV
# Description: XMLTV is a simple python class that can
#   load an XMLTV file and retrieve;
#	1) Channels details
#	2) Programs on now
#	3) Programs on next
#
#   The XMLTV class is designed to be efficient. The
#   UpdateNowShows and UpdateNextShows functions should
#   only be called at large intervals (eg 10 minutes).
#
#   To actually retrieve the list of now and next shows
#   you should access the self.channels[].nowShow or the
#   self.channels[].nextShow
#
#   The DoLoad function should be called at very large
#   intervals to reload the entire file. This is incase
#   more than 24hrs has past and the xmltv file could
#   have been updated with new data.
#---------------------------------------------------------
class Xmltv:

    #
    # Constructor
    #	
    def __init__(self, filepath):
        self.filepath = filepath
	self.channels = []
	self.noneChannel = Channel('None', 'None', 'None', 999)

    #
    # DoLoad
    # Pre: Set the self.filepath to the xmltv file before calling DoLoad
    # Return: If the load is successful the funciton will return 1 for true
    #	      Else 0 will be returned for false
    #	
    def DoLoad(self):
        print "DoLoad: Loading " + self.filepath

	try:
		#Clear existing data
		self.ClearChannels()
		
		#Load in XML File
		doc = xml.dom.minidom.parse(self.filepath)

		#Load Channels
		chanCount = 0
		nodes = doc.getElementsByTagName("channel")
		for node in nodes:
			chanDisplayNameList = node.getElementsByTagName("display-name")
			if (not chanDisplayNameList == []):
				chanDisplayName = chanDisplayNameList[0].firstChild.nodeValue
			else:
				chanDisplayName = "No Name"
			chanId = node.getAttribute("id")
			if len(chanId) > 0: #only add the channel if it has an id
				chanIconList = node.getElementsByTagName("icon")
				if (not chanIconList == []):
					chanIcon = chanIconList[0].getAttribute("src")
				else:
					chanIcon = None
				self.channels.append(Channel(chanDisplayName, chanId, chanIcon, chanCount))

				chanCount = chanCount + 1

		self.channels.sort()

		#Load Programs into the correct channel
		nodes = doc.getElementsByTagName("programme")
		for node in nodes:
			progTitleList = node.getElementsByTagName("title")
			if (not progTitleList == []):
				progTitle = progTitleList[0].firstChild.nodeValue
			progStart = node.getAttribute("start")
			progStop = node.getAttribute("stop")
			progDescription = "No Data Available"		# there is no need for description but i am leave code here for future references
			progChannelId = node.getAttribute("channel")

			# Add this program to the correct channel based on the channel id
			# This could be a bottleneck but there are not noramally many channels so could be ok
			for channel in self.channels:
				if (channel.id == progChannelId):
					channel.AddProgramme(progTitle, progStart, progStop, progDescription)

		print "DoLoad: Successfully loaded the XMLTV file"
		return 1

	except:
		print "DoLoad: An error occurred while trying to load the XMLTV file"
		return 0

    #
    # ClearChannels
    #	
    def ClearChannels(self):

	# Loop through all the channels and clear them
	for channel in self.channels:
		self.channels.DoClear()
		self.channels.remove(channel)

    #
    # UpdateNowShows
    #	
    def UpdateNowShows(self):

	# Loop through all the channels and get the program that is showing now
	# The program details are stored in self.channel.nowShow
	for channel in self.channels:
		programme = channel.GetProgrammeShowingAt(datetime.datetime.now())
		#print "Channel " + channel.name + ' is showing ' + programme.title + ' now.'

    #
    # UpdateNextShows
    #	
    def UpdateNextShows(self):

	# Loop through all the channels and get the program that is showing next
	# The program details are stored in self.channel.nextShow
	for channel in self.channels:
		programme = channel.GetProgrammeShowingNextAt(datetime.datetime.now())
		#print "Channel " + channel.name + ' is showing ' + programme.title + ' next.'

#---------------------------------------------------------
# Class: Channel
# Description: Channel is a simple python class that can
#   hold channel details and the channels current show
#   and next show
#---------------------------------------------------------
class Channel:

    #
    # Constructor
    #	
    def __init__(self, name, id, iconpath, order):
	self.name = name
	self.id = id
	self.order = order
	self.iconpath = iconpath
	self.programs = []
	self.defaultNoShow = Programme("Data Unavailable", "20001231125959", "20991231125959", "There is no data available for this time")
	self.nowShow = self.defaultNoShow
	self.nextShow = self.defaultNoShow

    #
    # Compare
    # This function is used to show python the order the channels should be in when doing a sort
    #	
    def __cmp__(self, other):
	return cmp(self.order, other.order)

    #
    # DoClear
    #	
    def DoClear(self):
	for programme in self.programs:
		self.programs.remove(programme)

    #
    # AddProgramme
    #	
    def AddProgramme(self, title, start, stop, description):
	self.programs.append(Programme(title, start, stop, description))

    #
    # SortPrograms
    #	
    def SortPrograms(self):
	self.programs.sort()

    #
    # GetProgrammeShowingAt
    # Returns the programme showing at the specified time
    # If there is no programme then the default no data show is returned
    #	
    def GetProgrammeShowingAt(self, time):
	for programme in self.programs:
		if (programme.start <= time and programme.stop >= time):
			self.nowShow = programme
			return programme

	return self.defaultNoShow

    #
    # GetProgrammeShowingNextAt
    # Returns the programme showing after the show showing at the specified time
    # If there is no programme then the default no data show is returned
    #		
    def GetProgrammeShowingNextAt(self, time):
	showNext = "false"
	for programme in self.programs:
		if (showNext == "true"):
			self.nextShow = programme
			return programme

		if (programme.start <= time and programme.stop >= time):
			showNext = "true"

	return self.defaultNoShow

#---------------------------------------------------------
# Class: Programme
# Description: Programme is a simple python class that can
#   hold programme details
#---------------------------------------------------------
class Programme:

    #
    # Constructor
    #	
    def __init__(self, title, start, stop, description):
	self.title = title
	self.start = datetime.datetime(*time.strptime(start[0:13],"%Y%m%d%H%M%S")[0:5])		#Convert to a datetime object
	self.stop = datetime.datetime(*time.strptime(stop[0:13],"%Y%m%d%H%M%S")[0:5])		#Convert to a datetime object
	self.description = description
	self.escaped_title = self.escape(title)							# Change to special chaarcters
	self.escaped_description = self.escape(description)					# Change to special chaarcters

    #
    # Compare
    # This function is used to show python the order the programs should be in when doing a sort
    #	
    def __cmp__(self, other):
	return cmp(self.start, other.start)


    #
    # escape
    # This function is used to change certain characters to their escaped version to keep drawing on screen happy
    #	
    def escape(self, inputString):
	inputString = inputString.replace('&', '&amp;')
	inputString = inputString.replace('<', '&lt;')
	inputString = inputString.replace('>', '&gt;')
	inputString = inputString.replace('"', '&quot;')
	inputString = inputString.replace("'", '&#39;')

	return inputString


