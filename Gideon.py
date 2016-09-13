#!/usr/bin/python3
# -*- encoding: utf-8 -*-

''' This program is intended to process torrents.
	
	Program main functions:

	Checks contents of Torrent.spoolfile
	Checks contents of downloaded torrents,
	Stores downloaded files due to its nature and contents at pre configured folder/s.
	Renames files by cleans filenames.
	It can find and select the most suitable cover from a folder and match to its videofile, so Freevo can read it as its cover.
	It can detect chapter-numbers at the end of the file/s, rename then as nxnn so Freevo can group videofiles as chapters.
	Scans videofiles properties and stores their information into a log file. (You'l need to install mplayer).
	As videofiles can be scanned, they can be stored at a tmp-folder, placed this entry into a queue and send a warning e-mail. (Useful if your Hardware freezes playing videos and you need to recompress them, usually into a xVid codec)
	It can process this queue of videofiles and recompress automatically to a given codec without loosing its final deliver path. Youl'l need avidemux to do that.
	It can send e-mails to notify some processes. You'l need to config your mail account.

	Logs are stored in a single Gideon.log file.

	You need to set up GideonConfig.py first. o run this program for the first time.
	'''

# Standard library module import
import os, sys, shutil, logging, datetime, time, smtplib, re
from email.mime.text import MIMEText  # for e-mail compose support
from subprocess import check_output  # Checks if transmission is active or not
import sqlite3  # for sqlite3 Database management

# Specific library module import
import transmissionrpc  # transmission rpc API
dyntestfolder = 'TESTS'


__version__ = "2.0alfa"
__author__ = "pablo33"


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
		# print ('\n\n\n','nueva iteración', moredirectories)
		for a in newdirectories:
			# checking for items (child directories)
			# print ('Checking directory', a)
			añadir = addchilddirectory (a)
			#adding found items to moredirectories
			for b in añadir:
				moredirectories.append (b)
		#adding found items to dirlist
		for a in moredirectories:
			dirlist.append (a)
	return dirlist

def addchilddirectory (directoriy):
	""" Returns a list of child directories
	Usage: addchilddirectory(directory with absolute path)"""
	paraañadir = []
	ficheros = os.listdir (directoriy)
	for a in ficheros:
		item = directoriy+'/'+a
		if os.path.isdir(item):
			paraañadir.append (item)
	return paraañadir

def folderinuse (folder):
	""" Scans a folder for files.
			Returns True if any file is in use (is being writted)
			Otherwise returns False
		(DefTest in TestPack3)
		"""
	folder = addslash(folder)
	folderlist = lsdirectorytree (folder)
	for a in folderlist:
		filelist = [(folder + i) for i in os.listdir(a)]
		for entry in filelist:
			if os.path.isfile (entry):
				if fileinuse (entry):
					return True
	return False



# .. Default Videodest.ini file definition (in case there isn't one)
startVideodestINIfile = """
# Put this file into Dropbox/TRinbox
#	
#	define a destination with some words to automatically store file-movies to the right place.
#	
#	Those paths are relative to Videodest default path (defined in Fmovie_Folder var (at GideonConfig.py))
#	

__version__ = 1.1
__date__ = "11/04/2015"

# You can define alias for common destinations, to substitute text 
alias=Series        ,    /series/
alias=Sinfantiles   ,    /Series infantiles/

# Define destinations:
#	guess a title to match the filemovie then,
#   define a relative path to store it (starting at default "filemovie folder" defined in GideonConfig.py file) 
#	(you can use alias enclosed in <....> to replace text, but remember that you must define them first)
#  Those are examples, please replace them and follow the structure.
#  Please, do not include comments at the end of alias or dest lines. This is not an python file.
#  
dest = star wars rebels, <Sinfantiles>
dest = Sleepy Hollow temporada 2, <Series>Sleepy Hollow Temp 2
dest = Sleepy Hollow temporada 1, <Series>Sleepy Hollow Temp 1

# EOF
"""


# .. Default GideonConfig(generic).py file definition (in case there isn't one)
DefaultConfigFile = """
''' Config file of Gideon
	'''

__version__ = 2.0
__date__ = "26/07/2016"
__author__ = "pablo33"


# Setting variables, default paths to store processed files.
Fmovie_Folder = "/home/user/movies/"  # Place to store processed movies
Faudio_Folder = "/home/user/audio/"  # Place to store processed music
Hotfolder = "/home/user/Dropbox/TRinbox/"  # (input folder) Place to get new .torrents and .jpg .png covers. (this files will be moved to Torrentinbox folder) Note that you should install Dropboxbox service if you want deposit files there.
Telegraminbox = None  #  "/home/user/Downloads/Telegram/"  # (input folder) Place to get new files and folders to process. Use this if you want to Gideon to process an incoming file.
TelegramNoCasedest = "/home/user/Downloads/"  # Destination file where telegram files goes if no Case is found.


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
#	11:	'Cover assigned to a moviefile',


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
logging.debug("======================================================")
logging.debug("================ Starting a new sesion ===============")
logging.debug("======================================================")


# (1.5) Setting main variables
Fmovie_Folder = addslash(GideonConfig.Fmovie_Folder)  # Default place to store movies
Faudio_Folder = addslash(GideonConfig.Faudio_Folder)  # Default place to store music
Hotfolder = addslash (GideonConfig.Hotfolder)  # Hotfolder to retrieve user incoming files, usually a sycronized Dropbox folder
Telegraminbox = addslash (GideonConfig.Telegraminbox)  # Hotfolder to retrieve Telegram Downloaded files or whatever other files
TelegramNoCasedest = addslash (GideonConfig.TelegramNoCasedest)  # Telegram files with no Case goes here, preserving the file/folder structure

s =  GideonConfig.s # Time to sleep between checks (Dropbox folder / transmission spool)
cmd  = GideonConfig.cmd # Command line to lauch transmission
lsdy = GideonConfig.lsdy # List of hot folders to scan for active or new file-torrents
TRmachine = GideonConfig.TRmachine
TRuser = GideonConfig.TRuser
TRpassword = GideonConfig.TRpassword
MaxseedingDays = GideonConfig.MaxseedingDays
mail_topic_recipients = GideonConfig.mail_topic_recipients

minmatch = 15  # Points to match files and cover names
players = ['mplayer','vlc']


Msgtimming = {
	'low': datetime.timedelta(seconds=3600),
	'med':datetime.timedelta(seconds=600),
	'high':datetime.timedelta(seconds=0)
	}
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
}

Codemimes = {
	'video' : 1,
	'audio' : 2,
	'notwanted' : 3,
	'compressed' : 4,
	'image' : 5,
	'other' : 6,
}


# (1.6) Prequisites:
#=============

if itemcheck (Hotfolder) != 'folder' :
	print ('\tHotfolder does not exist: %s'%Hotfolder)
	print ('\tIf you want to use this inbox service,')
	print ('\tplease edit your user configuration file at: \n',  userconfig)
	print ('\tor create this configured path to start using it.')

	Hotfolder = None  # This prevent using this Service.

# Checking and setting up Fvideodest file:
if Hotfolder != None:
	if startDefaultFile (startVideodestINIfile, Hotfolder + "Videodest.ini") == True:
		print ("Don't forget to customize Videodest.ini file with video-destinations to automatically store them into the right place. More instructions are available inside Videodest.ini file.")





# (1.7) Checking DB or creating it:
#=============

if itemcheck (dbpath) == "file":
	logging.info ('Database found at %s'%(dbpath))
else:
	logging.info ('Database not found, creating an empty one')
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
		filesretrieved integer DEFAULT (0),\
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
		naudios int ,\
		nnotwanted int ,\
		ncompressed int ,\
		nimagefiles int ,\
		nother int ,\
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

def removeitems(items):
	""" Removes a list of items (files)
		items can be absolute or relative path
		input: List of items,  (/path/to/file.ext)
		output: none
		"""
	logging.info("## removing items....")
	for a in items:
		logging.debug("Deleting:"+a)
		os.remove(a)
		logging.info("Deleted:"+a)

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
				logging.debug("Found "+var+" definition line")
				logging.debug("Splitting: "+line[:-1])
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
				logging.debug("Found: %s %s %s" %(a,param,b))
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
			# If there is a Chapter id. we do not want to loose it >> so trim = 0
			for i in GideonConfig.chapteridentifier :
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
		leters = "1234567890abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ-+*()[]_"
		while True :
			logging.debug(a)
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

	for pw in lista:
		# words in the middle
		x = a.upper().find(" "+pw.upper()+" ")
		if x >= 0:
			a = a[:x]+a[x+len(pw)+1:]
		# words at the end
		if len (pw)+1 < len (a):
			if a.upper().endswith(" "+pw.upper()):
				a = a[:-len(pw)-1]
		# words at the begining
		if len (pw)+1 < len (a):
			if a.upper().startswith(pw.upper()+" "):
				a = a[len(pw)+1:]
	return a

def sigcapfinder(filename):
	""" This little Function, scans for a chapter-counter at the end of the 
		filename, it will delete any punctuation character at the end and 
		it will also try to find numbers at the end of the filename. 
		If filename ends in three numbers, it'll change 'nnn' to 'nxnn'.
		This not affects if filename ends in four or more numbers. 'nnnn' so they are treated as a 'year'
		for example:

		sigcapfinder("my title 123") returns>> "my title 1x23"
		sigcapfinder("my title 123-[[[") returns>> "my title 1x23"
		sigcapfinder("my title ending in a year 1985") returns "my title ending in a year 1985"
	DefTest >> OK	"""
	if filename == "":
		logging.warning("Empty filename to find chapter!")
		return filename
	base = filename
	# chapter = 0 # for now, we assume there isn't any chapter in filename.
	# we trim not wanted characters at the end:
	count = 0
	for a in base[::-1]:
		if a in '[]-:,*+_.':
			count +=1
			continue
		break
	if count != 0:
		base = base [0:-count]		
		logging.debug("namebase has changed to "+base)
	if base == "" or len(base) < 5:
			logging.warning("filename made of simbols or very short, returning same filename")
			return filename
	
	# finding a final identifier, cleaning odd chars before capter
	expr = '[-. ]\d[xX]\d{2}'
	mo = re.search (expr, base[-5:])
	try:
		grupo = mo.group()
	except:
		pass
	else:
		base = base[:-5]+' '+base[-4:]
		return base


	# finding 3 final numbers
	expr = '[-. ]\d{3}'
	mo = re.search (expr, base[-4:])
	try:
		grupo = mo.group()
	except:
		pass
	else:
		base = base[:-4]+' '+base[-3:-2]+'x'+base[-2:]
	return base

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
	words = ["in","to","my","the","and","on","at","of","en","a","y","de","o","el","la","los","las","del", "lo", "es"]
	for a in words:
		wa=" "+a[0].upper()+a[1:]+" "
		wb=" "+a+" "
		filename = filename.replace(wa,wb)
	return filename

def clearfilename(filename):
	""" Process several filters for filename cleaning
		input: filename without extension, please
		output: filename without extension, of course
		"""
	logging.debug("# Cleaning filename: "+filename)
	filenametmp = filename

	
	#1 replacing dots, underscores & half  between leters.
	filenametmp = dotreplacement(filenametmp, ". ")
	filenametmp = dotreplacement(filenametmp, "_ ")
	filenametmp = dotreplacement(filenametmp, "- ")

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
	filenametmp = sigcapfinder(filenametmp)

	#7 Formatting as Title Type
	filenametmp = filenametmp.title()

	#8 Replacing little words to lowerCase
	filenametmp = littlewords (filenametmp)
	
	return filenametmp

# Main Functions -------------------------

def copyfile(origin,dest,mode="c"):
	""" Copy or moves file to another place
		input: file origin (full/relative patn and name)
		input: file destination (full/relative path an name)
		input: mode: "c" for copy, "m" for move (default "c")

		if a file already exists, nothing is done.
		return True if success, or False if it didn't success
		"""
	if itemcheck(origin) == "":
		logging.debug("\tOrigin file does not exists. Nothing to do!")
		return 'Missed'
	if itemcheck(dest) == "":
		makepaths ([os.path.dirname(dest),])
		if mode == "c":
			shutil.copy(origin,dest)
			return 'Copied'
		if mode == "m":
			shutil.move(origin,dest)
			return 'Moved'
	else:
		logging.debug("\tDestination file already exists")
		return 'Exists'

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
		output: 'other' (default), 'audio', 'video', 'movie', 'compressed', 'image'
		
		DefTest OK"""
	global GideonConfig
	ext = os.path.splitext(filename)
	if str(ext[1]) in ['','.']:
		print ('>>>>',filename)
		logging.warning('File has no extension: %s'%filename)
		return 'other'
	extwd = str (ext [1])
	extwd = extwd [1:]
	if extwd in GideonConfig.ext['video']: return 'video'
	elif extwd in GideonConfig.ext['audio']: return 'audio'
	elif extwd in GideonConfig.ext['compressed']: return 'compressed'
	elif extwd in GideonConfig.ext['notwanted']: return 'notwanted'
	elif extwd in GideonConfig.ext['image']: return 'image'
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
	movelist = extfilemove (Hotfolder, destfolder, lsextensions)
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
		'''
	if len (entrieslist) > 0:
		con = sqlite3.connect (dbpath)
		cursor = con.cursor()
		for Entry, Filetype in entrieslist:
			if cursor.execute ("SELECT count (id) from tw_inputs where fullfilepath = ? and status = 'Ready'", (Entry,)).fetchone()[0] == 0:
				cursor.execute ("INSERT INTO tw_inputs (fullfilepath, filetype) VALUES (?,?)", (Entry,Filetype))
				logging.info ('added incoming torrent to process: %s' %Entry)
				Id = (con.execute ('SELECT max (id) from tw_inputs').fetchone())[0]
				SpoolUserMessages(con, 1, TRid = Id)
				con.commit()
		con.close()
	return

def launchTR (cmdline, seconds=0):
	os.system(cmdline)
	logging.info ('Transmission have been launched.')
	time.sleep(seconds)
	return

def connectTR():
	if not getappstatus(['transmission-gtk']):
		launchTR (cmd, 5)
	tc = transmissionrpc.Client(address=TRmachine, port = '9091' ,user=TRuser, password=TRpassword)
	logging.debug('A Transmission rpc session has started')
	print ('Started rpc session')
	return tc

def SendtoTransmission():
	con = sqlite3.connect (dbpath) # it creates one if it doesn't exists
	cursor = con.cursor() # object to manage queries
	nfound = (cursor.execute ("SELECT count(id) FROM tw_inputs WHERE status = 'Ready' and ( filetype = '.magnet' or filetype = '.torrent') ").fetchone())[0]
	if nfound > 0:
		logging.info (str(nfound) + 'new torrent entries have been found.')
		tc = connectTR ()
		cursor.execute ("SELECT id, fullfilepath FROM tw_inputs WHERE status = 'Ready'  and ( filetype = '.magnet' or filetype = '.torrent')")
		for Id, Fullfilepath in cursor:
			trobject = tc.add_torrent (Fullfilepath)
			TRname = trobject.name
			TRhash = trobject.hashString
			con.execute ("UPDATE tw_inputs SET status='Added',  hashstring = ? , trname=? WHERE id=?", (TRhash, TRname,str(Id)))
			SpoolUserMessages(con, 2, TRid = Id)
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

def TrackDeletedTorrents(tc):
	''' Check if 'Added' torrents in DB are still in Transmission.
		If an entry is not present, it will be mark as 'Deleted'
		'''
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, hashstring from tw_inputs WHERE status = 'Added' or status = 'Completed'")
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
	cursor.execute ("SELECT id, hashstring from tw_inputs WHERE status = 'Added'")
	for DBid, HashString in cursor:
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
	msgto = ":".join(getrecipients(topic, mail_topic_recipients))
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
	mailaddedtorrents (con)
	mailpreasignedtorrents (con)
	mailcomplettedtorrents (con)
	mailRPolicytorrents (con)
	con.close()
	return

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
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' AND msg_inputs.topic = 1 AND ( filetype = '.torrent' OR filetype = '.magnet')")
	for Nreg, Trid, Trname in cursor:
		msg = """A new torrent has been sent to Transmission Service for Downloading:
	Torrent Name:
	%s
	
	It will be tracked as nº:%s in Database.""" %(Trname,Trid)
		STmail ('Added to Transmission ' + Trname, msg, topic=1)
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
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

def mailcomplettedtorrents(con):
	''' e-mail Completed torrents, this is to inform that a torrent have been processed
	usually corresponds with the preasigned destinations.
	It could contain other info of the torrent process.
	It corresponds with topic nº7 in DB, "Files have been processed and copied into destination"
	It should send one e-mail for each torrent file.
	The body should have "torrent ID in database for further information." >> Trid = ...
	'''
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' and msg_inputs.topic = 7")
	for Nreg, Trid, Trname in cursor:
		NCase = con.execute ("SELECT caso FROM pattern WHERE trid=%s"%Trid).fetchone()[0]
		if NCase > 0:
			msgbody = "A torrent has been Delivered to its destination: \n\
				Torrent Name: %s \n\
				trid = %s \n\
				Case = %s \n\n \
			Files movements:\n"%(Trname, Trid, Casos[NCase])

			filelisttxt, nonwantedfilestxt = getfiledeliverlistTXT (con,Trid)
			msgbody += filelisttxt + "\n"
			msgbody += nonwantedfilestxt + "\n"
			STmail ('Torrent completted and delivered: '+ Trname ,msgbody, topic=7)
		else:
			msgbody = "A torrent has been Downloaded: \n\
				Torrent Name: %s \n\
				trid = %s \n\
				Case = %s \n\n \
			It remains in Transmission default Download folder:\n"%(Trname, Trid, Casos[NCase])

			filelisttxt = getfileoriginlistTXT (con,Trid)
			msgbody += filelisttxt + "\n"
			# msgbody += gettorrentstatisticsTXT ()
			STmail ('Torrent is completted: '+ Trname ,msgbody, topic=7)
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
	It should send one e-mail for each torrent file.
	The body should have "torrent ID in database for further information." >> Trid = ...
	'''
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.status = 'Ready' and msg_inputs.topic = 6")
	for Nreg, Trid, Trname in cursor:
		NCase = con.execute ("SELECT caso FROM pattern WHERE trid=%s"%Trid).fetchone()[0]
		msgbody = "A new torrent has been preasigned: \n\
			Torrent Name: %s \n\
			trid = %s \n\
			Case = %s \n\n \
		Predeliver:\n"%(Trname, Trid, Casos[NCase])

		filelisttxt, nonwantedfilestxt = getfiledeliverlistTXT (con,Trid)
		msgbody += filelisttxt + "\n"
		msgbody += nonwantedfilestxt + "\n"
		STmail ('Predelivered status for: '+ Trname ,msgbody, topic = 6 )
		con.execute ("UPDATE msg_inputs SET status='Sent' WHERE nreg = ?", (Nreg,))
	con.commit()
	return

def gettrrpendingTXT (con):
	cursor2 = con.execute ("SELECT id, trname FROM tw_inputs WHERE status = 'Added' ORDER BY added_date")
	filelisttxt = "Torrents pending downloading:\n"
	for entry in cursor2:
		filelisttxt += "\t"+str(entry[0])+"\t"+entry[1]+"\n"
	return filelisttxt

def getfiledeliverlistTXT (con,Trid):
	cursor2 = con.execute ("SELECT wanted, size, originalfile, destfile FROM files WHERE trid = %s ORDER BY destfile"%Trid)
	filelisttxt = "List of files: \n"
	nonwantedfilestxt = ""
	for entry in cursor2:
		if entry[0] == 1:
			filelisttxt += "\t"+entry[3]+"\t("+str(entry[1])+")\n"
		else:
			if nonwantedfilestxt == "":
				nonwantedfilestxt = "List of nonwanted files: \n"
			nonwantedfilestxt += "\t" + os.path.basename(entry[2])+"\t("+str(entry[1])+")\n"
	
	return filelisttxt, nonwantedfilestxt

def getfileoriginlistTXT (con,Trid):
	Dwfolder = con.execute ("SELECT dwfolder from tw_inputs WHERE id = %s"%Trid).fetchone()[0]
	if Dwfolder == None:
		Dwfolder =''
	Dwfolder = addslash(Dwfolder)
	cursor2 = con.execute ("SELECT wanted, size, originalfile FROM files WHERE trid = %s ORDER BY originalfile "%Trid)
	filelisttxt = "List of files: \n"
	for entry in cursor2:
		filelisttxt += "\t"+Dwfolder+entry[2]+"\t("+str(entry[1])+")\n"
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

def Retrievefiles (tc):
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, hashstring FROM tw_inputs WHERE filesretrieved = 0 and (status = 'Added' or status = 'Completed') ")
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
		matrix = [0,0,0,0,0,0,0,0,0]
		folders = set()
		for key in filesdict:
			Size = filesdict.get(key)['size']
			Originalfile = filesdict.get(key)['name']
			Mime = fileclasify(Originalfile)
			params = DBid, Size, Originalfile, Mime
			con.execute ("INSERT INTO files (trid, size, originalfile, mime ) VALUES (?,?,?,?)",params)
			matrix = addmatrix (matrix, Mime)
			folders.add (os.path.dirname(Originalfile))
		matrix = addfoldersmatrix (matrix,folders,7,8)
		# Selecting Case and processing torrent files.
		Caso, Psecuence = Selectcase (matrix)
		Deliverstatus, Msgcode = 'Added', 6
		if Caso == 0 :
			Deliverstatus, Msgcode = None, 7
		params = len(filesdict), Deliverstatus ,DBid
		con.execute ("UPDATE tw_inputs SET filesretrieved=?, deliverstatus = ? WHERE id = ?",params)
		params = DBid, 'Added', Caso, str(Psecuence),  matrix[0],matrix[1],matrix[2],matrix[3],matrix[4],matrix[5],matrix[6],matrix[7],matrix[8]
		con.execute ("INSERT INTO pattern (trid,status,caso,psecuence,nfiles,nvideos,naudios,nnotwanted,ncompressed,nimagefiles,nother,nfolders,folderlevels) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",params)
		con.commit()
		ProcessSecuence (con, DBid, Psecuence)
		SpoolUserMessages(con, Msgcode, DBid)
	con.commit()
	con.close()

def ProcessSecuence(con, Id, Psecuence):
	global GideonConfig
	for process in Psecuence:
		print ("\t",process,'...........')
		cursor2 = con.execute("SELECT nreg, mime, originalfile, destfile FROM files WHERE trid = %s and wanted = 1"%Id)
		if process == 'assign video destination':
			for entry in cursor2:
				params = (Fmovie_Folder+entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'assign audio destination':
			for entry in cursor2:
				params = (Faudio_Folder+entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'cleanfilenames':
			for entry in cursor2:
				folder= os.path.dirname(entry[3])
				filename, ext = os.path.splitext(os.path.basename(entry[3]))
				cleanedfilename = clearfilename(filename)
				newdest = os.path.join(folder,(cleanedfilename+ext))
				params = (newdest,
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == '(o)cleanDWfoldername':
			for entry in cursor2:
				folder= os.path.dirname(entry[2])
				filename = os.path.basename(entry[2])
				if folder != '':
					folder = clearfilename(folder)
				newdest = os.path.join(folder,filename)
				params = (newdest, entry[0])
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
		elif process == 'deletenonwantedfiles':
			for entry in cursor2:
				if entry[1] == 'notwanted':
					con.execute("UPDATE files SET destfile = null, wanted = 0  WHERE nreg = ?", (entry[0],))
			con.commit()
			continue
		elif process == '(o)assign local path from videodest.ini' and Hotfolder != None:
			filmnamelist = set()
			for entry in cursor2:
				if entry[1] == 'video':
					filmnamelist.add(clearfilename(os.path.splitext(entry[2].split("/")[0])[0]))
					filmnamelist.add(clearfilename(os.path.splitext(entry[2].split("/")[-1])[0]))
			Subpath, maxmatch = "", 10
			Fvideodest = getaliaspaths(Hotfolder+"Videodest.ini")
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

	return

Psecuensedict = {
	0 : list(),
	1 : ['(o)cleanDWfoldername','deletenonwantedfiles','moveupfileandrename','(o)assign local path from videodest.ini','assign video destination'],
	2 : ['(o)cleanDWfoldername','deletenonwantedfiles','(o)assign local path from videodest.ini','assign video destination',],
	3 : ['(o)cleanDWfoldername','assign audio destination','cleanfilenames'],
	4 : list(),
}

Casos = {
	0 : "There is no available case for this matrix",
	1 : "(video) Torrent is just one file and it is a video file. and it may have some NonWantedFiles.",
	2 : "(video) Contains 1 video file and at least a image file, at the same level.",
	3 : "(audio) Contains one or more audio files and at least a image file, at the same level.",
}

def Selectcase (matrix):
	""" Selects a case to deliver the torrent files and an operational behaviour for files.
		operational behaviour is returned a a list of number of codes that operates on all the files of
		the torrent.
		If no case is matched, it returns None.
		Actual Matrix represents:
		[0] nfiles
		[1] nvideos
		[2] naudios
		[3] nnotwanted
		[4] ncompressed
		[5] nimagefiles
		[6] nother
		[7] nfolders
		[8] folderlevels

		DefTest OK"""
	# Selectig case of only one video file:
	if matrix[0] >= 1 and matrix[1] == 1 and (matrix[2]+matrix[4]+matrix[5]+matrix[6])==0 and matrix[8]==1:
		NCase = 1

	elif matrix[0] > 1 and matrix[1]==1 and (matrix[2]+matrix[4])==0 and matrix[6]==0 and matrix[8]==1:
		NCase = 2

	elif matrix[0] >= 1 and matrix[2]>0 and (matrix[1]+matrix[6])==0 and matrix[7]==1 and matrix[8]==1:
		NCase = 3

	else:
		NCase = 0

	logging.info ("Selected case %s : "%NCase + Casos[NCase])
	
	return NCase, Psecuensedict[NCase]

def addmatrix(matrix, mime):
	""" Adds +1 on matrix [0]
		Adds +1 on matrix by mime type dict.
		Deftest OK"""
	matrix [0] += 1
	matrix [Codemimes[mime]] += 1
	return matrix

def addfoldersmatrix (matrix, folders, posnfolders, posfolderlevels):
	""" Given a info matrix and a set of relative _folders_,
		it returns in the given positions:
			number of diferent folders (counts the elements that are into the set())
			depth of level path.
		returns the matrix.
		Deftest OK"""
	matrix [posnfolders] = len(folders)
	levels = 0
	for a in folders:
		nlev = 1 + a.count('/')
		if nlev > levels:
			levels = nlev
	matrix [posfolderlevels] = levels
	return matrix

def ProcessCompletedTorrents():
	''' Check for 'Completed' torrents and _deliverstatus_ = 'Added' in tw_inputs DB.
		Process torrent's files and do the movements.
		Once the move is done, field _deliverstatus_ is set to 'Delivered'
		'''
	con = sqlite3.connect (dbpath)
	cursor1 = con.cursor()
	cursor1.execute ("SELECT id, trname, dwfolder from tw_inputs WHERE status = 'Completed' and deliverstatus = 'Added'")
	for Id, Trname, Dwfolder in cursor1:
		cursor2 = con.cursor()
		cursor2.execute ("SELECT nreg, originalfile, destfile from files WHERE trid = %s and wanted = 1 and status = 'Added' "%Id)
		for Nreg, originalfile, destfile in cursor2:
			origin = addslash (Dwfolder) + originalfile
			status = copyfile (origin, destfile)
			con.execute ("UPDATE files SET status = ? WHERE nreg = ?",(status,Nreg))
		con.execute ("UPDATE tw_inputs SET deliverstatus = 'Delivered' WHERE id = %s"%Id)
		SpoolUserMessages(con, 7, TRid = Id)
	con.commit()
	con.close()

	return

def StartTRService ():
	con = sqlite3.connect (dbpath)
	Nactivetorrents = con.execute("SELECT count(status) FROM tw_inputs WHERE status = 'Added'").fetchone()[0]
	if Nactivetorrents > 0 and not getappstatus(['transmission-gtk']):
		launchTR (cmd, 25)
		SpoolUserMessages(con, 9, None)
	con.commit()
	con.close()
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
			logging.warning('(coverservice):Folder %s does not exist.'%folder2scan)
	coverperformer (filemovieset, Availablecoversfd)		

def coverperformer(filemovieset,Availablecoversfd):
	''' Assign cover files and moves matched cover next to the film file.
		input sould be a list, but also a string with a /path/to/filename.ext is possible
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
	dellist = ['',]
	for trr in tc.get_torrents():
		DBid, Deliverstatus = cursor.execute ("SELECT id, deliverstatus from tw_inputs WHERE TRname = ? and (status = 'Ready' or status = 'Added' or status = 'Completed') ", (trr.name,)).fetchone()
		if DBid == None:
			logging.warning('Active torrent is not being tracked on DB: %s'%trr.name)
			continue
		elif trr.seed_ratio_mode == 'unlimited' or (trr.seed_ratio_mode == 'global' and not tc.session.seedRatioLimited):
			# Retention policy does not apply to torrents that seeds forever.
			print ("Retention policy does not apply to torrents that seeds forever.")
			continue
		elif trr.doneDate == 0:
			# Retention policy does not apply to Manual added torrents with already existent files
			continue
		elif Deliverstatus == None:
			#Torrent has no Case Selected, you can stablish a retention policy for this torrents.
			continue
		elif Deliverstatus == 'Delivered':
			# This torrents have been delivered to another location. You can delete them due to a retention policy defined here:
			if trr.isFinished or (trr.status in ['seeding','stopped'] and trr.progress >= 100 and now > (trr.date_done + MaxseedingDays_dt)):
				logging.info ('Torrent %s in DB is going to be deleted due to a retention policy: (%s)'%(DBid, trr.name))
				SpoolUserMessages(con, 10, TRid = DBid)
				dellist.append ((trr.id, DBid))
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
	dellist.remove('')
	for trr_id, DBid in dellist:
		tc.remove_torrent(trr_id, delete_data=True, timeout=None)
		logging.info ('\tTorrent %s in DB has been deleted from Transmission Service.'%DBid)
		con.execute ("UPDATE tw_inputs SET status='Deleted' WHERE id = %s"%DBid)
	con.commit()
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
	Itemlist = []
	filelist = [os.path.join(Tfolder,i) for i in os.listdir(Tfolder)]
	for entry in filelist:
		entrytype = None
		if os.path.isdir (entry):
			if folderinuse (entry):
				logging.info("folder %s was not processed because was in use." %entry)
				continue
			else:
				entrytype = '.folder'
		elif os.path.isfile (entry):
			if os.path.splitext(entry)[1].lower() in ('.rar','.zip','.7z'):
				logging.info("file %s was not processed because it is a compressed file." %entry)
				continue
			if fileinuse (entry) == True:
				logging.info("file %s was not processed because it were open by an application." %entry)
				continue
			else:
				entrytype = '.file'
		if entrytype != None:
			Itemlist += [(entry,entrytype),]
	return Itemlist

# ========================================
# 			== MAIN PROCESS  ==
# ========================================
if __name__ == '__main__':
	# Main loop
	StartTRService ()
	while True:
		if Hotfolder != None:
			Dropfd (Availablecoversfd, ["jpg","png","jpeg"])  # move incoming user covers to covers repository
			Hotfolderinputs = [(i,".torrent") for i in Dropfd (Torrentinbox, ["torrent",])]
			if len (Hotfolderinputs) > 0:
				addinputs (Hotfolderinputs)
			CoverService (Fmovie_Folder, Availablecoversfd, Hotfolder+"Videodest.ini")

		if Telegraminbox != None:
			Hotfolderinputs += Telegramfd (Telegraminbox)
			if len (Hotfolderinputs) > 0:
				addinputs (Hotfolderinputs)

		SendtoTransmission ()
		# Process file and folders Telegram entries

		if getappstatus (['mplayer','vlc']) == False:
			ProcessCompletedTorrents ()

		if getappstatus(['transmission-gtk']):
			tc = connectTR ()
			TrackManualTorrents (tc)
			TrackDeletedTorrents(tc)
			TrackFinishedTorrents (tc)
			Retrievefiles(tc)
			RetentionPService(tc)
		
		MsgService ()

		logging.debug("# Done!, next check at "+ str (datetime.datetime.now()+datetime.timedelta(seconds=s)))
		time.sleep(s)


