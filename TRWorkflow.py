#!/usr/bin/python3
''' This program is intended to process downloaded torrents.
	
	This program has three main functions:

	Check contents of Torrnt.spoolfile
	Check contents of downloaded torrent,
	Stores downloaded files due to its nature and contents at pre configured folder/s.
	Rename files by cleaning filenames.
	It can find and select the most suitable cover from a folder and match to its videofile, so Freevo can read it as its cover.
	It can detect chapter-numbers at the end of the file/s, rename then as nxnn so Freevo can group videofiles as chapters.
	Scans videofiles properties and stores their information into a log file. (You'l need to install mplayer).
	As videofiles can be scanned, they can be stored at a tmp-folder, stored into a queue and send a warning e-mail. (Useful if your Hardware freezes playing videos and you need to recompress them, usually into a xVid codec)
	It can process this queue of videofiles and recompress automatically to a given codec without loosing its deliver path. Youl'l need avidemux to do that.
	It can send e-mails to notify some processes. You'l need to config your mail account.

	Logs are stored in TRworkflow.log file.

	You need to set up TRWorkflowconfig.py first.
	'''

# module import
import os, sys, shutil, logging, datetime, time, smtplib
from glob import glob
from email.mime.text import MIMEText


__version__ = "2.0"
__date__ = "12/04/2015"
__author__ = "pablo33"


# ===================================
# 				UTILS		
# ===================================
# 				(General util functions)

def addslash(d,text="variable"):
	""" Add a slash at the end if not any
		"""
	if d[-1]!= "/" :
		d += "/"
		logging.warning("..Adding a slash to "+text+":"+d)
	return d

def itemcheck(a):
	if os.path.isfile(a):
	    return 'file'
	if os.path.isdir(a):
	    return 'folder'
	if os.path.islink(a):
	    return 'link'
	return ""

def copyfile(origin,dest,mode="c"):
	""" Copy or moves file to another place
		input: file origin (fullpatn and name)
		input: file destination (fullpath an name)
		input: mode: "c" for copy, "m" for move (default "c")
		"""
	if itemcheck(dest) == "":
		destdir=os.path.dirname(dest)
		if itemcheck(destdir) == "":
			logging.debug("Creating destination dir:"+destdir)
			os.makedirs(destdir)
		if mode == "c":
			shutil.copy(origin,dest)
			logging.info("\nFile:               "+origin+"\nhas been copied to: "+ dest)
			print ("File:               "+origin+"\nhas been copied to: "+ dest)
			return 1
		if mode == "m":
			shutil.move(origin,dest)
			logging.info("\nFile:               "+origin+"\nhas been moved to:  "+ dest)
			print ("File:               "+origin+"\nhas been moved to:  "+ dest)
			return 1
	else:
		logging.warning("Destination file already exists, file %s has not been procesed" %(origin))
		print ("Destination file already exists, file %s has not been procesed" %(origin))
		return "0"


# ===================================
# 				Setting up		
# ===================================

# (1) LOG MODULE ........ (Configurying the logging module)
# ---------------------------------------------------------

# Getting current date and time
now = datetime.datetime.now()
today = "/".join([str(now.day),str(now.month),str(now.year)])
tohour = ":".join([str(now.hour),str(now.minute)])

# Getting user folder to place log files....
userpath = os.path.join(os.getenv('HOME'),".TRWorkflow")
userconfig = os.path.join(userpath,"TRWorkflowconfig.py")
logpath =  os.path.join(userpath,"logs")
if itemcheck (logpath) != "folder":
	os.makedirs(logpath)
logging_file = os.path.join(logpath,"TRworkflow.log")

# loading user preferences
if itemcheck (userconfig) == "file":
	print ("Loading user configuration....")
	sys.path.append(userpath)
	import TRWorkflowconfig
	import namefilmcleaner, readini, filmcovermatch, programstarter
else:
	# Crear archivo genérico.
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

# Starting log file
logging.debug("======================================================")
logging.debug("================ Starting a new sesion ===============")
logging.debug("======================================================")

# exit()

# Setting main variables
Fmovie_Folder = TRWorkflowconfig.Fmovie_Folder # Default place to store movies
Faudio_Folder = TRWorkflowconfig.Faudio_Folder # Default place to store music
Fother_Folder = TRWorkflowconfig.Fother_Folder # Default place to store other downloads
Dropboxfolder = TRWorkflowconfig.Dropboxfolder # Default place to store automatic inbox .torrents, .covers and Videodest.ini file 

# Prequisites:
#=============
#1 directory paths must end in slash "/"
Fmovie_Folder = addslash (Fmovie_Folder,"Fmovie_Folder")
Faudio_Folder = addslash (Faudio_Folder,"Faudio_Folder")
Fother_Folder = addslash (Fother_Folder,"Fother_Folder")
Dropboxfolder = addslash (Dropboxfolder,"Dropboxfolder")



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

# .. Fvideodest var is global, that provides a dynamic read of videodest.ini on each processed torrent.
Fvideodest = "" # Later it'll be a dictionary that it is read from Videodest.ini on each torrent process

# ===================================
# 				Input process		
# ===================================

def defaultpath(origin):
	""" Selects destination due on filetype
		"""
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

def emailme(msgfrom, msgsubject, msgto, textfile, msgcc=""):
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

def scanfolder(d):
	''' scans the contents of a folder.
		input: "folderpath to scan"

		output:
		(
			number of folders at first level,
			number of files at first level,
			list of folders,
			list of video-files,
			list of audio-files,
			list of notwanted-files,
			list of other files,
			list of compressed files,
			)
		'''
	global TRWorkflowconfig

	__version__ = 1.2
	__date__="20/11/2014"
	if d[-1]!="/": d = d+"/"
	listitems = glob(d+"*")
	# Starting counters and vars
	ND, NF = 0, 0
	lFL, lVF, lAF, lNW, lCF, lOF = [], [], [], [], [], []
	# Iterating elements
	for a in (listitems):
		logging.info ("Item: '"+a)
		if os.path.isdir(a):
			logging.info (">>> isdir")
			ND += 1
			lFL.append(a)
			continue
		elif os.path.isfile(a):
			NF += 1
			ext = os.path.splitext(a)[1]
			if ext[1:] in TRWorkflowconfig.ext["movie"]:
				logging.info  (">>> is a movie")
				lVF.append(a)
				continue
			if ext[1:] in TRWorkflowconfig.ext["audio"]:
				logging.info  (">>> is audio")
				lAF.append(a)
				continue
			if ext[1:] in TRWorkflowconfig.ext["compressed"]:
				logging.info  ("is a compressed file")
				lCF.append(a)
				continue
			if ext[1:] in TRWorkflowconfig.ext["notwanted"]:
				logging.info  ("is a non wanted file")
				lNW.append(a)
				continue
			logging.info  ("is other file-type")
			lOF.append(a)
	return (ND,NF,lFL,lVF,lAF,lNW,lCF,lOF)

def fileclasify(f):
	""" Classify a file
		input: file
		output: "other" (default), "audio", "video", "movie", "compressed" 
		"""
	global TRWorkflowconfig
	ext = os.path.splitext(f)
	if str(ext[1]) in ["","."]:
		logging.warning("File has no extension")
		return "other"
	extwd = str (ext [1])
	extwd = extwd [1:]
	logging.debug("File extension is:"+extwd)
	if extwd in TRWorkflowconfig.ext["movie"]:
		logging.info  (">>> is a movie")
		return "movie"
	if extwd in TRWorkflowconfig.ext["audio"]:
		logging.info  (">>> is audio")
		return "audio"
	if extwd in TRWorkflowconfig.ext["compressed"]:
		logging.info  ("is a compressed file")
		return "compressed"
	logging.info  ("is other file-type")
	return "other"

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

def delivermovie(origin,Fvideodest):
	""" Delivers a fideofile in order a pertenency on a group
		input: /path/to/file.ext
		input: dictionary from TRWorkflowconfig (Fvideodest var)
		
		output: path included in Dict. It returs "" if not matches are found
		"""
	logging.debug("Delivering movie, checking:"+origin)
	destinationlist = [""]
	for a in Fvideodest:
		destinationlist.append(a)
	r1, match = filmcovermatch.matchfilm(origin,destinationlist)
	if r1 == "":
		logging.debug("No mathches found to deliver, returning default path for the item")
		return ""
	return Fvideodest[r1]

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
			("list","of","files","that","have","been","moved")
		'''
	# Checking folders:
	if itemcheck (origin) in (["","file"]):
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check TRWorkflowconfig and set up Dropboxfolder to a valid path")
	if itemcheck (dest) in (["","file"]):
		logging.critical("Path doesn't exist or it is already a file, can't continue: Please, check TRWorkflowconfig and set up Torrentinbox to a valid path")
	# We want an ending slash.... 
	if origin[-1]!="/": origin += "/"
	items = []
	newitems = glob(origin+"*")
	for i in newitems:
		if itemcheck(i) == 'file':
			for a in extensions:
				if os.path.splitext(i)[1].upper() == "."+a.upper():
					items.append(i)
	# We want an ending slash.... 
	if dest[-1]!="/": dest += "/"
	for i in items:
		name = os.path.basename(i)
		basename, extension = os.path.splitext(name)[0], os.path.splitext(name)[1].lower()
		# We freevo does not like jpeg extensions
		if extension == ".jpeg":
			extension = ".jpg"
		# new cover's name will be cleaned for better procesing
		cleanedname = namefilmcleaner.clearfilename (basename)
		copyfile(i,dest+cleanedname+extension,mode="m")
	return items

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

def TRProcess(DW_DIRECTORY, TR_TORRENT_NAME):
	""" This function process an entry from Transmission-Downloaded-items Spool
	inputs:
	DW_DIRECTORY (string):		Main path of source directory to fetch files from (DW_DIRECTORY variable from Transmission)
	TR_TORRENT_NAME (string):	Name of the item to process (file or directory) (TR_TORRENT_NAME variable from Transmission)

	Output: "" > Everithing has gone OK.
			"" > There were some problems.
	"""

	global Fvideodest

	# Dumping info to log list: we want to know wath log is for what downloaded item in case of inspection
	logging_list = os.path.dirname(logging_file)+"/Torrent Log List.log"
	if itemcheck(logging_list) != "file":
		logging.info("Initializing Logging file at:"+logging_list)
		f = open(logging_list,"w")
		f.write(";".join(["Date","Time","DW_DIRECTORY","TR_TORRENT_NAME","\n"]))
		f.close()

	f = open(logging_list,"a")
	f.write(";".join([today,tohour,DW_DIRECTORY,TR_TORRENT_NAME,"\n"]))
	f.close()

	logging.info("Start item is at:"+DW_DIRECTORY)
	logging.info("Item is:"+TR_TORRENT_NAME)
	logging.debug("Default Fmovie_Folder:"+Fmovie_Folder)
	logging.debug("Default Faudio_Folder:"+Faudio_Folder)
	logging.debug("Default Fother_Folder:"+Fother_Folder)
	logging.debug("        Dropboxfolder:"+Dropboxfolder)


	# Prequisites:
	#=============
	#1 directory paths must end in slash "/"
	DW_DIRECTORY  = addslash (DW_DIRECTORY ,"DW_DIRECTORY" )


	#2 Reading Videodestinations in ini file
	# Ini file is converted into a keyword dictionary to redirec series & movies by title. 
	# Setup your own user "Videodest.ini". you must store this .ini file at "Dropboxfolder" defined folder

	# Checking and setting up Fvideodest file:
	if itemcheck(Dropboxfolder+"Videodest.ini") == "":
		logging.warning("Videodest.ini file does not exist, setting up for the first time")
		f = open(Dropboxfolder+"Videodest.ini","a")
		f.write(startVideodestINIfile)
		f.close()
		print ("Don't forget to customize Videodest.ini file with video-destinations to automatically store them into the right place. More instructions are available inside Videodest.ini file.")

	logging.debug("Extracting alias definition from "+Dropboxfolder+"Videodest.ini")
	alias = readini.readdict (Dropboxfolder+"Videodest.ini","alias",",")

	logging.debug("Extracting dest definition")
	dest = readini.readdict (Dropboxfolder+"Videodest.ini","dest",",")

	logging.debug("Substituting dest alias")
	for a in alias:
		for b,c in dest.items():
			if "<"+a+">" in c:
				dest[b]=c.replace("<"+a+">",alias[a])

	logging.debug("Checking path inconsistences:")
	# paths in destinations must not start with "/" either end in "/"
	for a,b in dest.items():
		if len (b) > 0:
			if b[0] == "/":
				b = b [1:]
			if b[-1] == "/":
				b = b [:-1]
			dest[a] = b

	Fvideodest = dest

	#3 Itemname must not end in slash "/"
	if TR_TORRENT_NAME[-1] == "/" :
		TR_TORRENT_NAME = TR_TORRENT_NAME [:-1]
		logging.warning("..Torrent names must not end in slash:"+TR_TORRENT_NAME)

	#4 Item check:
	for a in (os.path.join(DW_DIRECTORY,TR_TORRENT_NAME), Fmovie_Folder, Faudio_Folder, Fother_Folder):
		if itemcheck(a) not in ("file","folder"):
			logging.warning(a + " does not exists or is not a file nor a folder item, please check config file or input parameters, links items are not allowed.... Exitting")
			print (a + " does not exists or is not a file nor a folder item, please check config file or input parameters, links items are not allowed\n Exitting....\n")
			exit()		
		else:
			logging.debug(a + " >> exists. OK!")

	# File Vs Folder
	#===============
	#1 Check if torrent is dir vs file
	logging.debug("Checking if downloaded item is file or directory...")
	origin = DW_DIRECTORY+TR_TORRENT_NAME
	if os.path.isfile(origin):
		logging.info (origin+" is a file.")
		procfile(origin,"c") # >> process the file.
	elif os.path.isdir (origin):
		logging.info (origin+" is a folder:")
		dest = TRprocfolder(origin)
		state = procfolder (dest) # >> process the folder contents
		if state == "3": print ("Case of sub-folder.... nothing was programmed\n")
	else:
		logging.info("ERROR: Downloaded item does not exist or item is a link to a place, nothing to do")
		print ("Item does not exist or item is a link to a place, nothing to do.\nPlease, check input parameters.")
	logging.info("Done!")
	print ("Done!\n")
	#end of file
	# TO DO: Identify numbers of cap.   three numbers is a cap + the same starting number, Then rename cap- as nXnn.
	return

def Dropfd():
	''' move torrents and covers from one destination to another.
		Pej. You can setup origin folder at /$home/Dropbox/TRinbox and 
		set a destination folder to $home/Downloads (A hot folder for Transmission)

		Destination folder is also used as a repository of covers function.
		'''
	global TRWorkflowconfig
	movelist = extfilemove (TRWorkflowconfig.Dropboxfolder, TRWorkflowconfig.Torrentinbox, ["torrent","jpg","png","jpeg"])
	if movelist == []:
		logging.debug("Nothing was in the Dropbox-hot-folder.")
	else:
		logging.info("Those files were processed: from Dropbox-hot-folder:")
		for a in movelist:
			logging.info(a)
	return movelist

def dtsp(spoolfile):
	"""
		Process torrent spool-file.
		Input: path/to/spoolfile/spoolfilename.spool

		Output: none
	"""

	logging.debug ("-------  Searching for a new Downloaded Torrent queue  -------")
	# DEVELOP SPOOL PROCESING

	# (1) Checking Spool File
	if itemcheck (spoolfile) == "":
		logging.debug("Thereis nothing to do, TorrentSpool file does not exist....")
		return

	# (2) Read pull file and putting it into a list.

	mylist = []
	while True:
		# Getting list of entries
		mypull = readini.listtags (spoolfile,"Torrent","=")
		if (mypull) == [""] :
			logging.info("There are not more files to process for now.")
			logging.info("Removing Torrent-spool-file")
			os.remove(spoolfile)
			break

		logging.info("Starting to process pull, %s entry(-ies) have been registered."%(len(mypull)))
		# Running
		for entry in mypull:
			a,b = readini.split(entry,"\t")	
			skipp = 0
			if itemcheck (a) != "folder":
				logging.warning("Folderpath in entry does not exist ("+a+"). Skipping (entry will be deleted)")
				skipp=1
			if itemcheck (os.path.join(a,b)) in ("","link") and skipp == 0:
				logging.warning("file: does not exist or is a link ("+b+"). Skipping (entry will be deleted)")
				skipp=1
			if skipp == 0:
				# Procesing Torrent
				print ("Procesing Torrent")
				TRProcess(a,b)
			# updating pull file:
			newpull = readini.listtags (spoolfile,"Torrent","=")
			newpull.remove (entry)
			# re-write spool-file
			os.remove(spoolfile)
			f = open (spoolfile,"a")
			for x in newpull:
				f.write ("Torrent="+x+"\n")
			f.close()
			
		logging.debug("An iteration on Torrent Spool file List has been procesed")
		logging.debug("Cleaning pull file & looking for more files to process.....")

	logging.debug ("-------  End of Downloaded Torrent queue  -------")
	pass

# ========================================
# ===  MAIN PROCESS                  ==========================
# ========================================

if __name__ == '__main__':
	launchstate = 0 # At first run we assume that launch state is 0 (Transmission is not launched)
	s =  TRWorkflowconfig.s # Time to sleep between checks (Dropbox folder / transmission spool)
	cmd  = TRWorkflowconfig.cmd # Command line to lauch transmission
	lsdy = TRWorkflowconfig.lsdy # List of hot folders to scan for active or new torrents
	lsext= ['.part','.torrent'] # extensions that delates a new torrent or an antive one.

	spoolfile = os.path.join (logpath, "Torrent.spool") # Spool file for incoming torrents
	
	# Main loop
	while True:
		Dropfd() # Checks Dropbox folder for .torrents and .images
		dtsp (spoolfile) # Checks Torrent.spool file
		if launchstate == 0 :
			launch = programstarter.launcher (cmd, lsdy, lsext) # Finding new .Torrents & pending torrents to start Transmission
			if launch == 1:
				logging.info("'"+cmd + "' has been executed, turning launchstate to 1")
				launchstate = 1
		logging.debug("# Done!, waiting for "+str(s)+" seconds....")
		time.sleep(s)


'''
# def emailme(msgfrom, msgsubject, msgto, textfile, msgcc=""):
	Send a mail notification.
		parameters:
			msgfrom = e-mail from
			msgsubjet = Subject (string in one line)
			msgto = mail_recipients (could be more than one parsed into a string colon (:) separated)
			textfile = path to textfile, this is the body of the message. You can pass a string anyway,
'''		
#emailme ( TRWorkflowconfig.mailsender, 'Testing mail %s' %('XXXX-1-Ññ'), 'pcasas33@gmail.com', '/home/pablo/.TRWorkflow/TRWorkflowconfig.py', 'pablolabora@gmx.es')