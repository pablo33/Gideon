''' Config file of torrent TRWorkflow
	'''

__version__ = 2.0
__date__ = "12/07/2016"
__author__ = "pablo33"


# Setting variables, default paths to store processed files.
Fmovie_Folder = "/home/user/movies/" # Place to store processed movies
Faudio_Folder = "/home/user/audio/" # Place to store processed music
Hotfolder = "/home/user/Dropbox/TRinbox/" # (input folder) Place to get new .torrents and .jpg .png covers. (this files will be moved to Torrentinbox folder) Note that you should install Dropboxbox service if you want deposit files there.



# mail config (this example is for a gmx account, with SSL autentication)
mailmachine = 'mail.gmx.com'		# your server machine
mailsender = 'youremail@here.com'	# your sender email account
mailpassw = 'yourPa$$wordhere'		# your email password.

# Notifications config:
# Recipients to send info: you can add as many as you want and assign different topics to e-mail them,
# you can write more than one e-mail recipient into one string by separating them by colons (:)
# Asociate msg topics here by number. (note that only topics marked OK will are enabled)

mail_topic_recipients = {
	'adminemail@gmx.es' 		: set(range (1,11)),
	'user1@email.com' : set([7,]),
	'user2@email.com' : set([6,7,10,]),	
	}

#Msgtopics:
#OK	1 : 'Added incoming torrent to process',
#	2 : 'Torrent has been added to Transmission for downloading',
#	3 : 'Torrent has been manually added',
#	4 : 'Torrent has been manually deleted',
#	5 : 'Torrent is completed',
#OK	6 : 'List of files has been retrieved and preasigned',
#OK	7 : 'Files have been processed and copied into destination',
#	8 : 'No Case was found for this Torrent',
#OK	9 : 'Transmission has been launched',
#OK	10:	'Torrent Deleted due to a retention Policy',

# The logging level, can be: "DEBUG","INFO","WARNING","ERROR","CRITICAL"
loginlevel = "INFO"

# Retention Policy: None (deactivated) / max days after a torrent is completted. (it will also deleted if the torrent finished its seeding ratio)
MaxseedingDays = None
#MaxseedingDays = 30

# Seconds to wait until hot folders are scanned for new items.
s = 60

# Command line to start Transmission
cmd  = "/usr/bin/transmission-gtk -m &"
TRmachine = 'localhost'
TRuser = 'yourconfigureduser'
TRpassword = 'yourconfiguredpassword'


# Chapter identifier, this prevents deleting in case it is found even it they are into braces "[ ]"
chapteridentifier = ('Cap', 'cap', 'episodio') 

# How to typify items
ext = {
	"video":['mkv','avi', 'mpg', 'mpeg', 'wmv', 'bin', 'rm', 'divx', 'ogm', 'vob', 'asf', 'mkv','m2v', 'm2p', 'mp4', 'viv', 'nuv', 'mov', 'iso', 'nsv', 'ogg', 'ts', 'flv'],
	"audio":['mp3', 'ogg', 'wav', 'm4a', 'wma', 'aac', 'flac', 'mka', 'ac3'],
	"compressed":['rar','zip', '7z'],
	"notwanted":['txt','url','lnk','DS_Store', 'nfo', 'info'],
	"image":['jpg','png','gif'],
}

# List of prohibited words. This words will be deleted from files and folder-names
prohibited_words = ['zonatorrent','lokotorrents','com','Spanish','English','www','mp3','HDTV','DVDRip','rip','Xvid','bluray','microhd','LeoParis',
	'Widescreen','DVD9.','dvd9','dvdr','.FULL.','PAL','Eng.','Ger.','Spa.','Ita.','Fra.','Multisubs','x264',
	'720p','1080p','DVD','AC3','  ', 'Divxtotal','Com','..','__','--','()','[]'
	]