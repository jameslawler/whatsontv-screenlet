#!/usr/bin/env python

#  WhatsOnTV (c) JamesL 2007 <>
#
# INFO:
# - A screenlet to display XMLTV tv guide listings with logos
# 
# TODO:
# - Thread the image downloader so it doesn't halt the screenlet while downloading

import screenlets
from screenlets.options import StringOption, FileOption, ListOption, IntOption
import pango
import cairo
import gobject
import gtk
import os
from urllib2 import urlopen
from XMLTV import Xmltv

class WhatsOnTVScreenlet (screenlets.Screenlet):
	"""A screenlet to display now and next TV listings from an XMLTV file"""
	
	# default meta-info for Screenlets (should be removed and put into metainfo)
	__name__	= 'WhatsOnTVScreenlet'
	__version__	= '0.2'
	__author__	= 'JamesL'
	__desc__	= __doc__	# set description to docstring of class
	
	# editable options (options that are editable through the UI)
	xmltv_file_path = 'listing.xml'
	xmltv_num_channels = 6
	xmltv_channels = []
	chanmenu_item = None

	__timeout = None
	update_interval = 5

	text_x	= 50
	text_y	= 5
	icon_width = 40
	icon_height = 40
	height_one_channel = 51
	width_one_channel = 270

	tvGuide = Xmltv('')
	selectedChannel = tvGuide.noneChannel
	p_layout = None
	
	# constructor
	def __init__ (self, **keyword_args):
		#call super (width/height MUST match the size of graphics in the theme)
		screenlets.Screenlet.__init__(self, width=270, height=310, 
			uses_theme=True, **keyword_args)
		# set theme
		self.theme_name = "default"
		# add menuitems
		self.add_menuitem('load_xmltv', 'Refresh Data')
		self.add_menuitem('download_icons', 'Download Channel Logos')
		self.add_menuitem('', '-')
		self.add_menuitem('channel_up', 'Move Channel Up')
		self.add_menuitem('channel_down', 'Move Channel Down')
		self.add_default_menuitems()
		# add option group
		self.add_options_group('WhatsOnTVScreenlet', 'XMLTV Details')
		# add editable option
		self.add_option(FileOption('WhatsOnTVScreenlet', 		# group name
			'xmltv_file_path',					# attribute-name
			self.xmltv_file_path,					# default-value
			'XMLTV File Path', 					# widget-label
			'File Path to the XMLTV file for your tv data',		# description
			['*.xml'], True, True
			))

		self.add_option(IntOption('WhatsOnTVScreenlet', 		# group name
			'xmltv_num_channels',					# attribute-name
			self.xmltv_num_channels,				# default-value
			'Number of Channels', 					# widget-label
			'Number of channels to display in the screenlet',	# description
			min=1, max=20
			))

		self.add_option(ListOption('WhatsOnTVScreenlet', 		# group name
			'xmltv_channels',					# attribute-name
			self.xmltv_channels,					# default-value
			'XMLTV Channels', 					# widget-label
			'The order in which the channels are displayed',	# description
			hidden=True						# user should not edit this
			))

		self.update_interval = self.update_interval

	# attribute-"setter", handles setting of attributes
	def __setattr__ (self, name, value):

		#temp fix to stop bug where the FileOption value is being set to False
		if name == 'xmltv_file_path':
			if value == False:
				return True #do not save this change
			elif self.xmltv_file_path != None and value != self.xmltv_file_path:
				self.xmltv_channels = [] #reset channel list incase this new file does not have these channels

		# call Screenlet.__setattr__ in baseclass (ESSENTIAL!!!!)
		screenlets.Screenlet.__setattr__(self, name, value)
		# check for this Screenlet's attributes, we are interested in:
		if name == "update_interval":
			if value > 0:
				self.__dict__['update_interval'] = value
				if self.__timeout:
					gobject.source_remove(self.__timeout)
				self.__timeout = gobject.timeout_add(int(value * 1000), self.update_listings)
			else:
				# TODO: raise exception!!!
				self.__dict__['update_interval'] = 1
				pass
	
	def on_init (self):
		print "Started WhatsOnTV Screenlet"

		#Load the xmltv file
		self.load_xmltv()

	def on_mouse_down (self, event):
		self.selectedChannel = self.get_channel_at_pixel(event.x, event.y)

	def on_menuitem_select (self, id):
		if id == 'load_xmltv':
			self.load_xmltv()

		if id == 'channel_up':
			self.move_channel_up(self.selectedChannel)

		if id == 'channel_down':
			self.move_channel_down(self.selectedChannel)

		if id == 'download_icons':
			for channel in self.tvGuide.channels:
				self.download_icon(channel)

		if id[0:7] == 'channel':
			chanId = id[8:]
			for channel in self.tvGuide.channels:
				if channel.id == chanId:
					if channel.order >= 0:
						self.hide_channel(channel)
						return True
					else:
						self.show_channel(channel)
						return True
			

	def on_draw (self, ctx):
		# if theme is loaded
		if self.theme:
			# set scale rel. to scale-attribute
			ctx.scale(self.scale, self.scale)

			#loop each channel and print a tv box for each one
			topHeight = 0
			height = 50
			topBetween = 1
			chanCount = 0
		
			ctx.save()
			if self.get_number_displayed_channels() == 0:
				ctx.translate(0, topHeight)
				ctx.scale(1, 1)
				self.theme.render(ctx, 'background')
				self.draw_text(ctx, "No XMLTV data found.", self.text_x - 10, topHeight + self.text_y)
				self.draw_text(ctx, "Check your XMLTV file.", self.text_x - 10, 25 + self.text_y)
			ctx.restore()

			for channel in self.tvGuide.channels:
				#Check if we can show more channels
				if channel.order >=0 and chanCount < self.xmltv_num_channels:
					#Increment the channel counter
					chanCount = chanCount + 1

					#Draw background image for each channel
					ctx.save()
					ctx.translate(0, topHeight)
					ctx.scale(1, 1)
					self.theme.render(ctx, 'background')
					ctx.restore()

					#Draw channel icon
					chanIconFilePath = self.get_screenlet_dir() + '/logos/' + channel.id + '.png'
					if os.path.exists(chanIconFilePath):
						ctx.save()
						try:
							ctx.translate(5, topHeight + 5)
							img = cairo.ImageSurface.create_from_png(chanIconFilePath)
							if img:
								scale_width = float(self.icon_width)/float(img.get_width())
								scale_height = float(self.icon_height)/float(img.get_height())
								ctx.scale(scale_width, scale_height)
								ctx.set_source_surface(img, 0, 0)
								ctx.paint()
						except:
							print 'Error occurred while loading logo for channel - ' + channel.id
						ctx.restore()

					#Draw the Now text
					self.draw_text(ctx, "(" + channel.nowShow.start.strftime("%H:%M") +  ") " + channel.nowShow.escaped_title, self.text_x, topHeight + self.text_y)

					#Draw the Next text
					self.draw_text(ctx,"(" + channel.nextShow.start.strftime("%H:%M") +  ") " + channel.nextShow.escaped_title, self.text_x, topHeight + self.text_y + 20)

					topHeight = topHeight + height + topBetween

	def on_draw_shape (self, ctx):
		self.on_draw(ctx)

	def load_xmltv (self):
		print 'Loading XMLTV file - ' + self.xmltv_file_path
		#Load XMLTV file
		self.xmltv_file_path = self.xmltv_file_path
		self.tvGuide = Xmltv(self.xmltv_file_path)
		self.tvGuide.DoLoad()

		#save channel list if the option is empty
		if len(self.xmltv_channels) == 0:
			self.save_channel_order()
		else:
			#change order to match the list in the options
			self.update_channel_orders()

		#resize the form to only be big enough for the number of channels
		numChannels = self.get_number_displayed_channels()
		self.width = int(self.width_one_channel * self.scale)
		if numChannels == 0:
			self.height = int(1 * (self.height_one_channel * self.scale))
		else:
			self.height = int(numChannels *(self.height_one_channel * self.scale))
					
		self.tvGuide.channels.sort()
		self.tvGuide.UpdateNowShows()
		self.tvGuide.UpdateNextShows()
		self.redraw_canvas()

		#Create sub menu
		self.create_channel_menu_list()

	def save_channel_order(self):
		#clear list
		self.xmltv_channels =[]

		#rebuild list
		for channel in self.tvGuide.channels:
			if channel.order >= 0:
				self.xmltv_channels.append(channel.id)

		#cause the options to be saved
		self.xmltv_channels = self.xmltv_channels
	
	def update_channel_orders(self):
		#hide all channels by default
		for channel in self.tvGuide.channels:
			channel.order = -1

		chanCount = 0
		for chanId in self.xmltv_channels:
			for channel in self.tvGuide.channels:
				if channel.id == chanId:
					channel.order = chanCount

			chanCount = chanCount + 1

	# timeout-function
	def update_listings (self):
		#resize the form to only be big enough for the number of channels
		numChannels = self.get_number_displayed_channels()
		self.width = int(self.width_one_channel * self.scale)
		if numChannels == 0:
			self.height = int(1 * (self.height_one_channel * self.scale))
		else:
			self.height = int(numChannels * (self.height_one_channel * self.scale))

		self.tvGuide.UpdateNowShows()
		self.tvGuide.UpdateNextShows()
		self.redraw_canvas()
		return True

	def draw_text(self, ctx, text, x, y):
		#truncate long text at 30 characters
		if (len(text) > 30):
			text = text[0:30] + "..."
		ctx.save()
		ctx.translate(x, y)
		if self.p_layout == None :
			self.p_layout = ctx.create_layout()
		else:
			ctx.update_layout(self.p_layout)
		p_fdesc = pango.FontDescription("Free Sans 25")
		p_fdesc.set_size(10 * pango.SCALE)
		self.p_layout.set_font_description(p_fdesc)
		self.p_layout.set_width((self.width) * pango.SCALE)
		self.p_layout.set_markup(str(text))
		ctx.set_source_rgba(1, 1, 1, 0.8)
		ctx.show_layout(self.p_layout)
		ctx.fill()
		ctx.restore()

	def get_channel_at_pixel(self, pixel_x, pixel_y):
		if len(self.tvGuide.channels) == 0:
			return self.tvGuide.noneChannel

		chanPicked = int(pixel_y / self.height_one_channel)

		for channel in self.tvGuide.channels:
			if channel.order == chanPicked:
				return channel
		
		return self.tvGuide.noneChannel

	def move_channel_up(self, channel):
		if channel == self.tvGuide.noneChannel:
			return

		#Do not move up if at the top
		if channel.order == 0:
			return

		chanOrder = channel.order
		channel.order = chanOrder - 1

		#switch with the channel that previously had this order
		for chan in self.tvGuide.channels:
			if chan.order == chanOrder - 1 and not chan.name == channel.name:
				chan.order = chanOrder

		#reload data
		self.tvGuide.channels.sort()
		self.update_listings()
		self.save_channel_order() 

	def move_channel_down(self, channel):
		if channel == self.tvGuide.noneChannel:
			return

		#Do not move down if at the bottom
		if channel.order == len(self.tvGuide.channels) - 1:
			return

		chanOrder = channel.order
		channel.order = chanOrder + 1

		#switch with the channel that previously had this order
		for chan in self.tvGuide.channels:
			if chan.order == chanOrder + 1 and not chan.name == channel.name:
				chan.order = chanOrder

		#reload data
		self.tvGuide.channels.sort()
		self.update_listings()
		self.save_channel_order()

	def hide_channel(self, channel):
		#set the order to be -1
		channel.order = -1
	
		#reload data
		self.tvGuide.channels.sort()
		self.update_listings()
		self.save_channel_order()

		#reset order ids
		self.update_channel_orders()

	def show_channel(self, channel):
		#set the order to be the highest order + 1
		chanOrder = 0
		for chan in self.tvGuide.channels:
			chanOrder = chan.order + 1

		channel.order = chanOrder
	
		#reload data
		self.tvGuide.channels.sort()
		self.update_listings()
		self.save_channel_order()

		#reset order ids
		self.update_channel_orders()

	def create_channel_menu_list(self):
		#Create Channels menu item if does not exist
		if self.chanmenu_item == None:
			self.chanmenu_item = gtk.MenuItem("Channels")
			self.chanmenu_item.show()
			self.menu.insert(self.chanmenu_item, 3)
		else:
			self.chanmenu_item.remove_submenu()

		chanmenu_menu = gtk.Menu()
		self.chanmenu_item.set_submenu(chanmenu_menu)

		#sort channels by name temporarily to create the menu
		self.tvGuide.channels.sort(self.compare_channel_name)
		
		# loop through all channels and add them to the list
		for channel in self.tvGuide.channels:
			item = gtk.CheckMenuItem(channel.name)
			if channel.order >= 0:
				item.set_active(True)
			else:
				item.set_active(False)
			item.connect("activate", self.menuitem_callback, 
				'channel:' + channel.id)
			item.show()

			chanmenu_menu.append(item)

		#change sorting back to use the order
		self.tvGuide.channels.sort()

	def compare_channel_name(self, this, other):
        	return cmp(this.name, other.name)

	def download_icon(self, channel):
		chanIconFilePath = self.get_screenlet_dir() + '/logos/' + channel.id + '.png'
		if os.path.exists(chanIconFilePath):
			return

		if channel.iconpath != None:
			print 'Logo needs to be downloaded for channel ' + channel.id + ' : URL is - ' + channel.iconpath
			if channel.iconpath[0:4] == 'http' and channel.iconpath[-4:] == '.png':
				logo_url = urlopen(channel.iconpath)
				logo_data = logo_url.read()
				fileObj = open(chanIconFilePath, "w")
				fileObj.write(logo_data)
				fileObj.close()
				print 'Download complete for URL ' + channel.iconpath
			else:
				print 'Error: Logo url does not start with http and/or does not end with .png'
		
	def get_number_displayed_channels(self):
		number_displayed = 0
		for channel in self.tvGuide.channels:
			if channel.order >= 0:
				number_displayed = number_displayed + 1

		if number_displayed > self.xmltv_num_channels:
			number_displayed = self.xmltv_num_channels

		return number_displayed

# If the program is run directly or passed as an argument to the python
# interpreter then create a Screenlet instance and show itThread.__init__(self)
if __name__ == "__main__":
	# create new session
	import screenlets.session
	screenlets.session.create_session(WhatsOnTVScreenlet)


