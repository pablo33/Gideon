#!/usr/bin/python3
''' Config file for torrent TRWorkflow
	This is a python file.
	'''

__version__ = 1.4
__date__ = "29/11/2014"
__author__ = "pablo33"


# Setting variables, default paths to store processed files.
Fmovie_Folder = "/home/user/movies/" # Place to store processed movies
Faudio_Folder = "/home/user/audio/" # Place to store processed music
Fother_Folder = "/home/user/Downloads/" # Place to store other processed downloads (This folder is also used as tmp folder to store avidemux pull files)
Hotfolder = "/home/user/Dropbox/TRinbox/" # (input folder) Place to get new .torrents and .covers. (this files will be moved to Torrentinbox folder) Note that you should install Dropboxbox service if you want deposit files there.

# Chapter identifier, this prevents deleting in case it is found even it they are into braces "[ ]"
chapteridentifier = ('Cap', 'cap', 'episodio') 

# How to tipify items
ext = {
	"video":['mkv','avi', 'mpg', 'mpeg', 'wmv', 'bin', 'rm', 'divx', 'ogm', 'vob', 'asf', 'mkv','m2v', 'm2p', 'mp4', 'viv', 'nuv', 'mov', 'iso', 'nsv', 'ogg', 'ts', 'flv'],
	"audio":['mp3', 'ogg', 'wav', 'm4a', 'wma', 'aac', 'flac', 'mka', 'ac3'],
	"compressed":['rar','zip', '7z'],
	"notwanted":['txt','url','lnk','DS_Store'],
	"image":['jpg','png','gif'],
}
# List of prohibited words. This words will be deleted from files and folder-names
prohibited_words = ['zonatorrent','lokotorrents','com','Spanish','English','www','MP3','HDTV','XviD','DVDRip','LeoParis',
	'Widescreen','DVD9.','.FULL.','PAL','Eng.','Ger.','Spa.','Ita.',
	'Fra.','Multisubs','720p','DVD','AC3','  ','..','__','()','[]'
	]

# Send codec info for downloaded videos. Set to "always","alert", or "never" 
send_info_mail = "never"

# You can get alerts due to some video information, see video info in log folder.
alert_values = {'ID_VIDEO_FORMAT':'H264',
	}

# mail config (this example is for a gmx account, with SSL autentication)
mailmachine = 'mail.gmx.com'		# your server machine
mailsender = 'youremail@here.com'	# your sender email account
mailpassw = 'yourPa$$wordhere'		# your email password.
mail_recipients = 'recipientsemail@here.com'	# Recipients to send info: you can add as many as you want, write them into one string and separated by colons (:). 

# Transmission norifications
TR_DW_DIRECTORY="/your/full/path/to/transmission/download/dir" # Path where transmission stores downloaded files.
TR_MAILTO="peopleto@here.com" # one or more recipients in "To" separated by semi colons (;)
TR_MAILTOCC="peopletocc@here.com" # one or more recipients in "CC" separated by semi colons (;)

# The logging level, can be: "DEBUG","INFO","WARNING","ERROR","CRITICAL"
loginlevel = "DEBUG"

# Seconds to wait until hot folders are scanned for new items.
s = 600

# Command line to start Transmission
cmd  = "/usr/bin/transmission-gtk -m &"

# list of hot folders to scan for active or new torrents (if any .torren or .part is detected, transmission will be launched)
lsdy = ['/home/user/transmission','/home/user/transmission.tmp']


# Shut down the system when avi's pull has finished (1 = shutdown , otherwise system will remain up)
shdown = 0
