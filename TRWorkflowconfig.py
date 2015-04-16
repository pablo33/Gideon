#!/usr/bin/python3
''' Config file for torrent TRWorkflow
	This is a python file.
	'''

__version__ = 1.4
__date__ = "29/11/2014"
__author__ = "pablo33"


# Setting variables, default paths to store processed files.
Fmovie_Folder = "/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/pelis/" # Place to store processed movies
Faudio_Folder = "/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/Música/" # Place to store processed music
Fother_Folder = "/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/Others/" # Place to store other processed downloads (This folder is also used as tmp folder to store avidemux pull files)
Torrentinbox = "/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/Downloads/" # Place to get covers from. It is a repository of covers from wich the videofile finds and gets a cover. (Usually The same folther that transmission puts torrents in)
Dropboxfolder = "/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/TRinbox/" # (input folder) Place to get new .torrents and .covers. (this files will be moved to Torrentinbox folder) Note that you should install Dropboxbox service if you want deposit files there.

# Chapter identifier, this prevents deleting in case it is found
chapteridentifier = ('Cap', 'cap', 'episodio')

# How to tipify items
ext = {
	"movie":['mkv','avi', 'mpg', 'mpeg', 'wmv', 'bin', 'rm', 'divx', 'ogm', 'vob', 'asf', 'mkv','m2v', 'm2p', 'mp4', 'viv', 'nuv', 'mov', 'iso', 'nsv', 'ogg', 'ts', 'flv'],
	"audio":['mp3', 'ogg', 'wav', 'm4a', 'wma', 'aac', 'flac', 'mka', 'ac3'],
	"compressed":['rar','zip', '7z'],
	"notwanted":['txt','url','lnk','DS_Store'],
}
# List of prohibited words. This words will be deleted from files and folder-names
prohibited_words = ['zonatorrent','lokotorrents','com','Spanish','www','MP3','HDTV','XviD','DVDRip','LeoParis',
	'Widescreen','DVD9.','.FULL.','PAL','Eng.','Ger.','Spa.','Ita.',
	'Fra.','Multisubs','720p','DVD','AC3','  ','..','__','()','[]'
	]

# Send codec info for downloaded videos. Set to "always","alert", or "never" 
send_info_mail = "never"

# You can get alerts due to some video information, see video info in log folder.
alert_values = {'ID_VIDEO_FORMAT':'H264',
	}

# Recipients to send info: you can add as many as you want, write them into one string and separated by spaces.
mail_recipients = 'pablolabora@gmx.es'

# The logging level, can be: "DEBUG","INFO","WARNING","ERROR","CRITICAL"
loginlevel = "DEBUG"
# Maximum of log files. 1 - 9999, but please half a hundred should be enough
maxlogfiles = 15
# Logging folder:
logging_folder="/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/logs/"

# Seconds to wait until hot folders are scanned for new items.
s = 30

# Command line to start Transmission
cmd  = "/usr/bin/transmission-gtk -m &"

# list of hot folders to scan for active or new torrents (if any .torren or .part is detected, transmission will be launched)
lsdy = ['/home/pablo/Dropbox/Misdocs/python/TRWorkflow V2/Downloads']


# Shut down the system when avi's pull has finished (1 = shutdown , otherwise system will remain up)
shdown = 0

