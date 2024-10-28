--------------------------------------------------------------------------------
  WhatsOnTV v0.2 - (c) by JamesL 2007
--------------------------------------------------------------------------------

This software is released under the GNU Public License v3. You are free
to modify and copy this software unless you don't keep the above coypright 
notice or pretend this to be your work. The author gives you NO 
warranties at all.

WhatsOnTV is a screenlet to display data from XMLTV listings. You need to supply 
your own XMLTV file and channel logos (optional).


Installation:
-------------
Place WhatsOnTV screenlet folder in your ~/.screenlets/ folder.

Place channel logos within the ~/screenlets/WhatsOnTV/logos folder.
Each logo must have the file name <channel-id>.png.

<channel-id> is the channel id specified in the xmltv file under the <Channel> element

If your XMLTV file contains Internet icon src locations for your channels you can use
the right click option "Download Channel Logos" to automatically download the logos to
your Logos folder. This feature only works for URLS that start with http and end with .png


Change Log:
-----------

Version 0.2
+ Created an icon
+ Changed the channel list in the options to be hidden. This list is programmatically handled and should not be edited manually
+ Start times are displayed for the Now and Next show. Format of time is HH:MM in 24 hour time.
+ Icons automatically resized
+ Icons can be downloaded from the Internet if a url is provided in the XMLTV file and no logo exists locally
+ Fixed bug with start and stop datetimes to ignore the timezone part (eg +1000)
+ Fixed bug so that when changing the XMLTV file location the channel list is cleared to be rebuilt
+ Fixed bug so that form automatically resizes depending on how many channels are available
+ Increased maximum number of channels on screen to 20
