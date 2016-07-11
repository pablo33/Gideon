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

	Logs are stored in a single TRworkflow.log file.

	You need to set up TRWorkflowconfig.py first. o run this program for the first time.
	'''

# Standard library module import
import os, sys, shutil, logging, datetime, time, smtplib, re
from email.mime.text import MIMEText  # for e-mail compose support
from subprocess import check_output  # Checks if transmission is active or not
import sqlite3  # for sqlite3 Database management
import transmissionrpc


# Custom module iport
# import namefilmcleaner, readini, filmcovermatch, programstarter



__version__ = "3.0beta"
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

def copyfile(origin,dest,mode="c"):
	""" Copy or moves file to another place
		input: file origin (full/relative patn and name)
		input: file destination (full/relative path an name)
		input: mode: "c" for copy, "m" for move (default "c")

		if a file already exists, nothing is done.
		return True if success, or False if it didn't success
		"""

	if itemcheck(dest) == "":
		makepaths ([os.path.dirname(dest),])
		if mode == "c":
			shutil.copy(origin,dest)
			return True
		if mode == "m":
			shutil.move(origin,dest)
			return True
	else:
		logging.debug("\tDestination file already exists")
		return False


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

userpath = os.path.join(os.getenv('HOME'),".TRWorkflow")
userconfig = os.path.join(userpath,"TRWorkflowconfig.py")
dbpath = os.path.join(userpath,"DB.sqlite3")
Torrentinbox = os.path.join(userpath,"Torrentinbox")  # Place to manage incoming torrents files
Availablecoversfd = os.path.join(userpath,"Covers")  # Place to store available covers

logpath =  os.path.join(userpath,"logs")
logging_file = os.path.join(logpath,"TRworkflow.log")

makepaths ([userpath, logpath, Torrentinbox, Availablecoversfd])


# (1.3) loading user preferences
if itemcheck (userconfig) == "file":
	print ("Loading user configuration....")
	sys.path.append(userpath)
	import TRWorkflowconfig
	import namefilmcleaner, readini, programstarter
else:
	# initilizing user's default config file.
	print ("There isn't an user config file: " + userconfig)
	if itemcheck ("TRWorkflowconfig(generic).py") != "file":
		print ("Please, run TRWorkflow.py for the first time from its own intalled dir. ")
		exit()
	else:
		copyfile ("TRWorkflowconfig(generic).py",userconfig,"c")
		print ("An user config file has been created: " + userconfig)
		print ("Please customize by yourself before run this software again")
		print ("This software is going to try to open with a text editor.")
		os.system ("gedit "+userconfig)
		exit()

print ("Loginlevel:", TRWorkflowconfig.loginlevel)
logging.basicConfig(
    level=TRWorkflowconfig.loginlevel,
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
Fmovie_Folder = addslash(TRWorkflowconfig.Fmovie_Folder)  # Default place to store movies
Faudio_Folder = addslash(TRWorkflowconfig.Faudio_Folder)  # Default place to store music
Hotfolder = addslash (TRWorkflowconfig.Hotfolder)  # Hotfolder to retrieve user incoming files, usually a sycronized Dropbox folder
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
}

Codemimes = {
	'video' : 1,
	'audio' : 2,
	'notwanted' : 3,
	'compressed' : 4,
	'image' : 5,
	'other' : 6,
}


s =  TRWorkflowconfig.s # Time to sleep between checks (Dropbox folder / transmission spool)
cmd  = TRWorkflowconfig.cmd # Command line to lauch transmission
lsdy = TRWorkflowconfig.lsdy # List of hot folders to scan for active or new file-torrents
lsext= ['.part','.torrent'] # extensions that delates a new torrent or an antive one. 
TRmachine = TRWorkflowconfig.TRmachine
TRuser = TRWorkflowconfig.TRuser
TRpassword = TRWorkflowconfig.TRpassword


# .. Default Videodest.ini file definition (in case there isn't one)
startVideodestINIfile = """
# Put this file into Dropbox/TRinbox
#	
#	define a destination with some words to automatically store file-movies to the right place.
#	
#	Those paths are relative to Videodest default path (defined in Fmovie_Folder var (at TRWorkflowconfig.py))
#	

__version__ = 1.1
__date__ = "11/04/2015"

# You can define alias for common destinations, to substitute text 
alias=Series        ,    /series/
alias=Sinfantiles   ,    /Series infantiles/

# Define destinations:
#	guess a title to match the filemovie then,
#   define a relative path to store it (starting at default "filemovie folder" defined in TRWorkflowconfig.py file) 
#	(you can use alias enclosed in <....> to replace text, but remember that you must define them first)
#  Those are examples, please replace them and follow the structure.
#  Please, do not include comments at the end of alias or dest lines. This is not an python file.
#  
dest = star wars rebels, <Sinfantiles>
dest = Sleepy Hollow temporada 2, <Series>Sleepy Hollow Temp 2
dest = Sleepy Hollow temporada 1, <Series>Sleepy Hollow Temp 1

# EOF
"""

## Deprecated ## spoolfile = os.path.join (logpath, "Torrent.spool") # Spool file fullpath-location for incoming torrents

# (1.6) Prequisites:
#=============

if itemcheck (Hotfolder) != 'folder' :
	print ('Hotfolder does not exist. Please edit your user configuration file at: \n',  userconfig)
	exit()

# Checking and setting up Fvideodest file:
if itemcheck(Hotfolder+"Videodest.ini") == "":
	logging.warning("Videodest.ini file does not exist, setting up for the first time")
	f = open(Hotfolder+"Videodest.ini","a")
	f.write(startVideodestINIfile)
	f.close()
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
	#  For Incoming torrents and pictures, it registers the date of inclusion and state of referenced file:
	#	ready: file is ready to be used.
	#	deleted: file has been deleted.
	cursor.execute ("CREATE TABLE tw_inputs (\
		id INTEGER PRIMARY KEY AUTOINCREMENT,\
		fullfilepath char NOT NULL ,\
		filetype char,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d','now')),\
		state char NOT NULL DEFAULT('Ready'),\
		deliverstatus char,\
		filesretrieved integer DEFAULT (0),\
		trname char, \
		dwfolder char \
		)")
	cursor.execute ("CREATE TABLE msg_inputs (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),\
		trid int,\
		state char NOT NULL DEFAULT('Ready'),\
		topic int NOT NULL\
		)")
	cursor.execute ("CREATE TABLE files (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		added_date date NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','localtime')),\
		trid int NOT NULL,\
		state char NOT NULL DEFAULT('Added'),\
		wanted boolean DEFAULT (1),\
		size number ,\
		mime char ,\
		originalfile char,\
		destfile char \
		)")
	cursor.execute ("CREATE TABLE pattern (\
		nreg INTEGER PRIMARY KEY AUTOINCREMENT,\
		trid int NOT NULL,\
		state char NOT NULL DEFAULT('Added'),\
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



# .. Fvideodest var is global, that provides a dynamic read of videodest.ini on each processed torrent.
## Deprecated: destination are an the DataBase >> Fvideodest = "" # Later it'll be a dictionary that it is read from Videodest.ini on each torrent process



# ===================================
# 				Input process		
# ===================================

'''
def defaultpath(origin):
	""" Selects destination due on filetype
		DefTest >> OK """
	global Fmovie_Folder
	global Fother_Folder
	global Faudio_Folder
	# Estoring file by filetype.
	kindofitem = fileclasify(origin)
	dest = ""
	if kindofitem == "movie" :
		dest = Fmovie_Folder
	if kindofitem == "other" :
		dest = Fother_Folder
	if kindofitem == "audio" :
		dest = Faudio_Folder
	return dest
'''
def procfile (origin, mode="c"):
	""" If item is a file, and you only have to clean and deliver, 
		you can process it with this script. 
		The file will not be renamed in place but later into destination.
		inputs: full-path/to/input/filename
		output: full-path/to/out-putt/filename
		"""
	global Fvideodest, TRWorkflowconfig

	logging.debug ("Cleaning filename & delivering")
	basename , ext = os.path.basename(os.path.splitext(origin)[0]), os.path.splitext(origin)[1]
	basepath = os.path.dirname(origin)
	NEW_filename = namefilmcleaner.clearfilename(basename) # Cleaning name.
	NEW_basepath = defaultpath(origin) # We set a default path in order to a kind of item.
	subpath =""
	media = fileclasify (origin) # We set media a filetype

	#1 Adding sub-paths to dest. Only for movies, you can define a sub-path to add
	if media == "movie":
		subpath = delivermovie(NEW_filename,Fvideodest)

	#2 Stting destination string, preserving file-extension
	dest = os.path.join((NEW_basepath+subpath),(NEW_filename+ext))

	#3 Movies ====
	if media == "movie":
		# Wait!, before copy/move the file, we scan this file in place and check if it is a good file or need to re-process.
		# Checking file for 
		pull = MailMovieInfo (origin,TRWorkflowconfig.mail_recipients)
		# We add this file to a pull of files to process with avidemux
		if pull == 1:
			# we stop process and store information on a pull file for later process with avidemux
			add_to_pull(origin,dest)
			return "1"
	
	#4 we process file to destination.
	state = copyfile(origin,dest,mode)
	if state == "0": # File already exists.
		return "0"
	logging.info("Filename has been processed and stored as:"+dest)
	
	#5 Covers from covers repository
	if media == "movie":
		# We always trying to find a cover and put it at the right place. 
		addcover(dest,TRWorkflowconfig.Torrentinbox)

	#6 If everything have been ok, we return dest
	return dest

def procfolder(origin):
	global Fmovie_Folder
	global Fother_Folder
	global Faudio_Folder
	# Grabbing information
	#---------------------
	print("..... Scaning folder contents:")
	logging.info("Scaning folder contents:")
	items = scanfolder(origin)
	nfolder = int (items[0]) # number of folders (1 level)
	nfiles  = int (items[1]) # number of files (1 level)
	nmovies = len (items[3]) # number of movies (1 level)
	naudio  = len (items[4]) # number of audiofiles (1 level)
	nnotwant= len (items[5]) # number of not wanted files 
	ncompres= len (items[6]) # number of compressed files 
	nother  = len (items[7]) # number of other files
	print ("Executing decisions")
	# Decisions:
	# =========
	#1# only one movie without folders nor other useful files.
	if nmovies == 1 and (nfolder+naudio+nother+ncompres)==0 :
		logging.info ("===========\n#1# Thereis only one videofile.")
		logging.debug ("moving up this file...:"+items[3][0]+" and giving its parent folder name:")
		NEW_item = moveup(items[3][0])
		
		# Removing old-empty tree
		shutil.rmtree(os.path.dirname(items[3][0]))
		
		# Processing file
		logging.info("Moving file to movies place")
		state = procfile (NEW_item,"m")
		return state
				
	#2# more than one movie without other files.
	elif nmovies > 1 and (nfolder+naudio+nother+ncompres)==0 :
		logging.info ("===========\n#2# There are just some videos:")
		
		# Process files at upper dir
		removetree = True
		for a in items[3]:
			# moving up
			a2 = os.path.join( os.path.dirname(os.path.dirname(a)) , os.path.basename(a) )
			a2is = itemcheck(a2)
			if a2is == "file":
				logging.info("file %s already exists, replacing it." %(a2))
				os.remove(a2)
			if a2is in ("folder","link"):
				logging.warning("file %s can not replace a %s"%(a2,a2is))
				logging.warning("parent folder won't be removed")
				a2 = a
				removetree = False
			else:
				shutil.move(a,a2)

			state = procfile (a2,"m")
			if state == "0":
				logging.warning("Final destinaton file already exist, deleting original item: "+a2)
				os.remove(a2)
			elif state == "1":
				logging.info("File has been put into avidemux queue: "+a2)
			else:
				logging.info("File %s has been processed and stored as %s."%(a2,state))

		# Removing old tree
		itemtree = os.path.dirname(items[3][0])

		if removetree == True:
			logging.debug("Removing processed items container folder: "+itemtree)
			shutil.rmtree(itemtree) # Removing folder.
			nnotwant = 0 # We don't want to delete this files again.
		else:
			logging.warning("There have been some errors processing videos, check "+ itemtree + " folder once you have processed pull file with avidemux.")
	
	elif nfolder > 0 or nfiles == 0 :
		logging.warning("Case of sub-folder.... nothing was programmed")
		return "3"
	else:
		logging.warning ("Nothing was programmed for this case: Reporting Folder Scaning Results")
	
	# Removing non wanted files if there aren't folders
	if nfolder+ncompres+nother == 0 and nnotwant >= 1 :
		logging.debug ("Deleting non wanted files:.........")
		removeitems(items[5])
	
	# Exiting with the report.
	report = printreport(items)
	print (report)
	logging.debug(report)

def MailMovieInfo(moviefile,mail):
	""" e-mails info movie to a mail.

		input: filemovie, recipient e-mail
		output: 
		"""
	global TRWorkflowconfig
	
	send = 0 # We put send flag > off
	mydict, info_file = Extractcmovieinfo(moviefile)
	# we add a Megapixel parameter
	mydict ['MP'] = int(mydict ['ID_VIDEO_WIDTH']) * int(mydict ['ID_VIDEO_HEIGHT']) / 1000000
	alerts = set (a for a in TRWorkflowconfig.alert_values)
	data = set (a for a in mydict)
	union = alerts & data
	if len (union) > 0:
		f = open (info_file,"a")
		f.write("===========  ALERTS ===========\n\n")
		for a in union:
			if mydict[a] == TRWorkflowconfig.alert_values[a]:
				f.write(a+"="+mydict[a]+"\n")
				send = 1
		f.write('MP='+str(mydict['MP'])+'\n')
		f.write("\n")
		f.close()
	# checking Exceptions 
	if send == 1 and mydict ['MP'] < 0.3 : # Videos less than 0.3Mp do not have any problems on my machine. They do not need to be recompressed.
		send = 0

	# Sending alerts
	if send == 1 or TRWorkflowconfig.send_info_mail == "always":
		logging.debug("Sending alert mail")
		emailme ( TRWorkflowconfig.mailsender, 'Alert notification in %s' %(os.path.basename(moviefile)), mail, info_file)
	return send

def TRprocfolder(origin):
	global Fother_Folder
	# Cleaning folder name
	basename = os.path.basename(origin)
	logging.debug ("Cleaning foldername:"+basename+">>>")
	NEW_filename = namefilmcleaner.clearfilename(basename)
	logging.info ("Name cleaned:"+NEW_filename)
	dest = Fother_Folder+NEW_filename
	# Checking destination
	logging.debug ("Checking destination...")
	if itemcheck(dest) == "":
		logging.debug("....copying tree to destination")
		logging.debug("from:"+origin)
		shutil.copytree(origin,dest)
		logging.info("item has been copied to :"+dest)
		print (origin+ " >> has been copied to :\n"+dest)
		return dest
	else:
		logging.warning("Destination folder already exists, folder %s has not been procesed" %(origin))
		sys.exit("\nDestination Folder ("+dest+") already exists. Exiting.\n")

def moveup (item):
	''' This function:
		#1 moves the file to parent directory with the
		#2 same name as his container folder (parent).
		#3 preserves the extension.
		#5 returns its new absolute path.
		#BUT: Do not remove original folder !
		input: string with absolute path (item must be a file)
		output: string with absolute new path
			And file is moved.
		'''
	ext=os.path.splitext(item)[1]
	endbasename = os.path.dirname(item)+ext
	shutil.move(item,endbasename)
	return endbasename

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

def printreport(items):
	"""Prints a input report
		input: list of items
		output: String with 'printed' report
		"""
	nfolder = int (items[0]) # number of folders (1 level)
	nfiles  = int (items[1]) # number of files (1 level)
	nmovies = len (items[3]) # number of movies (1 level)
	naudio  = len (items[4]) # number of audiofiles (1 level)
	nnotwant= len (items[5]) # number of not wanted files 
	ncompres= len (items[6]) # number of compressed files 
	nother  = len (items[7]) # number of other files
	report = "\n========== ORIGINAL ITEM REPORT ========\n"
	report += "".join(["Number of sub-folder        :",str(nfolder),"\n"])
	report += "".join(["Number of files             :",str(nfiles),"\n"])
	report += "".join(["    Number of movies        :",str(nmovies),"\n"])
	for a in items[3]:
		report += "".join([os.path.basename(a),"\n"])
	report += "".join(["    Number of audiof        :",str(naudio),"\n"])
	for a in items[4]:
		report += "".join([os.path.basename(a),"\n"])
	report += "".join(["    Number of NonWantedFiles:",str(nnotwant),"\n"])
	for a in items[5]:
		report += "".join([os.path.basename(a),"\n"])
	report += "".join(["    Number of compressed files   :",str(ncompres),"\n"])
	for a in items[6]:
		report += "".join([os.path.basename(a),"\n"])
	report += "".join(["    Number of other files   :",str(nother),"\n"])
	for a in items[7]:
		report += "".join([os.path.basename(a),"\n"])
	report += "".join(["========================================","\n"])
	return report

def addcover(film,Torrentinbox):
	''' This function evaluates a suitable cover for a filemovie based on its filename.
		it scans into a folder most suitable cover based on cover filenames and returns this match.
		Returns "" if not covers are found.
		if a cover is found, it is moved beside the film and it is renamed (the image cover)
		with film's name (obiously preserving image extension).
			note that this function has been improved with chapter id. recognition to suit Freevo users (see comments below).

		input: /path/to/film.ext
		input: /path/to/repository_of_covers
		'''
	logging.debug("Finding a cover for:"+film+" in "+Torrentinbox)
	cover, match = filmcovermatch.matchfilm(film,filmcovermatch.listcovers(Torrentinbox))
	if cover == "":
		logging.info("No covers found")
		return ""
	logging.info("Found "+cover+" as most suitable cover for "+film)
	# If you are using Freevo as your HTPC, you should want to rename serie's cover without chapter's number, so:
	# Check if cover has a chapter identifier:
	if namefilmcleaner.chapid(film) == "":
		dest = os.path.splitext(film)[0]+os.path.splitext(cover)[1].lower()
	else:
		dest = os.path.splitext(film)[0][:-2]+os.path.splitext(cover)[1].lower()
		logging.info("Cover file is for a chapter structure, deleting Chapter identifier")
	# If destination cover is found, we will re-write it, so covers can be update with new ones.
	if itemcheck (dest) != "":
		logging.warning("file already exists, deleting old cover")
		os.remove(dest)
	# Finally we move cover.
	logging.debug("moving cover to:"+dest)
	shutil.move(cover,dest)
	return match

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
	mydict = readini.readparameters(info_file,"=")
	return mydict, info_file

def add_to_pull(origin,dest):
	""" Opens pull file and write a new line
	
		"""
	global logpath
	pullfile = addslash(logpath,"logpath")+"Avidemux.pull"
	if itemcheck (origin) == "":
		logging.info("Initializing Avidemux Pull file at "+pullfile)
	f = open(pullfile,"a+")
	# origin must not have any commas in the title:
	f.write("Avidemux="+origin+"\t"+dest+"\n")
	logging.debug("writed %s >>> %s in pullfile"%(origin,dest))
	f.close()
	return


# ========================================
# ===  PROCESING A TRANSMISSION ITEM ==========================
# ========================================

def listcovers(path):
	''' Return a list of covers-files
	input: relative path, or full-path
	output: list of image-files with relative or full-path
		'''
	# We need a final slash to path
	if path[-1] != "/":
		path += "/"
	# Initializing Lista
	lista = []
	# Listing
	for a in ("jpg","png","jpeg"):
		listb = glob(path+"*."+a)
		listc = glob(path+"*."+a.upper())
		for a in listb:
			lista.append(a)
		for a in listc:
			lista.append(a)
	lista.sort()
	return lista

# < used / reviewed > ----------------------------------------------------------------------------

def matchfilm(filmname,lista):
	''' Selects a item from a list with the best match.
		it is intended to find a cover file within a list of possible covers.

		input: filename.ext or full-path/filename.ext of a movie.
		input: list of items to match (filenames.ext or full-path/filenames.ext) (of covers)
		output: item of the list (of covers) that best matches as "cover", and punctuation of match
		Deftest OK!!'''
	# We want only the name of the file, without extension.
	match = 0
	matcheditem = ""
	for a in lista:
		# Get only the filename without extension
		name = os.path.splitext(os.path.basename(a))[0]
		matchw = 0
		for b in name.split():
			if b.upper() in filmname.upper():
				matchw += len(b)
				
		if matchw > match:
			matcheditem, match = a, matchw
	"""
	# We need at least a match of 4 points to return a reasonable match
	if match < 5:
		return "", 0
	"""
	return matcheditem, match

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
	r1, match = matchfilm (filmname,destinationlist)
	if r1 == "":
		logging.debug("\t\tNo mathches found to deliver, returning default path for the item")
		return "", 0
	return Fvideodest[r1], match

def getaliaspaths (textfile):
	""" Returns a dictionary contanining words and a relativa path to store filesdict
		The keys are fetched from a txt .ini like file.
		Deftest OK!! """
	logging.debug("\t\tExtracting alias definition from "+ textfile)
	alias = readini.readdict (textfile,"alias",",")

	logging.debug("\t\tExtracting dest definition")
	subpahts = readini.readdict (textfile,"dest",",")

	logging.debug("\t\tSubstituting dest alias")
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
	global TRWorkflowconfig
	ext = os.path.splitext(filename)
	if str(ext[1]) in ['','.']:
		logging.warning('File has no extension')
		return 'other'
	extwd = str (ext [1])
	extwd = extwd [1:]
	if extwd in TRWorkflowconfig.ext['video']: return 'video'
	elif extwd in TRWorkflowconfig.ext['audio']: return 'audio'
	elif extwd in TRWorkflowconfig.ext['compressed']: return 'compressed'
	elif extwd in TRWorkflowconfig.ext['notwanted']: return 'notwanted'
	elif extwd in TRWorkflowconfig.ext['image']: return 'image'
	return 'other'

def emailme(msgfrom, msgsubject, msgto, textfile, msgcc=''):
	'''Send a mail notification.
		parameters:
			msgfrom = e-mail from
			msgsubjet = Subject (string in one line)
			msgto = mail_recipients (could be more than one parsed into a string colon (:) separated)
			textfile = path to textfile, this is the body of the message. You can pass a string anyway,
		'''
	
	global TRWorkflowconfig
	
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
	s = smtplib.SMTP(TRWorkflowconfig.mailmachine)
	s.starttls()
	s.login( TRWorkflowconfig.mailsender, TRWorkflowconfig.mailpassw) # your user account and password
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
		#print (type(pids))
		logging.debug('no %s app is currently running'%(app))
		return None
	pidlist = pids.split()
	la = lambda x : int(x)
	pidlist = list (map (la , pidlist))
	return pidlist

def getappstatus (app):
	''' DefTest >> OK'''
	if get_pid (app) == None:
		return False
	return True

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
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check TRWorkflowconfig and set up Hotfolder to a valid path")
	if itemcheck (dest) in (["","file"]):
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check TRWorkflowconfig and set up Torrentinbox to a valid path")
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
		cleanedname = namefilmcleaner.clearfilename (basename)
		itemdest =  dest+cleanedname+extension
		while not copyfile (i,itemdest,mode="m"):
			itemdest = nextfilenumber (itemdest)
		moveditems.append (itemdest)
	return moveditems

def Dropfd(destfolder, lsextensions):
	''' move .torrents and covers from one destination to another.
		Pej. after setup your hotfolder, you can place there .torrent files or covers to 
		Start processing downloads or covers to have in mind.
		.torrent files and covers goes to $HOME/.TRWorkflow/Torrentinbox folder
		'''
	movelist = extfilemove (Hotfolder, destfolder, lsextensions)
	if movelist == []:
		logging.debug("Nothing was in the Dropbox-hot-folder.")
	else:
		logging.info("Those files were processed: from Hotfolder:")
		for a in movelist:
			logging.info('\t'+ a)
	return movelist

def addinputs ():
	''' Add new torrent entries into a DB queue,
	This queue is stored into the software database SQLite. > Table "TW_Inputs"
		'''
	Hotfolderinputs = Dropfd (Torrentinbox, ["torrent",])
	if len (Hotfolderinputs) > 0:
		con = sqlite3.connect (dbpath) # it creates one if it doesn't exists
		cursor = con.cursor() # object to manage queries
		for entry in Hotfolderinputs:
			params = (entry,'.torrent')
			cursor.execute ("INSERT INTO tw_inputs (fullfilepath, filetype) VALUES (?,?)", params)
			logging.info ('added incoming torrent to process: %s' %entry)
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
	if not getappstatus('transmission-gtk'):
		launchTR (cmd, 5)
	tc = transmissionrpc.Client(address=TRmachine, port = '9091' ,user=TRuser, password=TRpassword)
	logging.info('A Transmission rpc session has started')
	print ('Started rpc session')
	return tc

def SendtoTransmission():
	con = sqlite3.connect (dbpath) # it creates one if it doesn't exists
	cursor = con.cursor() # object to manage queries
	nfound = (cursor.execute ("select count(id) from tw_inputs where state = 'Ready'").fetchone())[0]
	if nfound > 0:
		logging.info (str(nfound) + 'new torrent entries have been found.')
		tc = connectTR ()
		cursor.execute ("SELECT id, fullfilepath FROM tw_inputs WHERE state = 'Ready'")
		for Id, Fullfilepath in cursor:
			trobject = tc.add_torrent (Fullfilepath)
			TRname = trobject.name
			con.execute ("UPDATE tw_inputs SET state='Added', trname=? WHERE id=?", (TRname,str(Id)))
			SpoolUserMessages(con, 2, TRid = Id)
	con.commit()
	con.close()
	return

def TrackManualTorrents(tc):
	''' Scans for list of torrents currently in transmission,
		add to DB those which are unknown.
		Those torrents are 'untracked torrents', and usually has been added
		directly to transmission by the user.
		With this function, TRWorkflow will track them.
		'''
	trobjlst = tc.get_torrents()
	if len (trobjlst) > 0:
		con = sqlite3.connect (dbpath)
		cursor = con.cursor()
		for trobject in tc.get_torrents():
			DBid = cursor.execute ("SELECT id from tw_inputs WHERE TRname = ? and (state = 'Ready' or state = 'Added' or state = 'Completed') ", (trobject.name,)).fetchone()
			if DBid == None and ( trobject.status in ['check pending', 'checking', 'downloading', 'seeding']):
				params = (trobject.magnetLink, '.magnet', 'Added', trobject.name)
				cursor.execute ("INSERT INTO tw_inputs (Fullfilepath, filetype, state, TRname) VALUES (?,?,?,?)", params)
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
	cursor.execute ("SELECT id, trname from tw_inputs WHERE state = 'Added' or state = 'Completed'")
	TRRset = set()
	for trr in tc.get_torrents():
		TRRset.add (trr.name)
	for Id, TRname in cursor:
		if TRname not in TRRset:
			con.execute ("UPDATE tw_inputs SET state='Deleted' WHERE id = ?", (Id,))
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
	for trr in tc.get_torrents():
		if trr.status in ['seeding','stopped'] and trr.progress >= 100:
			cursor.execute ("SELECT id from tw_inputs WHERE state = 'Added' and trname = ?", (trr.name,))
			for entry in cursor:
				Id = entry[0]
				con.execute ("UPDATE tw_inputs SET state='Completed', dwfolder = ? WHERE id = ?", (trr.downloadDir ,Id))
				SpoolUserMessages(con, 5, TRid = Id)
	con.commit()
	con.close()

def SpoolUserMessages(con, Topic, TRid=0):
	''' Insert an outgoing message into Data base,
		it assign a date of message release, so many messages can be send a time into one e-mail
		'''
	params = (
		'Ready',
		Topic,
		TRid
		)
	con.execute ("INSERT INTO msg_inputs (state, topic, trid) VALUES (?,?,?)", params)
	return

def STmail (topic, msg):
	msgfrom = TRWorkflowconfig.mailsender
	msgto = TRWorkflowconfig.mail_recipients
	msgsubject = topic
	textfile = msg
	emailme(msgfrom, msgsubject, msgto, textfile, msgcc="")
	return

def mailaddedtorrents(con):
	cursor = con.cursor ()
	cursor.execute ("SELECT nreg, trid, trname FROM msg_inputs join tw_inputs ON msg_inputs.trid = tw_inputs.id WHERE msg_inputs.state = 'Ready' and msg_inputs.topic = 1")
	for Nreg, Trid, Trname in cursor:
		msg = """A new torrent has been sent to Transmission Service for Downloading:
	Torrent Name:
	%s
	
	It will be tracked as nº:%s in Database.""" %(Trname,Trid)
		STmail ('Added to Transmission ' + Trname, msg)
		con.execute ("UPDATE msg_inputs SET state='Sent' WHERE nreg = ?", (Nreg,))
	con.commit()
	return

def MsgService():
	con = sqlite3.connect (dbpath)
	mailaddedtorrents (con)
	con.close()
	return

def gettrrobj (tc, name):
	""" Giving a Torrent's name, returns active Transmission's torrent object. 
		 Returns None if noone is Fetched
		"""
	trr = tc.get_torrents()
	for trobject in trr:
		if trobject.name == name:
			return trobject
	return None

def Retrievefiles (tc):
	con = sqlite3.connect (dbpath)
	cursor = con.cursor()
	cursor.execute ("SELECT id, trname FROM tw_inputs WHERE filesretrieved = 0 and (state = 'Added' or state = 'Completed') ")
	for Id, Trname in cursor:
		print (Id, Trname)
		trobject = gettrrobj (tc, Trname)
		filesdict = trobject.files()
		if len(filesdict) == 0:
			continue
		matrix = [0,0,0,0,0,0,0,0,0]
		folders = set()
		for key in filesdict:
			Size = filesdict.get(key)['size']
			Originalfile = filesdict.get(key)['name']
			Mime = fileclasify(Originalfile)
			params = Id, Size, Originalfile, Mime
			con.execute ("INSERT INTO files (trid, size, originalfile, mime ) VALUES (?,?,?,?)",params)
			matrix = addmatrix (matrix, Mime)
			folders.add (os.path.dirname(Originalfile))
		params = len(filesdict), Id
		con.execute ("UPDATE tw_inputs SET filesretrieved=?, deliverstatus = 'Added' WHERE id = ?",params)
		matrix = addfoldersmatrix (matrix,folders,7,8)
		# Selecting Case and processing torrent files.
		Caso, Psecuence = Selectcase (matrix)
		params = Id, 'Added', Caso, str(Psecuence),  matrix[0],matrix[1],matrix[2],matrix[3],matrix[4],matrix[5],matrix[6],matrix[7],matrix[8],
		con.execute ("INSERT INTO pattern (trid,state,caso,psecuence,nfiles,nvideos,naudios,nnotwanted,ncompressed,nimagefiles,nother,nfolders,folderlevels) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",params)
		con.commit()
		ProcessSecuence (con, Id, Psecuence)
		SpoolUserMessages(con, 6, Id)
	con.commit()
	con.close()

def ProcessSecuence(con, Id, Psecuence):
	global TRWorkflowconfig
	for process in Psecuence:
		print (process,'...........')
		cursor2 = con.execute("SELECT nreg, mime, originalfile, destfile FROM files WHERE trid = %s and wanted = 1"%Id)
		if process == 'assign video destination':
			for entry in cursor2:
				params = (TRWorkflowconfig.Fmovie_Folder+entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'assign audio destination':
			for entry in cursor2:
				params = (TRWorkflowconfig.Faudio_Folder+entry[3],
					entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'cleanfilenames':
			for entry in cursor2:
				folder= os.path.dirname(entry[3])
				filename, ext = os.path.splitext(os.path.basename(entry[3]))
				cleanedfilename = namefilmcleaner.clearfilename(filename)
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
				cleanedfoldername = namefilmcleaner.clearfilename(folder)
				newdest = os.path.join(cleanedfoldername,filename)
				params = (newdest, entry[0])
				con.execute("UPDATE files SET destfile=? WHERE nreg = ?",params)
			con.commit()
			continue
		elif process == 'moveupfileandrename':
			# (Valid when there is only one file to process)
			entry = cursor2.fetchone()
			folder= os.path.dirname(entry[3])
			filename , ext  = (os.path.splitext(entry[3]))
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
		elif process == '(o)assign local path from videodest.ini':
			Fvideodest = getaliaspaths(Hotfolder+"Videodest.ini")
			filmnamelist = set()
			for entry in cursor2:
				if entry[1] == 'video':
					filmnamelist.add(namefilmcleaner.clearfilename(os.path.splitext(entry[2].split("/")[0])[0]))
					filmnamelist.add(namefilmcleaner.clearfilename(os.path.splitext(entry[2].split("/")[-1])[0]))
			Subpath, maxmatch = "", 5
			for filmname in filmnamelist:
				tmpSubpath, match = Getsubpath (filmname, Fvideodest)
				if match > maxmatch:
					Subpath , maxmatch = tmpSubpath, match
			if maxmatch > 5:
				logging.info ("\tFound alias for movie: " + Subpath + ".Aciertos:"+ str(maxmatch) )
				cursor3 = con.execute("SELECT nreg, destfile FROM files WHERE trid = ? and wanted = 1", (Id,))
				for Nreg, destfile in cursor3:
					con.execute("UPDATE files SET destfile = ? WHERE nreg = ?", (os.path.join(Subpath,destfile) ,Nreg))		
				con.commit()
			continue
	return

Psecuensedict = { # (worked on originfile >> outputt destination)
	1 : ['(o)cleanDWfoldername','deletenonwantedfiles','moveupfileandrename','(o)assign local path from videodest.ini','assign video destination',],
	2 : ['(o)cleanDWfoldername','deletenonwantedfiles','(o)assign local path from videodest.ini','assign video destination',],
	3 : ['(o)cleanDWfoldername','assign audio destination','cleanfilenames'],
	4 : list(),
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
		logging.info ("Selected case 1 (video): Torrent is just one file and it is a video file. plus NonWantedFiles")
		Caso, Psecuence = 1, Psecuensedict[1]

	elif matrix[0] > 1 and matrix[1]==1 and (matrix[2]+matrix[4])==0 and matrix[6]==0 and matrix[8]==1:
		logging.info ("Selected case 2 (video): Contains 1 video file and at least a image file, at the same level.")
		Caso, Psecuence = 2, Psecuensedict[2]

	elif matrix[0] >= 1 and matrix[2]>=0 and (matrix[1]+matrix[6])==0 and matrix[7]==1 and matrix[8]==1:
		logging.info ("Selected case 3 (audio): Contains one or more audio files and at least a image file, at the same level.")
		Caso, Psecuence = 3, Psecuensedict[3]

	else:
		Caso, Psecuence = None, list()

	return Caso, Psecuence

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

# ========================================
# 			== MAIN PROCESS  ==
# ========================================
if __name__ == '__main__':
	# Main loop
	while True:
		Dropfd ( Availablecoversfd, ["jpg","png","jpeg"])  # move incoming user covers to covers repository
		addinputs()  # add .torrents files to DB. queue
		SendtoTransmission ()  # Send DB files/magnets registry to Transmission
		MsgService ()
		if getappstatus('transmission-gtk'):
			tc = connectTR ()
			TrackManualTorrents (tc)
			TrackDeletedTorrents(tc)
			TrackFinishedTorrents (tc)
			Retrievefiles(tc)

		logging.debug("# Done!, next check at "+ str (datetime.datetime.now()+datetime.timedelta(seconds=s)))
		time.sleep(s)
