#!/usr/bin/python3
# -*- encoding: utf-8 -*-

__version__ = "1.0"
__author__  = "pablo33"


''' This program is intended to process torrents.
	
	Program main functions:

	Checks contents of a folder to send this files to transmission,
	Checks contents of torrents added to transmission (everithing),
	Make a copy and store downloaded files due to its nature and contents at pre configured folder/s.
	Renames filenames clening them (Useful for HTPC storages).
	It can find and select the most suitable poster from a folder and match to its videofile, so Freevo/kodi can read it as its cover/poster.
	It can detect chapter-numbers at the end of the file/s, rename then as nxnn so Freevo/kodi can detect them as videofiles of a chapter-series.
	It can send e-mails to notify some events. You'l need to config your mail account.
	It deletes copied and processed torrents, so you'll forget about delete them manually from Transmission.
	It checks empty space at Transmission download filesystem and perform a delete trash, torrents, to free disk space.

	Logs are stored in a single Gideon.log file.

	You need to set up GideonConfig.py first to run this program for the first time.

	Notes about rar file support:
	For rar support you need to install or copy rarfile.py into the same foder as Gideon.py
	rarfile is a Python module for Rar archive reading. Licensed under ISC license.
	Copyright (c) 2005-2016 Marko Kreen <markokr@gmail.com>
	https://github.com/markokr/rarfile

	Note about trasnmissionrpc:
	This module helps using Python to connect to a Transmission JSON-RPC service.
	transmissionrpc is compatible with Transmission 1.31 and later.
	transmissionrpc is licensed under the MIT licenseself.
	https://pythonhosted.org/transmissionrpc/

	'''

# Standard library module import
import os, sys, shutil, logging, datetime, time, smtplib, re
from collections import namedtuple
from email.mime.text import MIMEText  # for e-mail compose support
from subprocess import check_output  # Checks if transmission is active or not
import sqlite3  # for sqlite3 Database management

# Specific library module import
import transmissionrpc  # transmission rpc API
dyntestfolder = 'TESTS'  # local path for Deftests

# importing rarfile utility rarinit()
try:
	import rarfile
except:
	print ('Rarfile library is not present. Gideon will not process Rar files.')
	RarSupport = False
else:
	#if rarfile.UNRAR_TOOL == False:
	if os.system('unrar') != 0:
		print ('No unrar tool is found. Gideon will not process Rar files.')
		print ('You can install it by typing $sudo apt-get install unrar.')
		RarSupport = False
	else:
		print ('RarSupport is active.')
		RarSupport = True



# ===================================
# 				UTILS		
# ===================================
# 				(General util functions)

# errors
class OutOfRangeError(ValueError):
	pass
class NotIntegerError(ValueError):
	pass
class NotStringError(ValueError):
	pass
class MalformedPathError(ValueError):
	pass
class EmptyStringError(ValueError):
	pass


def addslash (text):
	''' Returns an ending slash in a path if it doesn't have one '''
	if type(text) is not str:
		raise NotStringError ('Bad input, it must be a string')
	if text == "":
		return text
	if text [-1] != '/':
		text += '/'
	return text

def itemcheck(pointer):
	''' returns what kind of a pointer is 
		DefTest >> OK'''
	if type(pointer) is not str:
		raise NotStringError ('Bad input, it must be a string')
	if pointer.find("//") != -1 :
		raise MalformedPathError ('Malformed Path, it has double slashes')
	
	if os.path.isfile(pointer):
		return 'file'
	if os.path.isdir(pointer):
		return 'folder'
	if os.path.islink(pointer):
		return 'link'
	return ""

def makepaths (fdlist):
	for fditem in fdlist:
		itemisa = itemcheck (fditem)
		if itemisa == 'file':
			os.remove(fditem)
			os.makedirs(fditem)
		if itemisa == '':
			os.makedirs(fditem)
	return

def nextfilenumber (dest):
	''' Returns the next filename counter as filename(nnn).ext
	input: /path/to/filename.ext
	output: /path/to/filename(n).ext
		DefTest >> OK '''
	if dest == "":
		raise EmptyStringError ('empty strings as input are not allowed')
	filename = os.path.basename (dest)
	extension = os.path.splitext (dest)[1]
	# extract secuence
	expr = '\(\d{1,}\)'+extension
	mo = re.search (expr, filename)
	try:
		grupo = mo.group()
	except:
		#  print ("No final counter expression was found in %s. Counter is set to 0" % dest)
		counter = 0
		cut = len (extension)
	else:
		#  print ("Filename has a final counter expression.  (n).extension ")
		cut = len (mo.group())
		countergroup = (re.search ('\d{1,}', grupo))
		counter = int (countergroup.group()) + 1
	if cut == 0 :
		newfilename = os.path.join( os.path.dirname(dest), filename + "(" + str(counter) + ")" + extension)
	else:
		newfilename = os.path.join( os.path.dirname(dest), filename [0:-cut] + "(" + str(counter) + ")" + extension)
	return newfilename

def startDefaultFile (Stringfile,filepath):
	''' Dumps a string variable into a TXT file.'''
	if itemcheck(filepath) == "":
		logging.warning("%s file does not exist, setting up for the first time"%filepath)
		f = open(filepath,"a")
		f.write(Stringfile)
		f.close()
		return True
	return False

def fileinuse (entry):
	''' returns False if file is not beign used (opened), or
		returns True if file is beign used. 
		'''
	try:
		pids = check_output(["lsof", '-t', entry ])
	except:
		return False
	logging.debug('%s is beign accesed'%(entry))
	return True

def lsdirectorytree(directory = (os.getenv('HOME'))):
	""" Returns a list of a directory and its child directories
	usage:
	lsdirectorytree ("start directory")
	By default, user's home directory"""
	#init list to start
	dirlist = [directory]
	#setting the first scan
	moredirectories = dirlist
	while len (moredirectories) != 0:
		newdirectories = moredirectories
		#reset flag to 0; we assume from start, that there aren't child directories
		moredirectories = []
		# print ('\n\n\n','new iteration', moredirectories)
		for a in newdirectories:
			# checking for items (child directories)
			# print ('Checking directory', a)
			anadir = addchilddirectory (a)
			#adding found items to moredirectories
			for b in anadir:
				moredirectories.append (b)
		#adding found items to dirlist
		for a in moredirectories:
			dirlist.append (a)
	return dirlist

def addchilddirectory (directoriy):
	""" Returns a list of child directories
	Usage: addchilddirectory(directory with absolute path)"""
	paraanadir = []
	ficheros = os.listdir (directoriy)
	for a in ficheros:
		item = directoriy+'/'+a
		if os.path.isdir(item):
			paraanadir.append (item)
	return paraanadir

def folderinuse (folder):
	""" Scans a folder for files.
			Returns True if any file is in use (is being writted)
			Otherwise returns False
		(DefTest in TestPack3)
		"""
	tmpset=set()
	contents1=None
	for loop in [1,2]:
		folderlist = lsdirectorytree (folder)
		for i in folderlist:
			tmpset.add(i)
		for a in folderlist:
			filelist = [os.path.join(folder,i) for i in os.listdir(a)]
			for entry in filelist:
				if os.path.isfile (entry):
					tmpset.add (entry)
					if fileinuse (entry):
						return True
		if contents1 == None:
			contents1 = tmpset.copy()
			tmpset = set()
			time.sleep (8)
			continue
		elif contents1 != tmpset:
			return True
	return False

def toHumanSizeReadable (size, units = ''):
	''' this function gets an integer representing bytes and returns a
		human friendly readable text Kb, Mb, Gb, Tb

		You can force the output by explicity introducing a units argument
		or leave the code guess the better fit.
		'''
	if type(size) != int:
		raise NotIntegerError(str(size) + 'is not an integer')

	sep = " "

	if size < 1000 or units.upper() == 'B':
		hsr = str(size)+sep+'bytes'

	elif size < 900000 or units.upper() == 'KB':
		hsr = "%.0f"%(size/1000)+sep+'Kb'

	elif size < 900000000 or units.upper() == 'MB':
		hsr = "%.1f"%(size/1000000)+sep+'Mb'

	else:
		hsr = "%.1f"%(size/1000000000)+sep+'Gb'

	return hsr

LogOnceDict = {'RPSF':set(), 'RPMT':set(), 'RPNMC':set(), 'RILS':set(), 'CSVC':set(), 'DRARJob':set(), 'RFNP':set() }
def LogOnce (field, ID, msg='', action = 'log'):
	''' This function enables the log or print only one time, the same repetitive event, it is driven by an unique ID and field.
		a global var must to be defined with the fiels that you want to control.
		usage:
			field: must be one of the defined events at LogOnceDict.
			ID:    given an event, is the unique identifier for the item.
			msg:   is the customizable msg for the logging or the print outtput.
			action:is the action, should be 'log', 'print' or 'reset'.
		'''
	action = action.upper()
	actionstatus = False

	if type(field) != list:
		field = [field,]

	for fd in field:
		if fd not in LogOnceDict:
			logging.warning ('field %s is not part of the logging once messages'%fd)
			continue
		elif action not in ['RESET', 'LOG', 'PRINT']:
			logging.warning ('%s is not a valid action for logging once messages'%fd)
			continue

		actual = LogOnceDict[fd]
		if action == 'RESET':
			actual.discard(ID)

		elif action in ('LOG', 'PRINT'):
			if not ID in actual:
				logging.info (msg)
				if action == 'PRINT':
					print (msg)
				actual.add(ID)
				actionstatus = True

		LogOnceDict[fd] = actual
	return actionstatus


# .. Default Videodest.ini file definition (in case there isn't one)
startVideodestINIfile = """
# Put this file into the defined inbox folder for ,torrent files  ("TransmissionInbox" (at GideonConfig.py))
#	
#	define a destination with some words to automatically store file-movies to the right place.
#	
#	Those paths are relative to "Videodest" default path (defined in Fmovie_Folder var (at GideonConfig.py))
#	

__version__ = 1.1
__date__ = "03/11/2017"

# You can define alias for common destinations, to substitute text 
alias=terror        ,		/terror movies/
alias=anime			,		/anime movies/

# Define destinations:
#	guess a title to match the filemovie then,
#   define a relative path to store it (starting at default "filemovie folder" defined in GideonConfig.py file) 
#	(you can use alias enclosed in <....> to replace text, but remember that you must define them first)
#  Those are examples, please replace them and follow the structure.
#  Please, do not include comments at the end of alias or dest lines. This is not an python file.
#  
dest = the addams family, <terror>
dest = ghost in the shell, <anime>future
dest = star wars, /saga starwars/

# EOF
"""


# .. Default GideonConfig(generic).py file definition (in case there isn't one)
DefaultConfigFile = """
''' Config file of Gideon
	'''

__version__ = 2.1
__date__ = "04/11/2017"
__author__ = "pablo33"


# Setting variables, default paths to store processed files.
Fmovie_Folder = "/home/user/Videos/movies/"  # Place to store processed movies
Fseries_Folder = "/home/user/Videos/series/"  # Place to store processed movies
Faudio_Folder = "/home/user/Music/"  # Place to store processed music
Fbooks_Folder = "/home/user/Calibre_inbox/"  # Place to store processed e-books
Fcomic_Folder = "/home/user/Documents/Comix/"  # Place to store processed Comics
TelegramNoCasedest = "/home/user/Downloads/"  # Destination file where telegram files goes if no Case is found.

# Incomming folders, default paths to fetch files from
TransmissionInbox = "/home/user/Dropbox/TRinbox/"  # (input folder) Place to get new .torrents and .jpg .png covers/posters. (this files will be moved to Torrentinbox folder).
Telegraminbox = None  #  "/home/user/Downloads/Telegram/"  # (input folder) Place to get new files and folders to process. Use this if you want to Gideon to process an incoming file.

# mail config (this example is for a gmx account, with SSL autentication)
mailmachine = 'mail.gmx.com'		# your mail service machine
mailsender = 'your_email@here.com'	# your sender email account
mailpassw = 'yourPa$$wordhere'		# your email password.

# Notifications config:
# Recipients to send info: you can add as many recipients as you want and assign different topics to e-mail them,
# you can write more than one e-mail recipient into one string by separating them by colons (:)
# Asociate msg topics by a code-number. (note that only topics marked OK are enabled)

mail_topic_recipients = {
	'adminemail@gmx.es' 		: set(range (1,100)),
	'user1@email.com' 			: set([7,]),
	'user2@email.com' 			: set([6,7,10,]),	
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
#	11:	'Cover assigned to a moviefile',
#	12: 'System is running into low disk space'
#OK	13: 'Error adding a Torrent file to Transmission Service'


# The logging level, can be: "DEBUG","INFO","WARNING","ERROR","CRITICAL"
loginlevel = "INFO"

# Retention Policy (only aplicable to transmission) : None (deactivated) / max days after a torrent is completed. (it will also deleted if the torrent finished its seeding ratio)
MaxseedingDays = None
#MaxseedingDays = 30
# Minimum free space in bytes at torrent Download drive. Can be 0 or a number of bytes
# Gideon will remove delivered torrents if system is going low on space.
MinSpaceAtTorrentDWfolder = None
#MinSpaceAtTorrentDWfolder = 20000000000  # is 20Gb

# Seconds for Gideon sleep-cycle.
s = 60

# Command line to start Transmission and how to connect to transmissionrpc Service.
cmd  = "/usr/bin/transmission-gtk -m &"
TRmachine = 'localhost'
TRuser = 'yourconfigureduser'
TRpassword = 'yourconfiguredpassword'


# Chapter and season wording identification 
chapteridentifier = ('Cap', 'episodio', 'Chapter', 'Capítulo', 'capitulo', 'Chap')
seasonidentifer = ('Temporada', 'Season', 'Temp')

# How to typify items
ext = {
	"video":['mkv','avi', 'mpg', 'mpeg', 'wmv', 'rm', 'divx', 'ogm', 'vob', 'asf', 'mkv','m2v', 'm2p', 'mp4', 'viv', 'nuv', 'mov', 'iso', 'nsv', 'ogg', 'ts', 'flv'],
	"audio":['mp3', 'ogg', 'wav', 'm4a', 'wma', 'aac', 'flac', 'mka', 'ac3'],
	"ebook":['mobi','epub','azw3'],
	"comic":['cbr','cbz','pdf'],
	"compressed":['rar','zip', '7z'],
	"notwanted":['txt','url','lnk','DS_Store', 'nfo', 'info'],
	"image":['jpg','png','gif','jpeg'],
}

# List of prohibited words. This words will be deleted from files and folder-names
prohibited_words = ['zonatorrent','lokotorrents','com','Spanish','English','www','mp3','HDTV','DVDRip','rip','Xvid','bluray','microhd','LeoParis',
	'Widescreen','DVD9.','dvd9','dvdr','.FULL.','PAL','Eng.','Ger.','Spa.','Ita.','Fra.','Multisubs','x264',
	'720p','1080p','DVD','AC3','  ', 'Divxtotal','Com','..','__','--','()','[]',
	'mkv','Web-DL','Mpeg','m4v','mp4','avi','web','qt','flv','asf','wmv','mov','dl'
	]

"""


# ===================================
# 			== Setting up ==
# ===================================

# (1) LOG MODULE ........ (Configurying the logging module)
# ---------------------------------------------------------

# (1.1) Getting current date and time
now = datetime.datetime.now()
today = "/".join([str(now.day),str(now.month),str(now.year)])
tohour = ":".join([str(now.hour),str(now.minute)])

# (1.2) Getting user folder to place log files, generating paths....

userpath = os.path.join(os.getenv('HOME'),".Gideon")
userconfig = os.path.join(userpath,"GideonConfig.py")
usertrash = os.path.join(os.getenv('HOME'),'.local/share/Trash/files')
Torrentinbox = os.path.join(userpath,"Torrentinbox")  # Place to manage incoming torrents files
Availablecoversfd = os.path.join(userpath,"Covers")  # Place to store available covers
if __name__ == '__main__':
	dbpath = os.path.join(userpath,"DB.sqlite3")
else:
	dbpath = os.path.join(dyntestfolder, "DB.sqlite3")

logpath = userpath
logging_file = os.path.join(logpath,"GideonLogFile.log")

makepaths ([userpath, logpath, Torrentinbox, Availablecoversfd])


# (1.3) loading user preferences
if itemcheck (userconfig) == "file":
	print ("Loading user configuration....")
	sys.path.append(userpath)
	# Import user config file
	import GideonConfig
else:
	# initilizing user's default config file.
	print ("There isn't an user config file: " + userconfig)
	startDefaultFile (DefaultConfigFile, userconfig)
	print ("An user config file has been created: " + userconfig)
	print ("Please customize by yourself before run this software again")
	print ("This software is going to try to open with a text editor.")
	os.system ("gedit "+userconfig)
	exit()

print ("Loginlevel:", GideonConfig.loginlevel)
logging.basicConfig(
    level=GideonConfig.loginlevel,
    format='%(asctime)s : %(levelname)s : %(message)s',
    filename = logging_file,
    filemode = 'a', # uncomment this to overwrite log file.
)
print ("logging to:", logging_file)

# (1.4) Starting log file
logging.info("======================================================")
logging.info("================ Starting a new sesion ===============")
logging.info("======================================================")


# (1.5) Setting main variables
Fmovie_Folder = addslash(GideonConfig.Fmovie_Folder)  # Default place to store movies
Fseries_Folder = addslash(GideonConfig.Fseries_Folder)  # Default place to store series
Faudio_Folder = addslash(GideonConfig.Faudio_Folder)  # Default place to store music
Fbooks_Folder = addslash(GideonConfig.Fbooks_Folder)  # Default place to store books
Fcomic_Folder = addslash(GideonConfig.Fcomic_Folder)  # Default place to store Comics
TelegramNoCasedest = addslash (GideonConfig.TelegramNoCasedest)  # Telegram files with no Case goes here, preserving the file/folder structure

TransmissionInbox = addslash (GideonConfig.TransmissionInbox)  # Hotfolder to retrieve user incoming files, usually a sycronized Dropbox folder
Telegraminbox = addslash (GideonConfig.Telegraminbox)  # Hotfolder to retrieve Telegram Downloaded files or whatever other files

s =  GideonConfig.s # Time to sleep between checks (Dropbox folder / transmission spool)
cmd  = GideonConfig.cmd # Command line to lauch transmission
lsdy = GideonConfig.lsdy # List of hot folders to scan for active or new file-torrents
TRmachine = GideonConfig.TRmachine
TRuser = GideonConfig.TRuser
TRpassword = GideonConfig.TRpassword
MaxseedingDays = GideonConfig.MaxseedingDays
MinSpaceAtTorrentDWfolder = GideonConfig.MinSpaceAtTorrentDWfolder
mail_topic_recipients = GideonConfig.mail_topic_recipients

chapteridentifier = GideonConfig.chapteridentifier
seasonidentifer = GideonConfig.seasonidentifer


minmatch = 15  # Points to match files and cover/posters names, the more points the more strict must be a match
players = ['mplayer','vlc']

Msgtopics = {
	1 : 'Added incoming torrent to process',
	2 : 'Torrent has been added to Transmission for downloading',
	3 : 'Torrent has been manually added',
	4 : 'Torrent has been manually deleted',
	5 : 'Torrent is completed',
	6 : 'List of files has been retrieved and preasigned',
	7 : 'Files have been processed and copied into destination',
	8 : 'No Case was found for this Torrent',
	9 : 'Transmission has been launched',
	10:	'Torrent Deleted due to a retention Policy',
	11:	'Cover assigned to a moviefile',
	12: 'System is running under low disk space',
	13: 'Error by adding a Torrent file to Transmission Service',
	}


# (1.6) Prequisites:
#=============
if not itemcheck(usertrash) == 'folder':
	usertrash = False

if itemcheck (TransmissionInbox) != 'folder' :
	print ('\tHotfolder does not exist: %s'%TransmissionInbox)
	print ('\tIf you want to use this inbox service,')
	print ('\tplease edit your user configuration file at: \n',  userconfig)
	print ('\tor create this configured path to start using it.')
	TransmissionInbox = None  # This prevent using this Service.

if itemcheck (Telegraminbox) != 'folder' :
	print ('\Telegraminbox does not exist: %s'%TransmissionInbox)
	print ('\tIf you want to use this inbox service,')
	print ('\tplease edit your user configuration file at: \n',  userconfig)
	print ('\tor create this configured path to start using it.')
	Telegraminbox = None  # This prevent using this Service.

elif Telegraminbox == TelegramNoCasedest:
	print ("You can't assign the same Telegram folder as input/output")
	print ('\tplease edit your user configuration file at: \n',  userconfig)
	Telegraminbox = None  # This prevent using this Service.


# Checking and setting up Fvideodest file:
if TransmissionInbox != None:
	if startDefaultFile (startVideodestINIfile, TransmissionInbox + "Videodest.ini") == True:
		print ("Don't forget to customize Videodest.ini file with video-destinations to automatically store them into the right place. More instructions are available inside Videodest.ini file.")



# (1.7) Checking DB or creating it:
#=============

if itemcheck (dbpath) == "file":
	logging.info ('Database found at %s'%(dbpath))
else:
	logging.info ('Database not found, creating an empty one.')
	con = sqlite3.connect (dbpath) # it creates one if it doesn't exists
	cursor = con.cursor() # object to manage queries

	# 0.1) Setup DB
	cursor.execute ("CREATE TABLE tw_inputs (\
		id INTEGER PRIMARY KEY AUTOINCREMENT,\
		hashstring char,\
		fullfilepath char NOT NULL ,\
		filetype char,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d','now')),\
		status char NOT NULL DEFAULT('Ready'),\
		deliverstatus char,\
		filesretrieved integer DEFAULT (NULL),\
		trname char, \
		dwfolder char \
		)")
	cursor.execute ("CREATE TABLE msg_inputs (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),\
		trid int,\
		status char NOT NULL DEFAULT('Ready'),\
		topic int NOT NULL\
		)")
	cursor.execute ("CREATE TABLE files (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),\
		trid int NOT NULL,\
		status char NOT NULL DEFAULT('Added'),\
		wanted boolean DEFAULT (1),\
		size number ,\
		mime char ,\
		originalfile char,\
		destfile char \
		)")
	cursor.execute ("CREATE TABLE pattern (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		trid int NOT NULL,\
		status char NOT NULL DEFAULT('Added'),\
		caso int ,\
		psecuence char,\
		nfiles int ,\
		nvideos int ,\
		nseries int ,\
		naudios int ,\
		nnotwanted int ,\
		ncompressed int ,\
		nimagefiles int ,\
		nother int ,\
		nbooks int ,\
		ncomics int ,\
		nfolders int ,\
		folderlevels int \
		)")

	con.commit()
	con.close()


# ===================================
# 				Not used		
# ===================================


def MailMovieInfo(moviefile,mail):
	""" e-mails info movie to a mail.

		input: filemovie, recipient e-mail
		output: 
		"""
	global GideonConfig
	
	send = 0 # We put send flag > off
	mydict, info_file = Extractcmovieinfo(moviefile)
	# we add a Megapixel parameter
	mydict ['MP'] = int(mydict ['ID_VIDEO_WIDTH']) * int(mydict ['ID_VIDEO_HEIGHT']) / 1000000
	alerts = set (a for a in GideonConfig.alert_values)
	data = set (a for a in mydict)
	union = alerts & data
	if len (union) > 0:
		f = open (info_file,"a")
		f.write("===========  ALERTS ===========\n\n")
		for a in union:
			if mydict[a] == GideonConfig.alert_values[a]:
				f.write(a+"="+mydict[a]+"\n")
				send = 1
		f.write('MP='+str(mydict['MP'])+'\n')
		f.write("\n")
		f.close()
	# checking Exceptions 
	if send == 1 and mydict ['MP'] < 0.3 : # Videos less than 0.3Mp do not have any problems on my machine. They do not need to be recompressed.
		send = 0

	# Sending alerts
	if send == 1 or GideonConfig.send_info_mail == "always":
		logging.debug("Sending alert mail")
		emailme ( GideonConfig.mailsender, 'Alert notification in %s' %(os.path.basename(moviefile)), mail, info_file)
	return send

def Extractcmovieinfo(filename):
	""" Extracts video information, stores it into a Name_of_the_movie.ext.info in logging folder.
		read parameters, returns it.

		input:  ./path/to/video/filename.avi
		output: {"dyctionary of atributes" : "Vaules"} , "info_file dumped"
		"""
	global logpath
	# Setting folder to store information
	info_file = addslash(logpath,"logging folder")+os.path.basename(filename+".info")
	logging.debug("Storing movie information at:"+ info_file)
	# We use mplayer to obtain movie information, be sure you have it istalled in your system.
	os.system("mplayer -vo null -ao null -identify -frames 0 '"+filename+"' > '"+info_file+"'")
	mydict = readparameters(info_file,"=")
	return mydict, info_file


# ========================================
# ===  Def Definition ====================
# ========================================

# Readini Functions ----------------------

def strip(string):
	""" input a string, and this script will trim start and end spaces and/or tabs.
		"""
	while True:
		go = 1
		if len (string) > 0:
			if string[0] == " " or string[-1] == " ":
				string = string.strip()
				go = 0
				continue
			if string[0] == "\t":
				string = string [1:]
				go = 0
				continue
			if string[-1] == "\t":
				string = string [:-1]
				go = 0
				continue
		if go == 1:
			break
	return string

def split(line,var):
	""" Split a string at first $var encountered

		If not any found, returs line, ''
		"""
	lt1, lt2  = line, ""
	at = line.find(var)
	if at != -1:
		lt1 = line [:at]
		lt2 = line[at+1:]
	return lt1, lt2

def readdict(inifile,var,sep):
	""" This function reads lines from an .ini file and gets parameters 
		to 	return a dictionary

		to read an ini-file like that:
			alias=word1,result1
			alias=word2,result2

		you should call this function as:
			readdict("/pathtofile/file.ini","alias",",")

	input:
		file (path)
		var to read
		sep identifier
	output:
		a dictionary
		"""	
	mydict = {'':''}
	with open(inifile,"r") as f:
		for line in f:
			a,b = split(line[:-1],"=")
			if strip(a) == var:
				#logging.debug("Found "+var+" definition line")
				#logging.debug("Splitting: "+line[:-1])
				lt1, lt2 = split(b,sep)				
				#Clean empty starting and end spaces
				lt1, lt2 = strip(lt1), strip(lt2)
				#adding to dict
				mydict [lt1] = lt2
	# cleaning empty entry
	mydict.pop("",None)
	return mydict

def readparameters(inifile,param="="):
	"""This function reads parameters from a .ini and returns a dictionary
		name of parameter : value
		"""
	mydict = {'':''}
	with open(inifile,"r") as f:
		for line in f:
			if param in line:
				a,b = split(line[:-1],"=")
				#logging.debug("Found: %s %s %s" %(a,param,b))
				mydict [strip(a)] = strip(b)
	# cleaning empty entry
	mydict.pop("",None)
	return mydict

def listtags(inifile,var,sep):
	""" This function reads lines from an .ini file and gets parameters 
		to 	return a list of the same Tag(alias) values.

		to read an ini-file like that:
			alias=string1
			alias=string2
			aliasX=string 3

		you should call this function as:
			readdict("/pathtofile/file.ini","alias","=")

		and you'll get:
			['string1','string2']
			# but not 'string3' so it is another alias.

	input:
		file (path)
		var to read
		sep identifier
	output:
		a list of sttrings
		"""	
	mylist = ['']
	with open(inifile,"r") as f:
		for line in f:
			a,b = split(line[:-1],sep)
			if strip(a) == var:
				#logging.debug("Found: "+line)
				#Cleaning and adding to list
				a1 , b1 = split (b,"\t")
				mylist.append (strip(a1)+"\t"+strip(b1))
	# cleaning empty entry if any registry is found
	if len (mylist) > 1:
		mylist.remove("")
	return mylist

def writedict_string(var,dict,sep=","):
	""" This function outputs a formatted string in a .ini like form.

		to write an ini-file like that:
			alias=word1,result1
			alias=word2,result2

		you should call this function as:
			writedict_string("alias",dictionary,",")
	input:
		alias
		dictionary to write
		sep identifier
	output:
		a formatted string with a new line on each key.
		"""	
	for a,b in dict.items():
		line = var+"="+a+sep+b+"\n"

# NamefilmCleaner Functions --------------

def trimbetween(a, lim):
	''' Trims a string between a pair of defined characters.
	input: "string"
	input: two characters (in order) pe. "[]"
	outputt: processed string

	inform the argument by two caracters
	p.e.  source: "La.Espada.Magica.DVDRip.[www.DivxTotal.com].LeoParis", "[]"
	results in : "La.Espada.Magica.DVDRip..LeoParis"

	DefTest >> OK'''
	cc = 0
	while True :
		st = a.find(lim[0])
		end = a.find(lim[1])
		if st > end and end != -1:
			a = a[0:end]+"\t"+a[end+1:] # We add a tab to mark this place and restart
			continue
		if st == -1 or end == -1 or st == end :
			break
		else:
			word = a[st+1:end]
			trim = 1
			# If there is a Season or Chapter id. we do not want to loose it >> so trim = 0
			for i in GideonConfig.chapteridentifier + GideonConfig.seasonidentifer :
				if word.find(i) != -1 or word == i :
					a = a[0:st]+"-"+word+"-"+a[end+1:]
					trim = 0
			if trim == 1:
				a = a[0:st]+a[end+1:]
	a = a.replace("\t",lim[1]) # we substitute tabs with end limit.
	return a

def dotreplacement(a,lim):
	'''replaces character between leters
	
	usage: dotreplacement ("string.with.some.dots.", ". ")
		input: "String.to.process"
		input: "lim" String, must contain two characters: caracter to search and character to replace with.
		output: "String to process" (procesed string)
	DefTest >> OK'''
	if a != '':
		leters = "1234567890abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ+*()[]_.-"
		while True :
			#logging.debug(a)
			st = a.find(lim[0])
			if a[0] == lim[0]:
				a = lim[1]+a[1:]
			elif a[-1] == lim[0]:
				a = a[0:-1]
			elif st == -1:
				break
			elif not (a[st-1] in leters and a[st+1] in leters):
				break
			else:
				a = a[0:st]+lim[1]+a[st+1:]
	return a

def prohibitedwords(a,lista):
	'''  Eliminates words in text entries
		those words matches if they are between spaces.
		input: "string with some words."
		input: ['List','of','words']
		outputt: "string without this words".
	DefTest >> OK'''

	delimiters = ('','()','[]','{}','__','··')
	for limit in delimiters:
		if limit != '':
			st,end = limit[0],limit[1]
		else:
			st,end = '',''
		for pw in lista:
			# words in the middle
			nww = st + pw + end
			x = a.upper().find (" " + nww.upper() + " ")
			if x >= 0:
				a = a[:x] + a[x+len(nww)+1:]
			# words at the end
			if len (nww)+1 < len (a):
				if a.upper().endswith ( " " + nww.upper()):
					a = a[:-len(nww)-1]
			# words at the begining
			if len (nww) + 1 < len (a):
				if a.upper().startswith(nww.upper() + " "):
					a = a[len(nww) + 1 :]
	return a

def Chapterfinder(filename):
	""" This function, scans for a chapter-counter 
		it will delete any punctuation character at the end and 
		it will also try to find numbers at the end of the filename. 
		If filename ends in three numbers, it'll change 'nnn' to 'nxnn'.
		This not affects if filename ends in four or more numbers. 'nnnn' so they are treated as a 'year'
		for example:

		Chapterfinder("my title 123") returns a tuple>> "my title 1x23", '1x23'
		Chapterfinder("my title 123-[[[") returns a tuple >> "my title 1x23", '1x23'
		Chapterfinder("my title ending in a year 1985") returns a tuple >> "my title ending in a year 1985", None
	DefTest >> OK	"""
	if filename == "":
		logging.warning("Empty filename to find chapter!")
		return filename, None, None
	base = clearfilename (filename)
	# we trim not wanted characters at the end:
	count = 0
	for a in base[::-1]:
		if a in '[]-:,*+_. ':
			count +=1
			continue
		break
	if count != 0:
		base = base [0:-count]		
		#logging.debug("namebase has changed to "+base)
	if base == "" or len(base) < 5:
			logging.warning("filename made of simbols or very short, returning same filename")
			return filename, None, None
	
	# finding first chapter identifier, cleaning chars before capter
	for expr in ('\d{1,2}[xX]\d{1,3}|[sS]\d{1,2}[._ ]?[eE]\d{1,3}','[eE][pP][_ ]?\d{1,3}'):
		mo = re.search (expr, base)
		try:
			grupo = mo.group()
		except:
			pass
		else:
			Chap = mo.group().lower()
			Chap = Chap.replace(' ','.')
			# Set the X to lower in filename
			# Set a '.' if there is a title especification after chapter and skip spaces.
			beforechar, afterchar = ('' , '')
			if mo.end() < len (base) and base[mo.end()] != '.':
				afterchar = '.'
				if base[mo.end()] == ' ':
					base = base[:mo.end()] + base[mo.end():].lstrip()
			if mo.start() > 2 and base[mo.start()-1] != ' ':
				beforechar = ' '
			Seriename = base[:mo.start()]
			base = Seriename + beforechar + Chap + afterchar + base[mo.end():]
			Seriename = Seriename.strip()
			if len (Seriename) < 3: Seriename = None
			return base, Chap, Seriename


	# finding 3 final numbers if no chapter found before
	expr = '[-. ]\d{3}'
	mo = re.search (expr, base[-4:])
	try:
		grupo = mo.group()
	except:
		pass
	else:
		Chap = base[-3:-2]+'x'+base[-2:]
		Seriename = base[:-4]
		base = Seriename + ' ' + Chap
		Seriename = Seriename.strip()
		if len (Seriename) < 3: Seriename = None
		return base, Chap, Seriename

	# finding Seasons and Chapters as Wordings
	inputbase = base
	season = None
	episode = None
	seriename = ''
	serieidpos = None
	for seasonword in seasonidentifer:
		expr = '%s[ _.-]?(?P<number>\d{1,3})'% (seasonword.lower())
		mo = re.search (expr,base.lower())
		try:
			grupo = mo.group()
		except:
			pass
		else:
			season = mo.group('number')
			lon = len (grupo)
			st = mo.start()
			serieidpos = st
			base = base[:st] + base [st+lon:]
			seriename = base[:st].strip()
			break

	for chapterword in chapteridentifier:
		expr = '%s[ _.-]?(?P<number>\d{1,3})'%(chapterword.lower())
		mo = re.search (expr,base.lower())
		try:
			grupo = mo.group()
		except:
			if season != None:
				base = inputbase
			pass
		else:
			episode = mo.group('number')
			lon = len (grupo)
			st = mo.start()
			base = base[:st] + base [st+lon:]
			if serieidpos != None:
				if st > serieidpos: st = serieidpos
			seriename = base[:st].strip()
			break

	if episode != None:
		episodetxt = 'x'
		if season == None:
			episodetxt = 'ep'
			seasonpart = ''
		else:
			seasonpart = '{0:01}'.format(int(season))
		Chap =  seasonpart + episodetxt + '{0:02}'.format(int(episode))
		base = seriename + ' ' + Chap
		return base, Chap, seriename


	return base, None, None

def chapid(item):
	''' Checks four last char$ of filename.
		Returns chapter number if a chapter is found.

		Chapters are idenfied with this mask :  'nxnn'
		input: fullpath (or not) of filename
		output: number of chapter (string) _or_
		output: ""  if no chapter is found.
	DefTest >> OK'''
	expr = '\d[xX]\d{2}'
	mo = re.search (expr, item[-4:])
	try:
		grupo = mo.group()
	except:
		return ''
	else:
		return item[-2:]
	
def littlewords(filename):
	''' Change little words starting uppercase to lowercase. This words must be defined.
		'''
	words = ["in","to","my","the","and","on","at","of","en","a","y","de","o","el","la","los","las","del", "lo", "es","su", "mi", "tu" ]
	for a in words:
		wa=" "+a[0].upper()+a[1:]+" "
		wb=" "+a+" "
		filename = filename.replace(wa,wb)
	return filename

def clearfilename(filename):
	""" Process several filters for filename cleaning
		input: filename without extension, please
		output: filename without extension, of course
		
		DefTest >> OK
		"""
	logging.debug ("# Cleaning filename: "+filename)
	filenametmp = filename

	
	#1 replacing dots, underscores & half  between leters.
	filenametmp = filenametmp.replace('_.','.')
	filenametmp = dotreplacement(filenametmp, "_ ")
	filenametmp = dotreplacement(filenametmp, "- ")
	filenametmp = dotreplacement(filenametmp, ". ")

	#2 trimming brackets
	filenametmp = trimbetween(filenametmp, "[]")
	
	#3 Replacing prohibited words.
	
	while True:
		filenametmp2 = prohibitedwords (filenametmp,GideonConfig.prohibited_words)
		if filenametmp == filenametmp2 :
			break
		filenametmp = filenametmp2

	while True:
		loop = 0
		#4 Trimming first and last spaces
		filenametmp = filenametmp.strip()
		if filenametmp[0] == " " or filenametmp[-1] == " ":
			loop = 1
		#5 Trimming first and last dots.
		if filenametmp[-1] == ".":
			filenametmp = filenametmp [:-1]
			loop = 1
		if filenametmp[0] == ".":
			filenametmp	= filenametmp [1:]
			loop = 1
		if loop == 0 :
			break

	#6 Finding and placing a Chapter-counter
	#filenametmp = Chapterfinder(filenametmp)[0]

	#7 Formatting as Title Type
	filenametmp = filenametmp.title()

	#8 Replacing little words to lowerCase
	filenametmp = littlewords (filenametmp)

	logging.debug ("# Final Filename   : "+ filenametmp)
	return filenametmp

# Main Functions -------------------------

def copyfile(origin,dest,mode="c", replace=True):
	""" Copy or moves file to another place
		origin: file origin (full/relative patn and name)
		dest: file destination (full/relative path an name)
		mode: "c" for copy, "m" for move (default "c")
		replace: True for replace existing file or False to skip. (default True)

		return
		'Missed' if origin does not exists or is not a file.
		'Skipped' if destination file already exists and replace = False (only checks the filename)
		'Copied' if file was copied
		'Moved' if file was moved
		"""
	
	if itemcheck(origin) != "file":
		logging.debug("\tOrigin file does not exists or is not a file. Nothing to do!")
		return 'Missed'

	destnature = itemcheck(dest)
	if destnature != "file" and destnature != "" :
		logging.warning ('Destination pointer is not a file, cannot continue copying')
		return 'Skipped'
	if destnature == 'file':
		logging.debug("\tDestination file already exists")
		if replace:
			logging.info ('\tReplacing file.')
			os.remove (dest)
		else:
			logging.info ('\tFile has not been replaced.')
			return 'Skipped'
	else:
		makepaths ([os.path.dirname(dest),])
	if mode == "c":
		shutil.copy(origin,dest)
		return 'Copied'
	if mode == "m":
		shutil.move(origin,dest)
		return 'Moved'

def matchfilm(filmname,lista):
	''' Selects a item from a list with the best match.
		it is intended to find a cover file within a list of possible covers.

		input: filename.ext or full-path/filename.ext of a movie.
		input: list of items to match (filenames.ext or full-path/filenames.ext) (of covers)
		output: item of the list (of covers) that best matches as "cover", and punctuation of match
		Deftest OK!!'''
	# We want only the name of the file, without extension.
	match = 0
	matcheditem = ''
	for a in lista:
		# Get only the filename without extension
		name = os.path.splitext(os.path.basename(a))[0]
		if name == '': continue

		points = 0
		for b in name.split():
			if (b.upper() in filmname.upper()) and not (2 <= len (b) <= 3):
				points += len(b)

		if filmname.upper() in name.upper() or name.upper() in filmname.upper():
			points += len (name)

		points =  points / len (name) * 100
		

		if points > match and points > minmatch:
			matcheditem, match = a, points
	return matcheditem, int(match)

def Getsubpath(filmname,Fvideodest):
	""" Delivers a fideofile in order a pertenency on a group
		input: filmname
		input: dictionary with keys and subpaths to compare (Fvideodest var)
		
		output: Best Subpath matched . It returs "" if not matches were found
		Deftest OK!!"""
	logging.debug("\tAssigning a sub-path defined in alias")
	destinationlist = [""]
	for a in Fvideodest:
		destinationlist.append(a)
	r1, match = matchfilm (filmname, destinationlist)
	if r1 == "" or match < minmatch:
		logging.debug("\t\tNo mathches found to deliver, returning default path for the item")
		return "", 0
	return Fvideodest[r1], match

def getaliaspaths (textfile):
	""" Returns a dictionary contanining words and a relative path to store filesdict
		The keys are fetched from a txt .ini like file.
		Deftest OK!! """
	alias = readdict (textfile,"alias",",")
	subpahts = readdict (textfile,"dest",",")
	for a in alias:
		for b,c in subpahts.items():
			if "<"+a+">" in c:
				subpahts[b]=c.replace("<"+a+">",alias[a])

	# paths in destinations must not start with "/" either end in "/"
	for a,b in subpahts.items():
		if len (b) > 0:
			if b[0] == "/":
				b = b [1:]
			if b[-1] == "/":
				b = b [:-1]
			subpahts[a] = b
	return subpahts

def fileclasify (filename):
	""" Classify a file
		input: file
		output: 'other' (default), 'audio', 'video', 'movie', 'compressed', 'image', 'ebook', 'comic'
		
		DefTest OK"""
	global GideonConfig
	file_split = os.path.splitext(filename)
	if str(file_split[1]) in ['','.']:
		print ('>>>>',filename)
		logging.warning('File has no extension: %s'%filename)
		return 'other'
	file_ext = str (file_split [1])
	file_ext = file_ext [1:].lower()
	if file_ext in GideonConfig.ext['video']:
		if Chapterfinder (file_split[0])[1] != None:
			return 'vserie'
		return 'video'
	elif file_ext in GideonConfig.ext['audio']: return 'audio'
	elif file_ext in GideonConfig.ext['ebook']: return 'ebook'
	elif file_ext in GideonConfig.ext['comic']: return 'comic'
	elif file_ext in GideonConfig.ext['compressed']: return 'compressed'
	elif file_ext in GideonConfig.ext['notwanted']: return 'notwanted'
	elif file_ext in GideonConfig.ext['image']: return 'image'
	return 'other'

def emailme(msgfrom, msgsubject, msgto, textfile, msgcc=''):
	'''Send a mail notification.
		parameters:
			msgfrom = e-mail from
			msgsubjet = Subject (string in one line)
			msgto = mail_recipients (could be more than one parsed into a string colon (:) separated)
			textfile = path to textfile, this is the body of the message. You can pass a string anyway,
		'''
	
	global GideonConfig
	
	# Open a plain text file for reading.
	if itemcheck (textfile) == "file":
		# the text file must contain only ASCII characters.
		with open(textfile) as fp:
			# Create a text/plain message
			msg = MIMEText(fp.read())
	else:
		msg = MIMEText(textfile)

	msg['Subject'] = msgsubject
	msg['From'] = msgfrom
	msg['To'] = msgto
	msg['Cc'] = msgcc

	# Send the message via our own SMTP server.
	s = smtplib.SMTP(GideonConfig.mailmachine)
	s.starttls()
	s.login( GideonConfig.mailsender, GideonConfig.mailpassw) # your user account and password
	s.send_message(msg)
	s.quit( )
	return

def get_pid (app):
	''' returns None if the aplication is not running, or
		returns application PID if the aplication is running 
		'''
	try:
		pids = check_output(["pidof", app ])
	except:
		logging.debug('no %s app is currently running'%(app))
		return None
	pidlist = pids.split()
	la = lambda x : int(x)
	pidlist = list (map (la , pidlist))
	return pidlist

def getappstatus (app):
	''' Given a list of names's process, it checks if there is any instance running
		DefTest >> OK'''
	state = False
	for entry in app:
		if get_pid (entry) != None:
			state = True
	return state

def extfilemove(origin,dest,extensions=[]):
	''' This function scans files that matches desired extensions and
		moves them to another place (destination).

		this function is not case sensitive, son you can especify "jpg" for 
		"JPG" or "jpg" extensions. Names on filenames are not changed.
		As a result, this function returns a list of moved files.
		
		input:
			origin: ./path/to/look/for/
			dest: ./path/to/move/files/to/
			extensions: ("list","of","extensions","to","move")
		output:
			("list of files", "that have been moved", "on its destination")
		DefTest >> OK '''
	# Checking folders:
	if itemcheck (origin) in (["","file"]):
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check GideonConfig and set up Hotfolder to a valid path")
	if itemcheck (dest) in (["","file"]):
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check GideonConfig and set up Torrentinbox to a valid path")
	origin, dest = addslash (origin), addslash (dest)
	items = []
	newitems = [origin + i for i in os.listdir (origin)]
	for i in newitems:
		if itemcheck(i) == 'file':
			for a in extensions:
				if os.path.splitext(i)[1].upper() == "."+a.upper():
					items.append(i)
	moveditems = []
	for i in items:
		name = os.path.basename(i)
		basename, extension = os.path.splitext(name)[0], os.path.splitext(name)[1].lower()
		# Freevo does not like jpeg extensions, replacing them
		if extension == ".jpeg":
			extension = ".jpg"
		# new cover's name will be cleaned for better procesing
		cleanedname = clearfilename (basename)
		itemdest =  dest+cleanedname+extension
		while copyfile (i,itemdest,mode="m") == 'Exists':
			itemdest = nextfilenumber (itemdest)
		moveditems.append (itemdest)
	return moveditems

def Dropfd(destfolder, lsextensions):
	''' move .torrents and covers from one destination to another.
		Pej. after setup your hotfolder, you can place there .torrent files or covers to 
		Start processing downloads or covers to have in mind.
		.torrent files and covers goes to $HOME/.Gideon/Torrentinbox folder
		'''
	movelist = extfilemove (TransmissionInbox, destfolder, lsextensions)
	if movelist == []:
		logging.debug("Nothing was in the Dropbox-hot-folder.")
	else:
		logging.info("Those files were processed: from Hotfolder:")
		for a in movelist:
			logging.info('\t'+ a)
	return movelist

def addinputs (entrieslist):
	''' Add new torrent entries into a DB queue,
	This queue is stored into the software database SQLite. > Table "TW_Inputs"
	[('/home/pablo/.Gideon/Torrentinbox/Lazona 102 Avi.torrent', '.torrent')]
		'''
	if len (entrieslist) > 0:
		con = sqlite3.connect (dbpath)
		cursor = con.cursor()
		for Entry, Filetype in entrieslist:
			if cursor.execute ("SELECT count (id) from tw_inputs where fullfilepath = ? and status = 'Added' ", (Entry,)).fetchone()[0] == 0:
				cursor.execute ("INSERT INTO tw_inputs (fullfilepath, filetype) VALUES (?,?)", (Entry,Filetype))
				Id = (con.execute ('SELECT max (id) from tw_inputs').fetchone())[0]
				logging.info ('({})added incoming job to process: {}'.format(Id, Entry))
				SpoolUserMessages(con, 1, TRid = Id)
				con.commit()
		con.close()
	return

def launchTR (cmdline, seconds=0):
	os.system(cmdline)
	logging.info ('Transmission has been launched.')
	time.sleep(seconds)
	return

def connectTR():
	if not getappstatus(['transmission-gtk']):
		launchTR (cmd, 5)
	tc = transmissionrpc.Client(address=TRmachine, port = '9091' ,user=TRuser, password=TRpassword)
	logging.debug('A Transmission rpc session has started')
	return tc

def SendtoTransmission():
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	nfound = (cursor.execute ("SELECT count(id) FROM tw_inputs WHERE status = 'Ready' and ( filetype = '.magnet' or filetype = '.torrent')").fetchone())[0]
	if nfound > 0:
		logging.info (str(nfound) + ' new torrent entries have been found.')
		tc = connectTR ()
		cursor.execute ("SELECT id, fullfilepath FROM tw_inputs WHERE status = 'Ready'  and ( filetype = '.magnet' or filetype = '.torrent')")
		for Id, Fullfilepath in cursor:
			try:
				trobject = tc.add_torrent (Fullfilepath)
				TRname = trobject.name
				TRhash = trobject.hashString
				print ('Added a new torrent \n',Fullfilepath, TRname, 'Hash: '+ TRhash, sep='\n\t')
				con.execute ("UPDATE tw_inputs SET status='Added',  hashstring = ? , trname=? WHERE id=?", (TRhash, TRname,str(Id)))
				SpoolUserMessages(con, 2, TRid = Id)
			except transmissionrpc.error.TransmissionError:
				print ('Transmission ERROR adding an incomming job!:%s'%Fullfilepath)
				con.execute ("UPDATE tw_inputs SET status='Error' WHERE id=%s"%(str(Id)))
				logging.warning ('This torrent file has raised an Error: %s'%Fullfilepath)
				print ('Spooling error message')
				SpoolUserMessages(con, 13, TRid = Id)
		con.commit()
	con.close()
	return

def TrackManualTorrents(tc):
	''' Scans for list of torrents currently in transmission,
		add to DB those which are unknown.
		Those torrents are 'untracked torrents', and usually has been added
		directly to transmission by the user.
		With this function, Gideon will track them.
		'''
	trobjlst = tc.get_torrents()
	if len (trobjlst) > 0:
		con = sqlite3.connect (dbpath)
		cursor = con.cursor()
		for trobject in tc.get_torrents():
			DBid = cursor.execute ("SELECT id from tw_inputs WHERE hashstring = ? and (status = 'Ready' or status = 'Added' or status = 'Completed') ORDER BY id DESC", (trobject.hashString,)).fetchone()
			if DBid == None and ( trobject.status in ['check pending', 'checking', 'downloading', 'seeding']):
				params = (trobject.magnetLink, '.magnet', 'Added', trobject.name, trobject.hashString)
				cursor.execute ("INSERT INTO tw_inputs (Fullfilepath, filetype, status, TRname, hashstring) VALUES (?,?,?,?,?)", params)
				logging.info ('Found new entry in transmission, added into DB for tracking: %s' %trobject.name)
				Id = (con.execute ('SELECT max (id) from tw_inputs').fetchone())[0]
				SpoolUserMessages(con, 3, TRid = Id)
		con.commit()
		con.close()
	return

def TrackDeletedTorrents (tc):
	''' Check if 'Added' torrents in DB are still in Transmission.
		If an entry is not present at transmission service, it will be mark as 'Deleted'
		'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, hashstring from tw_inputs WHERE (status = 'Added' or status = 'Completed') and (filetype='.magnet' OR filetype = '.torrent')")
	for Id, HashString in cursor:
		if len(tc.info(HashString)) == 0:
			con.execute ("UPDATE tw_inputs SET status='Deleted' WHERE id = ?", (Id,))
			SpoolUserMessages(con, 4, TRid = Id)
	con.commit()
	con.close()
	return

def TrackFinishedTorrents (tc):
	''' Check if 'Added' torrents in DB are commpleted in Transmission.
		If an entry is not present, it will be mark as 'Deleted'
		'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, hashstring, fullfilepath, filetype from tw_inputs WHERE status = 'Added' and (filetype='.magnet' OR filetype = '.torrent')")
	for DBid, HashString, Fullfilepath, Filetype in cursor:
		if HashString == None:
			logging.warning ('An entry has been added to Transmission Service and has not a HashString yet.')
			continue
		trr = tc.get_torrent(HashString)
		if trr.status in ['seeding','stopped'] and trr.progress >= 100:
			con.execute ("UPDATE tw_inputs SET status='Completed', dwfolder = ? WHERE id = ?", (trr.downloadDir ,DBid))
			SpoolUserMessages(con, 5, TRid = DBid)
	con.commit()
	con.close()

def SpoolUserMessages(con, Topic, TRid=None):
	''' Insert an outgoing message into Data base,
		it assign a date of message release, so many messages can be send a time into one e-mail
		'''
	params = ('Ready', Topic, TRid)
	con.execute ("INSERT INTO msg_inputs (status, topic, trid) VALUES (?,?,?)", params)
	return

def STmail (title, msg, topic=0):
	msgfrom = GideonConfig.mailsender
	msgto = ",".join(getrecipients(topic, mail_topic_recipients))
	msgsubject = title
	textfile = msg
	if msgto != '':
		emailme(msgfrom, msgsubject, msgto, textfile, msgcc="")
	else:
		logging.info('No senders were configured to send this e-mails with topic number %s'%topic)
	return

def MsgService():
	con = sqlite3.connect (dbpath)
	mailStartedSevice (con)
	mailErrors (con)
	mailaddedtorrents (con)
	mailpreasignedtorrents (con)
	#mailnocasetorrents (con)  #  TO DO ----  8
	mailcompletedjobs (con)
	mailRPolicytorrents (con)
	con.close()
	return

def mailnocasetorrents (con):
	pass 

def mailRPolicytorrents(con):
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname, dwfolder FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' and msg_inputs.topic = 10")
	for Nreg, Trid, Trname, Dwfolder in cursor:
		msg = """A torrent has been deleted due to a configured Retention Policy:
	(%s days after downloading has been completed or Torrent's seeding ratio has finished.)
	Torrent id in data base (%s), Name:
	%s
	
	It has been deleted from Transmission Service,
	Downloaded files at %s have been also deleted.

	""" %(MaxseedingDays,Trid,Trname, Dwfolder)
		msg += "---------------------------------------"
		msg += "This is a full log of the torrent life:\n\n"
		msg += getactivitylogTXT(con,Trid)
		STmail ('Torrent Deleted: ' + Trname, msg, topic=10)
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
	con.commit()
	return

def mailaddedtorrents(con):
	lines = list()
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname, filetype FROM msg_inputs JOIN tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' AND msg_inputs.topic = 1 AND trname IS NOT NULL")
	for Nreg, Trid, Trname, Filetype in cursor:
		lines.append ("(%s), %s,Job name: %s" %(Trid, Filetype[1:], Trname))
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
	if len (lines) > 0:
		msg = "New jobs have been added to process:\n"
		for l in lines:
			msg += "\n"+l
		subject = 'New Jobs added to Gideon: '
		if len (lines) == 1:
			subject += Trname
		STmail (subject, msg, topic=1)
		con.commit()
	return

def mailErrors(con):
	lines = list()
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid,fullfilepath FROM msg_inputs JOIN tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' AND msg_inputs.topic = 13 ")
	for Nreg, Trid, Fullfilepath in cursor:
		lines.append ("(%s): %s" %(Trid, Fullfilepath))
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
	if len (lines) > 0:
		msg = "There have been errors adding this torrent files:\n"
		for l in lines:
			msg += "\n"+l
		subject = 'Errors adding new Jobs to Gideon: '
		if len (lines) == 1:
			subject += os.path.splitext(os.path.basename(Fullfilepath))[0]
		STmail (subject, msg, topic=13)
		con.commit()
	return

def mailStartedSevice(con):
	cursor = con.cursor ()
	ncount = cursor.execute ("SELECT count (nreg) FROM msg_inputs WHERE topic = 9 and status = 'Ready'").fetchone()[0]
	if ncount > 0:
		msgtrrlst = gettrrpendingTXT (con)
		msg = """Torrent Service has just Started due to incomplete downloads:
		
		%s
		
		""" %(msgtrrlst)

		STmail ('Transmission Service Started ', msg, topic=9)
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE topic = 9")
	con.commit()
	return

def mailcompletedjobs(con):
	''' e-mail Completed torrents, this is to inform that a torrent have been processed
	usually corresponds with the preasigned destinations.
	It could contain other info of the torrent process.
	It corresponds with topic nº7 in DB, "Files have been processed and copied into destination"
	It should send one e-mail for each torrent file.
	The body should have "torrent ID in database for further information." >> Trid = ...
	'''
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname, fullfilepath, filetype FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' and msg_inputs.topic = 7")
	for Nreg, Trid, Trname, Fullfilepath, Filetype in cursor:
		if Trname is None:
			Trname = os.path.basename (Fullfilepath)
		NCase = con.execute ("SELECT caso FROM pattern WHERE trid=%s"%Trid).fetchone()[0]
		if NCase > 0:
			msgbody = "A %s job has been Delivered to its destination: \n\
				Job Name: %s \n\
				trid = %s \n\
				Case = %s \n\n \
			Files movements:\n"%(Filetype [1:],Trname, Trid, Casos[NCase])

			filelisttxt, nonwantedfilestxt = getfiledeliverlistTXT (con,Trid)
			msgbody += filelisttxt + "\n"
			msgbody += nonwantedfilestxt + "\n"
			STmail ('Torrent completed and delivered: '+ Trname ,msgbody, topic=7)
		else:
			msgbody = "A torrent has been Downloaded: \n\
				Torrent Name: %s \n\
				trid = %s \n\
				Case = %s \n\n \
			It remains in Transmission default Download folder:\n"%(Trname, Trid, Casos[NCase])

			filelisttxt = getfileoriginlistTXT (con,Trid)
			msgbody += filelisttxt + "\n"
			# msgbody += gettorrentstatisticsTXT ()
			STmail ('Torrent is completed: '+ Trname ,msgbody, topic=7)
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = %s"%Nreg)
	con.commit()
	return

def getrecipients(topic, mail_topic_recipients):
	''' Given a topic number, return a set of recipients.
	mail_topic_recipients is defined as a dictionay, one or more e-mails as key, and a number-set 
	with associated topic numbers
	DEFTEST OK!!	'''
	recipients = set()
	for entry in mail_topic_recipients:
		if topic in mail_topic_recipients[entry]:
			recipients.add (entry)
	return recipients

def mailpreasignedtorrents (con):
	''' e-mail preasigned torrents, this is to inform what is going to download and
	How it is going to be process and delivered once it is completed.
	It corresponds with topic nº6 in DB, "List of files has been retrieved and preasigned"
	It should send one e-mail for each torrent file, but in case of series it should group all chapters into one.
	The body should have "torrent ID in database for further information." >> Trid = ...
	'''
	
	msggroupingdict = dict()  # Dictionary of Messages. It will group the same messages for the same series-series
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname, fullfilepath, filetype FROM msg_inputs JOIN tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' and msg_inputs.topic = 6")
	for r in cursor:
		Nreg, Trid, Trname, Fullfilepath, Filetype = r[0], r[1], r[2], r[3], r[4]
		if Filetype in ('.torrent','.magnet'):
			Jobname = Trname
		elif Filetype in ('.file', '.folder'):
			Jobname = os.path.basename (Fullfilepath)
		else:
			logging.critical ('unknown job type, Skipping...')
			continue
		NCase = con.execute ("SELECT caso FROM pattern WHERE trid=%s"%Trid).fetchone()[0]

		if NCase in (1,2):  ## Cases 1 and 2 only has one video file.
			fullfilepath = con.execute ("SELECT destfile FROM files WHERE trid=%s and wanted = 1 and mime = 'video' "%Trid).fetchone()[0]
			filename = os.path.splitext(os.path.basename (fullfilepath))[0]
			groupingtitle = filename
			if chapid (filename) != '':
				groupingtitle = filename [:-2]
		else:
			groupingtitle = Jobname

		filelisttxt, nonwantedfilestxt = getfiledeliverlistTXT (con,Trid)
		msgbody = "A new download job has been preasigned: \n\
			Job Name: %s \n\
			Job Type = %s \n\
			trid = %s \n\
			Case = %s \n\n \
		Predeliver:\n"%(Jobname, Filetype[1:],Trid, Casos[NCase])
		msgbody += filelisttxt + "\n"
		msgbody += nonwantedfilestxt + "\n"
		
		if groupingtitle in msggroupingdict:
			msgbody = msggroupingdict[groupingtitle] + '\n\n' + msgbody
		msggroupingdict [groupingtitle] = msgbody

		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
	for job in msggroupingdict:
		STmail ('Predelivered status for: '+ job, msggroupingdict [job], topic = 6 )
	con.commit()
	return

def gettrrpendingTXT (con):
	cursor2 = con.execute ("SELECT id, trname FROM tw_inputs WHERE status = 'Added' AND (filetype = '.torrent' OR filetype = '.magnet') ORDER BY added_date")
	filelisttxt = "Torrents pending downloading:\n"
	for entry in cursor2:
		Trname = entry[1]
		if Trname == None:
			Trname = 'WARNING, Torrent without a valid NAME!'
		filelisttxt += "\t"+str(entry[0])+"\t"+entry[1]+"\n"
	return filelisttxt

def getfiledeliverlistTXT (con,Trid):
	cursor2 = con.execute ("SELECT wanted, size, originalfile, destfile FROM files WHERE trid = %s ORDER BY destfile"%Trid)
	filelisttxt = "List of files: \n"
	nonwantedfilestxt = ""
	for entry in cursor2:
		Wanted   = entry[0]
		Size     = entry[1]
		Originalfile = entry[2]
		Destfile = entry[3]
		if Destfile == None:
			Destfile = Originalfile
		if Wanted == 1:
			filelisttxt += "\t"+Destfile+"\t("+toHumanSizeReadable(Size)+")\n"
		else:
			if nonwantedfilestxt == "":
				nonwantedfilestxt = "List of nonwanted files: \n"
			nonwantedfilestxt += "\t" + os.path.basename(Originalfile)+"\t("+toHumanSizeReadable(Size)+")\n"
	
	return filelisttxt, nonwantedfilestxt

def getfileoriginlistTXT (con,Trid):
	Dwfolder = con.execute ("SELECT dwfolder from tw_inputs WHERE id = %s"%Trid).fetchone()[0]
	if Dwfolder == None:
		Dwfolder =''
	Dwfolder = addslash(Dwfolder)
	cursor2 = con.execute ("SELECT wanted, size, originalfile FROM files WHERE trid = %s ORDER BY originalfile "%Trid)
	filelisttxt = "List of files: \n"
	for entry in cursor2:
		filelisttxt += "\t"+Dwfolder+entry[2]+"\t("+toHumanSizeReadable(entry[1])+")\n"
	return filelisttxt

def getactivitylogTXT (con,Trid):
	TRname, Fullfilepath, Filetype, Dwfolder, Filesretrieved = con.execute ("SELECT trname, fullfilepath, filetype, dwfolder, filesretrieved FROM tw_inputs WHERE id = %s"%Trid).fetchone()
	Caso = con.execute("SELECT Caso FROM pattern WHERE trid = %s"%Trid).fetchone()[0]
	cursor = con.execute ("SELECT added_date, topic FROM msg_inputs WHERE trid = %s ORDER BY added_date ASC"%Trid)
	activityTXT = 'Activity for %s:'%(TRname) + '\n'
	for date, topic in cursor:
		if topic == 1:
			txt = "%s\tTorrent was registered to be processed: torrent file name:%s"%(date, os.path.basename(Fullfilepath))
			activityTXT += txt + '\n'
		elif topic == 2:
			txt = "%s\tTorrent was added to Transmission for downloading."%date
			activityTXT += txt + '\n'
		elif topic == 3:
			txt = "%s\tTorrent was manually added to Transmission: MagnetLink: %s"%(date,Fullfilepath)
			activityTXT += txt + '\n'
		elif topic == 4:
			txt = "%s\tTorrent was manually deleted."%date
			activityTXT += txt + '\n'
		elif topic == 5:
			txt = "%s\tTorrent completed downloading."%date
			txt += "\tDownloaded folder: %s"%Dwfolder
			activityTXT += txt + '\n'
		elif topic == 6:
			txt = "%s\tTorrent was checked and preasigned:"%date
			txt += "\t Content of torrent (%s) files:\n"%Filesretrieved
			txt += getfileoriginlistTXT (con, Trid)
			activityTXT += txt + '\n'
		elif topic == 7:
			txt = "%s\tTorrent was processed and a file copying was performed:\n"%date
			txt += "\tCase %s: (%s).\n"%(Caso, Casos[Caso])
			txt += "\tProcessed files:\n"
			filelisttxt, nonwantedfilestxt = getfiledeliverlistTXT (con,Trid)
			txt += filelisttxt + "\n"
			txt += nonwantedfilestxt + "\n"
			activityTXT += txt + '\n'
		elif topic == 8:
			txt = "%s\tNo case was found:"%date
			txt += "\t Orifinal content of torrent (%s) files:\n"%Filesretrieved
			txt += getfileoriginlistTXT (con, Trid)
			activityTXT += txt + '\n'
		elif topic == 10:
			txt = "%s\tTorrent was deleted due to configured retiention policy:"%date
			activityTXT += txt + '\n'
		elif topic == 11:
			txt = "%s\tA movie file of this torrent was assigned a cover."%date
			activityTXT += txt + '\n'
	return activityTXT

def RetrieveTorrentFiles (tc):
	''' Selects from tW_inputs the new imputs, process their files and do the predeliver at DB
	'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, hashstring FROM tw_inputs WHERE filesretrieved IS NULL and (status = 'Added' or status = 'Completed') AND trname IS NOT NULL")
	cursorFreeze = list()
	for entry in cursor:
		cursorFreeze.append(entry)
	for DBid, HashString in cursorFreeze:
		trr = tc.get_torrent (HashString)
		if len(tc.info(HashString)) == 0:
			logging.warning ("Can't get torrent object: DBid: %s"%DBid)
			continue
		filesdict = trr.files()
		if len(filesdict) == 0:
			print ("Torrent may be waitting for files....")
			continue
		AddFilesToDB (con, DBid, filesdict, 'Transmission')
	con.close()

def Retrievefilesdict ( Fullfilepath, Filetype):
	''' Given a file or a folder, it creates a dictionary with information as a torrent does.
		it returns this dictionary
		Keys used by Gideon and Transmission-Service:
		{0: {
			'size': _in bytes_,
			'name': _filename with relative path to the main node_,
			},
		 1: {'size': _in bytes_,
			'name': _filename relativepath_,}
			...........}
	'''
	CollectionDictionary = dict ()
	regcounter = 0

	if Filetype == '.folder':
		itempath = Fullfilepath
		folderlist = lsdirectorytree (Fullfilepath)
		for subdirectory in folderlist:
			filelist = [(subdirectory + '/' + i) for i in os.listdir(subdirectory)]
			for entry in filelist:
				if itemcheck (entry) != 'file':
					continue
				name = entry [len(os.path.dirname(Fullfilepath))+1:]
				size = os.path.getsize (entry)
				itemdict = {'name': name , 'size': size}
				CollectionDictionary[regcounter] = itemdict			
				regcounter += 1
	elif Filetype == '.file':
		itempath = os.path.dirname(Fullfilepath)
		itemdict = {'name': os.path.basename(Fullfilepath)}
		itemdict['size'] = os.path.getsize(Fullfilepath)
		CollectionDictionary = {regcounter : itemdict}

	else:
		logging.critical ('Unknown entry-type, cannot continue, returning an empty dictionary of files.')

	return CollectionDictionary

class Matrix :
	""" Matrix generation for the set of downloaded files 
		it identifies de downloaded item in ordert to perform deliver actions """
	def __init__(self,TRid):
		self.TRid = TRid
		self.nfiles = 0
		self.nvideos = 0
		self.nseries = 0
		self.naudios = 0
		self.nnotwanted = 0
		self.ncompressed = 0
		self.nimagefiles = 0
		self.nother = 0
		self.nbooks = 0
		self.ncomics = 0
		self.nfolders = 0
		self.folderlevels = 0
		self.folders_Set = set ()

	def __addfolder__ (self,item):
		self.folders_Set.add (os.path.dirname(item))
		self.nfolders = len (self.folders_Set)
		nlev = 1 + item.count('/')
		if self.folderlevels < nlev:
			self.folderlevels = nlev

	def addfile (self,item):
		self.nfiles += 1
		mime = fileclasify (item)
		if mime == 'video' : self.nvideos += 1
		elif mime == 'vserie' : self.nseries += 1
		elif mime == 'audio' : self.naudios += 1
		elif mime == 'ebook' : self.nbooks += 1
		elif mime == 'comic' : self.ncomics += 1
		elif mime == 'compressed' :self.ncompressed += 1
		elif mime == 'notwanted' : self.nnotwanted += 1
		elif mime == 'image' : self.nimagefiles += 1
		else: self.nother += 1
		self.__addfolder__(item)

# =====================


def AddFilesToDB (con, TRid, filesdict, inputtype):
	''' Given a downloaded entry and its files-dict,
		it informs those files in the Data Base,
		it gets the matrix,
		inform the matrix into the database,
		it applies the process secuence and inform the destination of the files.
	'''
	Tmtx = Matrix (TRid)
	for key in filesdict:
		Size = filesdict.get(key)['size']
		Originalfile = filesdict.get(key)['name']
		Mime = fileclasify(Originalfile)
		params = TRid, Size, Originalfile, Mime
		con.execute ("INSERT INTO files (trid, size, originalfile, mime ) VALUES (?,?,?,?)",params)
		Tmtx.addfile(Originalfile)
	# Selecting Case and processing torrent files.
	Caso, Psecuence = Selectcase (Tmtx, inputtype, TRid=TRid)
	Deliverstatus = 'Added'
	if Caso == 0:
		Deliverstatus = None  # Torrents with no case are not delivered
	ProcessSecuence (con, TRid, Psecuence)
	params = len(filesdict), Deliverstatus ,TRid
	con.execute ("UPDATE tw_inputs SET filesretrieved=?, deliverstatus = ? WHERE id = ?",params)
	params = TRid, 'Added', Caso, str(Psecuence),   Tmtx.nfiles, Tmtx.nvideos, Tmtx.nseries, Tmtx.naudios, Tmtx.nnotwanted, Tmtx.ncompressed, Tmtx.nimagefiles, Tmtx.nother, Tmtx.nbooks, Tmtx.ncomics, Tmtx.nfolders, Tmtx.folderlevels
	con.execute ("INSERT INTO pattern (trid,status,caso,psecuence,nfiles,nvideos,nseries,naudios,nnotwanted,ncompressed,nimagefiles,nother,nbooks,ncomics,nfolders,folderlevels) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",params)
	con.commit()
	return

def ProcessSecuence(con, Id, Psecuence):
	global GideonConfig
	print ('Processing:{}'.format(Id))
	for process in Psecuence:
		print ("\t",process,'...........')
		filesetquery = "SELECT nreg, mime, originalfile, destfile FROM files WHERE trid = %s and wanted = 1"%Id
		cursor2 = con.execute (filesetquery)  # Is an iterator over the torrent files at database.
		
		if process == 'assign video destination':
			for entry in cursor2:
				params = (Fmovie_Folder+entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue

		elif process == 'assign serie destination':
			for entry in cursor2:
				params = (Fseries_Folder + entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue

		elif process == 'assign audio destination':
			for entry in cursor2:
				params = (Faudio_Folder+entry[2],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue

		elif process == 'assign Comics destination':
			for entry in cursor2:
				params = (Fcomic_Folder + entry[2],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'assign e-books destination':
			for entry in cursor2:
				params = (Fbooks_Folder + entry[2],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue

		elif process == 'assign Telegram destination':
			for entry in cursor2:
				params = (TelegramNoCasedest+entry[2],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'cleanfilenames':
			# Gets destination path, extract filename, cleans it and set result path and cleaned filename as destination.
			for entry in cursor2:
				folder= os.path.dirname(entry[3])
				filename, ext = os.path.splitext(os.path.basename(entry[3]))
				cleanedfilename = clearfilename(filename)
				newdest = os.path.join(folder,(cleanedfilename+ext))
				params = (newdest, entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		
		elif process == 'CleanDWtreefoldername':
			#Clear the destination tree folder, apply before assign a fullpath to destination.
			for entry in cursor2:
				folder= os.path.dirname(entry[3])
				filename = os.path.basename(entry[3])
				if folder != '':
					folder = clearfilename(folder)
				newdest = os.path.join(folder,filename)
				params = (newdest, entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		
		elif process == '(o>d)CopyTreeStructure':
			# Copy the origin structure to destination as is.
			for entry in cursor2:
				params = (entry[2], entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue

		elif process == 'moveupfileandrename':
			# (Valid when there is only one file to process)
			entry = cursor2.fetchone()
			folder= os.path.dirname(entry[3])
			filename , ext  = (os.path.splitext(entry[3]))
			if folder == '':
				folder = clearfilename(filename)
			params = (folder+ext, entry[0])
			con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'assign folder seriename':
			# Checks for a Serie name for the whole pack of files.
			# Is a serie name is found it will set as sub-folder name.
			seriecandidates = list ()
			FinalSeriename, conc = None, 0
			for entry in cursor2:
				filename0 , ext  = (os.path.splitext(os.path.basename(entry[3])))
				filename, Chap, Seriename = Chapterfinder (filename0)
				logging.debug ('Chapterfinder ({}) >> filename={}, Chap={}, Seriename={}'.format(filename0,filename,Chap,Seriename))
				if Seriename != None:
					seriecandidates.append (Seriename)
					serieconc = seriecandidates.count (Seriename)
					logging.debug ('Seriename candidate added: {}'.format(Seriename))
					if serieconc > conc:
						conc = serieconc
						FinalSeriename = Seriename
						logging.debug ('Seriename top candidate: {}, {} concurrences'.format(FinalSeriename,conc))
			logging.debug ('Selected Seriename: {}'.format(FinalSeriename))
			if FinalSeriename != None:
				cursor2 = con.execute("SELECT nreg, mime, originalfile, destfile FROM files WHERE trid = %s and wanted = 1"%Id)
				for entry in cursor2:
					filename0 , ext  = (os.path.splitext(os.path.basename(entry[3])))
					filename, Chap, Seriename = Chapterfinder (filename0)
					newdest = addslash(FinalSeriename) + filename + ext
					params = (newdest, entry[0])
					con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
					con.commit()
			continue

		elif process == 'deletenonwantedfiles':
			for entry in cursor2:
				if entry[1] == 'notwanted':
					con.execute("UPDATE files SET destfile = null, wanted = 0  WHERE nreg = ?", (entry[0],))
			con.commit()
			continue
		elif process == '(o)assign local path from videodest.ini' and TransmissionInbox != None:
			filmnamelist = set()
			for entry in cursor2:
				if entry[1] == 'video':
					filmnamelist.add(clearfilename(os.path.splitext(entry[2].split("/")[0])[0]))
					filmnamelist.add(clearfilename(os.path.splitext(entry[2].split("/")[-1])[0]))
			Subpath, maxmatch = "", 10
			Fvideodest = getaliaspaths(TransmissionInbox+"Videodest.ini")
			for filmname in filmnamelist:
				tmpSubpath, match = Getsubpath (filmname, Fvideodest)
				if match > maxmatch:
					Subpath , maxmatch = tmpSubpath, match
			if maxmatch > minmatch:
				logging.info ("\tFound alias for movie: " + Subpath + ".Aciertos:"+ str(maxmatch) )
				cursor3 = con.execute("SELECT nreg, destfile FROM files WHERE trid = ? and wanted = 1", (Id,))
				for Nreg, destfile in cursor3:
					con.execute("UPDATE files SET destfile = ? WHERE nreg = ?", (os.path.join(Subpath,destfile) ,Nreg))		
				con.commit()
			continue
	SpoolUserMessages(con, 6, Id)
	return

Psecuensedict = {
	0 : list(),  # It does nothing
	1 : ['(o>d)CopyTreeStructure','CleanDWtreefoldername','deletenonwantedfiles','moveupfileandrename','(o)assign local path from videodest.ini','assign video destination'],
	2 : ['(o>d)CopyTreeStructure','deletenonwantedfiles','(o)assign local path from videodest.ini','assign video destination',],
	3 : ['(o>d)CopyTreeStructure','CleanDWtreefoldername','assign audio destination','cleanfilenames'],
	4 : ['assign Telegram destination'],
	5 : ['assign Comics destination'],
	6 : ['assign e-books destination'],
	7 : ['assign audio destination','cleanfilenames'],
	8 : ['(o>d)CopyTreeStructure','assign folder seriename', 'cleanfilenames', 'deletenonwantedfiles','assign serie destination'],
	}

Casos = {
	0 : "There is no available case for this matrix",
	1 : "(video) Content is just one file and it is a video file. and it may have some NonWantedFiles.",
	2 : "(video) Contains 1 video file and at least a image file, at the same level.",
	3 : "(audio) Contains one or more audio files and at least a image file, at the same level.",
	4 : "Telegram downloaded file with no Case",
	5 : "(Comic) It has only one file and is a comic extension",
	6 : "(ebook) It has only one file and is a e-book extension",
	7 : "(audio) Contains one or more audio files, may contain some image files, and more that one level of folders.",
	8 : "(serie) Content has one or more series chapters, image-files and it may have some NonWantedFiles.",
	}

def Selectcase (matrix, inputtype, TRid=""):
	""" Selects a case to deliver the torrent files and an operational behaviour for files.
		operational behaviour is returned as a list of numbers's codes that operates on all the files for 
		the torrent.
		If no case is matched, it returns None.
		Actual Matrix properties:
			nfiles > count of files
			nvideos > count of videos.
			nseries > count of video series files
			naudios > count of audio files
			nnotwanted > count of non wanted files
			ncompressed > count of compressed files
			nimagefiles > count of image files
			nother > count of other files
			nbooks > count of book files
			ncomics > count of comic files
			nfolders > count of folder entries
			folderlevels > folder levels

		DefTest OK"""
	# Selectig case of only one video file:
	if matrix.nfiles >= 1 and matrix.nvideos == 1 and (matrix.naudios+matrix.ncompressed+matrix.nimagefiles+matrix.nother)==0:
		NCase = 1

	# Only one video with some image files.
	elif matrix.nfiles > 1 and matrix.nvideos==1 and (matrix.naudios+matrix.ncompressed)==0 and matrix.nother==0 and matrix.folderlevels==1:
		NCase = 2

	elif matrix.nfiles >= 1 and matrix.naudios>0 and (matrix.nvideos+matrix.nother)==0 and matrix.nfolders==1 and matrix.folderlevels==1:
		NCase = 3

	elif matrix.nfiles >= 1 and matrix.nvideos == 0 and matrix.naudios >= 1 and (matrix.ncompressed + matrix.nother + matrix.nbooks + matrix.ncomics) == 0 and matrix.nfolders>=1 and matrix.folderlevels > 1:
		NCase = 7

	elif matrix.nfiles == 1 and matrix.ncomics == 1:
		NCase = 5

	elif matrix.nfiles == 1 and matrix.nbooks == 1:
		NCase = 6

	# One or more series with some images or nonwanted files.
	elif matrix.nseries >= 1 and (matrix.naudios+matrix.ncompressed+matrix.nother+matrix.nvideos)==0 :
		NCase = 8

	elif inputtype == 'Telegram':
		NCase = 4

	else:
		NCase = 0

	logging.info ("({}) Selected case {} : {}".format(TRid, NCase, Casos[NCase]))
	
	return NCase, Psecuensedict[NCase]



def DeliverFiles():
	''' Check for 'Completed' entries and _deliverstatus_ = 'Added' in tw_inputs DB.
		Process files and do the movements.
		Once the move is done, field _deliverstatus_ is set to 'Delivered'
		'''
	con = sqlite3.connect (dbpath)
	cursor1 = con.cursor()
	cursor1.execute ("SELECT id, trname, fullfilepath, dwfolder, filetype from tw_inputs WHERE status = 'Completed' and deliverstatus = 'Added' ")
	for Id, Trname, Fullfilepath, Dwfolder, Filetype in cursor1:
		cursor2 = con.cursor()
		cursor2.execute ("SELECT nreg, originalfile, destfile, wanted from files WHERE trid = %s and status = 'Added' "%Id)
		for Nreg, originalfile, destfile, Wanted in cursor2:
			origin = addslash (Dwfolder) + originalfile
			if Wanted == 1:
				mode = 'c'
				if Filetype in ('.file','.folder'):
					mode = 'm'  # It's a Telegram input and need to be moved
				status = copyfile (origin, destfile, mode = mode)
			elif Filetype in ('.file', '.folder'):
				os.remove (origin)
				status = 'Deleted'
			else:
				continue
			con.execute ("UPDATE files SET status = ? WHERE nreg = ?",(status,Nreg))
		con.execute ("UPDATE tw_inputs SET deliverstatus = 'Delivered' WHERE id = %s"%Id)
		if Filetype == '.folder':
			CleanEmptyFolders (Fullfilepath)
		SpoolUserMessages(con, 7, TRid = Id)
		con.commit()
	con.close()
	return

def StartTRService ():
	con = sqlite3.connect (dbpath)
	Nactivetorrents = con.execute("SELECT count(status) FROM tw_inputs WHERE status = 'Added' and (filetype='.torrent' or filetype='.magnet')").fetchone()[0]
	if Nactivetorrents > 0:
		if not getappstatus(['transmission-gtk']):
			launchTR (cmd, 25)
			SpoolUserMessages(con, 9, None)
			con.commit()
			con.close()
		else:
			logging.info ('There are pending torrents to download, Transmission service is alive.')
	else:
		logging.info('There are no pending torrents in Database to continue downloading in Transmission Service')
	return

def Relatedcover(item):
	''' Return the possiblecovers for an item name plus .jpg or .png form.
		input filename >> outputt filename
		DEFTEST....OK!!'''
	possiblecovers = set ()
	basename = os.path.splitext(item)[0]
	if chapid (basename) != '':
		basename = basename[:-2]
	for i in ['.jpg','.png']:
		possiblecovers.add(basename+i)
	return possiblecovers

def VideoSACFilelist (folderpath):
	dirlist = lsdirectorytree (folderpath)
	filemovieset = set ()
	for entry in dirlist:
		ficheros = os.listdir (entry)
		paraañadir = set ()
		for a in ficheros:
			item = os.path.join(entry,a)
			if itemcheck (item) == 'file':
				if fileclasify(item) == 'video':
					add = True
					for i in Relatedcover (item):
						basename = os.path.splitext(i)[0]
						if itemcheck (i) == 'file':
							add = False
					if add == True:
						filemovieset.add (basename+os.path.splitext(item)[1])
				
	return filemovieset

def listcovers(path):
	''' Return a list of covers-files
	input: relative path, or full-path
	output: list of image-files with relative or full-path
		'''
	path = addslash (path)
	lista = os.listdir(path)
	lista2 = list()
	for a in lista:
		if itemcheck(path+a) == 'file' and fileclasify (path+a) == 'image':
			lista2.append(a)
	return lista2

def selectcover (film,Coversinbox):
	''' This function evaluates a suitable cover for a filemovie based on its filename.
		it scans in a folder the most suitable cover based on cover filenames and returns this match

		Returns "" if no covers were found.
		
		input: film.extension
		input: /path/to/repository_of_covers
		'''
	logging.debug("\tSearching a cover for: "+film)
	coverlist33 = listcovers(Coversinbox)
	slcover, match = matchfilm(film,coverlist33)
	if slcover == '' or match <= minmatch:
		slcover = ''
	return slcover

def CoverService (Fmovie_Folder, Availablecoversfd, inivideodest):
	logging.debug ('CoverService Started')
	Folderset = set()
	if itemcheck(inivideodest) == 'file':
		aliaspaths = getaliaspaths(inivideodest)
		for key in aliaspaths:
			Folderset.add( os.path.join(Fmovie_Folder[:-1],aliaspaths[key]))
	Folderset.add (Fmovie_Folder[:-1])
	filemovieset = set ()
	for folder2scan in Folderset:
		if  itemcheck (folder2scan) == 'folder':
			subset = VideoSACFilelist (folder2scan)
			for i in subset:
				filemovieset.add(i)
		else:
			LogOnce ('CSVC', folder2scan, msg='(coverservice):Folder %s does not exist.'%folder2scan, action='print')
	coverperformer (filemovieset, Availablecoversfd)

def coverperformer(filemovieset,Availablecoversfd):
	''' Assign cover files and moves matched cover next to the film file.
		input should be a list, but also a string with a /path/to/filename.ext is possible
		'''
	if type (filemovieset) == str():
		filemovieset = [filemovieset,]
	for entry in filemovieset:
		filmname = os.path.basename(entry)
		slcover = selectcover (filmname,Availablecoversfd)
		if slcover == '':
			logging.debug("\tNo covers found for %s"%filmname)
			continue
		else:
			logging.debug("\tA cover were found for %s"%filmname)
			origin = os.path.join(Availablecoversfd,slcover)
			dest = os.path.join(os.path.splitext(entry)[0]+os.path.splitext(slcover)[1])
			shutil.move(origin,dest)
			logging.debug("\t\tfrom %s >> %s"%(origin,dest))
			con = sqlite3.connect (dbpath)
			Trid = con.execute ("SELECT trid from files WHERE destfile = '%s' and status = 'Copied' ORDER BY added_date DESC"%entry).fetchone()
			if Trid != None:
				logging.info('A cover was assigned to a torrent file-movie: Trid=%s'%Trid)
				Trid = Trid[0]
			SpoolUserMessages(con, 11, Trid)
			con.commit()

	return

def RetentionPService(tc):
	if MaxseedingDays == None:
		logging.debug ('Retention Policy Service deactivated by user option')
		return
	MaxseedingDays_dt = datetime.timedelta(days=MaxseedingDays)
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	timedellist = list ()
	MinimunSpaceRemoveList = list()
	for trr in tc.get_torrents():
		try:
			DBid, Deliverstatus = cursor.execute ("SELECT id, deliverstatus from tw_inputs WHERE hashstring = ? and (status = 'Ready' or status = 'Added' or status = 'Completed') ", (trr.hashString,)).fetchone()
		except TypeError:
			msg = 'This torrent is not beign tracked at Database, it may be queued: %s,%s'%(trr.hashString, trr.name)
			logging.warning (msg)
			print (msg)
			continue
		if DBid == None:
			logging.warning('Active torrent is not being tracked on DB: %s'%trr.name)
			continue

		# DBid exists, it means that the torrent is beign tracked on the DataBase
		elif trr.seed_ratio_mode == 'unlimited' or (trr.seed_ratio_mode == 'global' and not tc.session.seedRatioLimited):
			LogOnce('RPSF',DBid,"({}) Retention policy does not apply to torrents that seeds forever: {}".format(DBid, trr.name), 'Print')
			continue
		elif trr.doneDate == 0:
			LogOnce('RPMT',DBid,"({}) Retention policy does not apply to unfinished torrents: {}".format(DBid, trr.name), 'Print')
			continue
		elif Deliverstatus == None:
			LogOnce('RPNMC',DBid,"({}) Retention policy does not apply to Torrents that has no match Case: {}".format(DBid, trr.name), 'Print')
			#you can stablish a retention policy for this torrents here, or delete them manually.
			continue

		elif Deliverstatus == 'Delivered':
			# This torrents have been delivered to another location. You can delete them due to a retention policy defined here:
			if trr.isFinished or (trr.status in ['seeding','stopped'] and trr.progress >= 100 and now > (trr.date_done + MaxseedingDays_dt)):
				logging.info ('Torrent %s in DB is going to be deleted due to a time retention policy: (%s)'%(DBid, trr.name))
				timedellist.append ((trr.id, DBid))
				'''
				print ('trr.isFinished:',trr.isFinished)
				print ('trr.date_active:',trr.date_active)
				print ('trr.date_done:',trr.date_done)
				print ('trr.ratio:',trr.ratio)
				print ('trr.seed_ratio_limit:',trr.seed_ratio_limit)
				print ('Is going to be deleted on:',trr.date_done + MaxseedingDays_dt)
				print (now > (trr.date_done + MaxseedingDays_dt))
				print (trr.doneDate)
				print (trr.id)
				print ('\n')
				'''
			else:
				#The next lisst of identifiers (MinimunSpaceRemoveList) is used 
				# in case of some torrent must to be deleted due to free space
				MinimunSpaceRemoveList.append((trr.id, DBid))

		LogOnce (['RPSF', 'RPMT', 'RPNMC'], DBid, action = 'Reset')

	for trr_id, DBid in timedellist:
		Removetorrent (tc, con, trr_id, DBid, sendtoTrash=False)
		
	Dwdir = tc.get_session().download_dir
	while shutil.disk_usage (Dwdir).free < MinSpaceAtTorrentDWfolder:
		if len(MinimunSpaceRemoveList) == 0:
			freetextspace = toHumanSizeReadable(shutil.disk_usage (Dwdir).free)
			msgx = 'Download dir is running into low disk space: %s available'%freetextspace
			if LogOnce ('RILS',freetextspace, msg = msgx, action='Print'):
				STmail ('System is running into low space', msgx, topic=12)
			break
		else:
			# LogOnce ('RILS',1, action = 'Reset')
			LogOnceDict ['RILS'] = set()

		candidate_idtuple = tuple()
		maxpoint = 0
		for trr_id, DBid in MinimunSpaceRemoveList:
			trr = tc.get_torrent(trr_id)
			sizepoints = (trr.sizeWhenDone / MinSpaceAtTorrentDWfolder) *100 * 3
			timepoints = ((now - trr.date_done).days /MaxseedingDays) *10
			progresspoints = trr.ratio *3
			points = sizepoints + timepoints + progresspoints  # evaluate points in order to Size and days remaining seeding
			if points > maxpoint:
				candidate_idtuple = (trr_id, DBid, trr.name)
				maxpoint = points

		trr_id, DBid, trr_name = candidate_idtuple
		MinimunSpaceRemoveList.remove ((trr_id,DBid))
		Removetorrent (tc, con, trr_id, DBid, sendtoTrash=False)
		print ('\tthis torrent has been deleted in ordder to gain free space (%s)'%DBid)
		logging.info ('\tTorrent (%s) in DB has been deleted from Transmission Service for gain free space.'%DBid)
	con.close()
	return

def Telegramfd (Tfolder):
	""" Checks a folder content and returns it to be added to process.
		As content for this folders usually are downloaded or copied,
		this function will check the size and the last modification time in order to
		return the pack.
		It will treat folders and files as inputs.
		compressed files will be ignored, as they sometimes are multifile and have passwords.
		"""
	Itemlist = list()
	filelist = [os.path.join(Tfolder,i) for i in os.listdir(Tfolder)]
	for entry in filelist:
		entrytype = None
		if os.path.isdir (entry):
			if folderinuse (entry):
				logging.info("Detected incoming folder job %s, it was not processed because some of their content was in use." %entry)
				continue
			entrytype = '.folder'
		elif os.path.isfile (entry):
			extension = os.path.splitext(entry)[1].lower()
			if extension in ('.zip','.7z'):
				logging.info("Detected job %s was not processed because it is not a rar compressed file." %entry)
				continue
			elif fileinuse (entry) == True:
				logging.info("Detected job %s was not processed because it were open by an application." %entry)
				continue
			elif extension == '.rar':
				LogOnce ('DRARJob', entry, msg="Detected a .rar job:"+ entry, action = 'log')
				entrytype = extension
			else:
				entrytype = '.file'
		if entrytype != None:
			Itemlist += [(entry,entrytype),]
		else:
			logging.warning ('This job was discarded: %s'%entry)
	return Itemlist

def PreProcessReadyTelegramInputs ():
	""" Pre-Process Ready Telegram Inputs, sets the downloaded folder and sets status = Added in Database
		now the input is ready to retrieve and pre-asign the files."""
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, fullfilepath, filetype from tw_inputs WHERE status = 'Ready' AND (filetype = '.file' OR filetype = '.folder')")
	for DBid, Fullfilepath, Filetype in cursor:
		Basedir = os.path.dirname(Fullfilepath)
		con.execute ("UPDATE tw_inputs SET status='Added', dwfolder = ? WHERE id = ?", (Basedir,DBid))
	con.commit()
	con.close()
	return

def RetrieveTelegramInputfiles():
	""" Retrieve the input files and do the Pre-deliver process,
		only for telegram inputs.
		"""
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, fullfilepath, filetype, dwfolder FROM tw_inputs WHERE filesretrieved IS NULL and status = 'Added' AND (filetype = '.file' OR filetype = '.folder')")
	cursorFreeze = list()
	for entry in cursor:
		cursorFreeze.append(entry)
	for DBid, Fullfilepath, Filetype, Dwfolder in cursorFreeze:
		filesdict = Retrievefilesdict (Fullfilepath, Filetype)
		if len(filesdict) == 0:
			logging.warning ("Thereis no files for this entry: %s"%Fullfilepath)
		AddFilesToDB (con, DBid, filesdict, 'Telegram')
		cursor.execute ("UPDATE tW_inputs SET status = 'Completed' WHERE id = %s"%DBid)
		con.commit ()
	con.close ()
	return

def CleanEmptyFolders (upperfolder):
	upperparent = os.path.dirname (upperfolder)
	foldercollection = lsdirectorytree (upperfolder)
	logging.info ('\tChecking empty folders to delete them')
	foldercollectionnext = set()
	while len(foldercollection) > 0:
		for i in foldercollection:
			logging.info ('checking: %s' %i)
			if itemcheck(i) != 'folder':
				logging.warning ('\tDoes not exists or is not a folder. Skipping')
				continue		
			if len (os.listdir(i)) == 0:
				if i != upperparent:
					shutil.rmtree (i)
					infomsg = "\tfolder: %s has been removed. (was empty)" % i
					logging.info (infomsg)
					foldercollectionnext.add (os.path.dirname(i))
					logging.debug ("\tadded next level to re-scan")			
		foldercollection = foldercollectionnext
		foldercollectionnext = set()
	return

def Removetorrent (tc, con, trr_id, DBid, sendtoTrash=True):
	'''given an transmission's torrent id, DBid
	it deletes the torrent from transmission service, it sets the entry in DB as Deleted
	and if complete=True and there is a known usertrash, it deletes from the HD
		'''
	torrentname = tc.get_torrent(trr_id).name
	tc.remove_torrent(trr_id, delete_data=True, timeout=None)
	con.execute ("UPDATE tw_inputs SET status='Deleted' WHERE id = %s"%DBid)
	print ('Torrent deleted: '+ torrentname)
	logging.info ('\tTorrent %s in DB has been deleted from Transmission Service: %s'%(DBid,torrentname))
	SpoolUserMessages(con, 10, TRid = DBid)
	con.commit()
	if not sendtoTrash and usertrash != False:
		packtodelete = os.path.join(usertrash, torrentname)
		indextodelete = os.path.join(usertrash, '../info',torrentname+'.trashinfo')
		deleteindex = True

		if itemcheck (packtodelete) == 'folder':
			shutil.rmtree (packtodelete)
		elif itemcheck (packtodelete) == 'file':
			os.remove (packtodelete)
		else:
			deleteindex = False
			logging.warning('I could not delete this pack from the Trash folder:' + packtodelete)
		if itemcheck (indextodelete) == 'file' and deleteindex == True:
			os.remove (indextodelete)
	return

def PreProcessReadyRARInputs():
	''' Checks 'Ready' .rar files at DB and set them to 'Added' if all rar's volume files are available.
		'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, fullfilepath from tw_inputs WHERE status = 'Ready' AND filetype = '.rar'")
	rarentrydict = dict()
	for DBid, Fullfilepath in cursor:
		if itemcheck (Fullfilepath) != 'file':
			con.execute ("UPDATE tw_inputs SET status='Deleted' WHERE id = ?", (DBid,))
			logging.warning ("RAR File at entry (%s) have been removed."%DBid)
			LogOnce ('RFNP', DBid, action = 'Reset')
		else:
			rarentrydict[Fullfilepath] = DBid

	CompleteDBids = list()
	headerrars = list()
	cursor.execute ("SELECT id, fullfilepath from tw_inputs WHERE status = 'Ready' AND filetype = '.rar'")
	for DBid, entry in cursor:
		try:
			rf = rarfile.RarFile(entry)
		except rarfile.NeedFirstVolume:
			logging.debug ('Skipping a non start rar volume:%s'%entry)
			continue
		else:
			headerrars.append (DBid)
			basedir = os.path.dirname(entry)
			toaddvolumelist_id = list()
			toaddflag = True
			for vfile in rf.volumelist():
				pointer = os.path.join(basedir,vfile)
				if pointer in rarentrydict:
					toaddvolumelist_id.append (rarentrydict[pointer])
				else:
					toaddflag = False
					break
			if toaddflag == True:
				##  Check rar file, because rf.volumelist is not the expected complete volume list, just the actual files found in folder by order.
				## I need to check the rar file.
				if not rf.needs_password():
					try:
						rf.testrar()
					except rarfile.RarCRCError:
						logging.warning ('Rar file has errors or it is incomplete:'+ entry)
					else:
						for i in toaddvolumelist_id:
							CompleteDBids.append (i)
				else:
					msg = '(%s) This rar file needs password: %s'%(DBid,entry)
					LogOnce ('RFNP', DBid, msg = msg, action='Print')


	for DBid in CompleteDBids:
		dwfolder = None
		if DBid in headerrars:
			dwfolder = basedir
		con.execute ("UPDATE tw_inputs SET status='Added', dwfolder = ? WHERE id = ?", (dwfolder,DBid))
	con.commit()
	con.close()
	return CompleteDBids

def UncompressRARFiles():
	''' Checks 'Added' rar files at DB and decompress them.
		Finally, mark them as status:Completed / deliverstatus:Delivered
		and delete them from HD
		'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, fullfilepath, dwfolder from tw_inputs WHERE status = 'Added' AND dwfolder is not null AND filetype = '.rar'")
	for DBid, Fullfilepath, Dwfolder in cursor:
		rf = rarfile.RarFile (Fullfilepath)
		if rf. needs_password():
			# send e-mail 
			logging.info ('(%s) This RAR file needs password to be decompressed:%s'%(DBid,Fullfilepath))
			remove = False
		else:
			print ('Decompressing:','(',DBid,')',Fullfilepath)
			rf.extractall(path=Dwfolder, pwd=None)
			remove = True
		for vfile in rf.volumelist():
			con.execute ("UPDATE tw_inputs SET status='Completed', deliverstatus='Delivered' WHERE fullfilepath = ? AND status = 'Added'", (vfile,))
			if remove:
				os.remove (vfile)
			else:
				shutil.move (vfile, os.path.join(TelegramNoCasedest,os.path.basename(vfile)))
				print (vfile, os.path.join(TelegramNoCasedest,os.path.basename(vfile)))
				exit
	con.commit()
	con.close()
	return

# ========================================
# 			== MAIN PROCESS  ==
# ========================================
if __name__ == '__main__':
	StartTRService ()
	while True:
		if TransmissionInbox != None:
			Dropfd (Availablecoversfd, ["jpg","png","jpeg"])  # move incoming user covers to covers repository
			Hotfolderinputs = [(i,".torrent") for i in Dropfd (Torrentinbox, ["torrent",])]
			if len (Hotfolderinputs) > 0:
				addinputs (Hotfolderinputs)

		if Telegraminbox != None:
			Hotfolderinputs = Telegramfd (Telegraminbox)
			if len (Hotfolderinputs) > 0:
				addinputs (Hotfolderinputs)
			if RarSupport == True:
				PreProcessReadyRARInputs ()
				if getappstatus (['mplayer','vlc']) == False:
					UncompressRARFiles ()

			PreProcessReadyTelegramInputs ()
			RetrieveTelegramInputfiles ()

		SendtoTransmission ()

		if getappstatus (players) == False:
			DeliverFiles ()
		else:
			logging.warning ('Some videoplayer is currently running, I will not deliver any files.')

		if TransmissionInbox != None and len(listcovers(Availablecoversfd))>0 :
			CoverService (Fmovie_Folder, Availablecoversfd, TransmissionInbox+"Videodest.ini")
		
		if getappstatus(['transmission-gtk']):
			tc = connectTR ()
			TrackManualTorrents (tc)
			TrackDeletedTorrents(tc)
			TrackFinishedTorrents (tc)
			RetrieveTorrentFiles (tc)
			RetentionPService (tc)

		MsgService ()

		logging.debug("# Done!, next check at "+ str (datetime.datetime.now()+datetime.timedelta(seconds=s)))
		print ('\n'+'='*20)
		time.sleep (s)
