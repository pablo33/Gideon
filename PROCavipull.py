""" Opens pull file, checks elements, send-e-mail with notification
	process files with avidemux, delete originals, notify each file,
	re-write avidemux-pull, notify the end of process.

	This process will go on until pull is empty.
	"""

__version__ = 2.0
__date__ = "05/05/2015"
__author__ = "pablo33"

import sys, os, logging


def itemcheck(a):
	if os.path.isfile(a):
	    return 'file'
	if os.path.isdir(a):
	    return 'folder'
	if os.path.islink(a):
	    return 'link'
	return ""


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
	import TRWorkflowconfig, readini
else:
	print ("There is not a config file. You must create a config file first.")
	print ("Please, run TRWorkflow.py and check your user config. ($HOME/.TRWorkflow/TRWorkflowconfig.py")
	exit()

shdown = 0 # Shutdown flag. We only shut-down the system if at least one file is processed correctly
#=== Logging Module ====

logfile = os.path.join(logpath,"process.log")

logging.basicConfig(
    level = TRWorkflowconfig.loginlevel,
    format = '%(asctime)s : %(levelname)s : %(message)s',
    filename = logfile,
    filemode = 'a', # uncomment this to overwrite log file.
)


# ======= START ================
logging.info("==================  New Start ====================")
pullfile = os.path.join(logpath,"Avidemux.pull")
if itemcheck (pullfile) == "":
	logging.info("Thereis nothing to do, Avidemux Pull file does not exist....")
	print ("Thereis nothing to do, Avidemux Pull file does not exist....")
	exit("Exiting...")

# Read pull file and put it into a dict
mylist = []
nfilesproc = 0 # number of files that have been procesed
while True:	
	mypull = readini.readdict (pullfile,"Avidemux","\t")
	# Delete items that have been processed (first time mylist is empty)
	if len (mylist) > 0:
		for a in mylist:
			mypull.pop(a,None)
	if len (mypull) == 0:
		logging.info("There are not more files to process for now.")
		logging.info("Removing pullfile")
		os.remove(pullfile)
		break
	# Updating pull-file
	f = open(pullfile,"w")
	for a,b in mypull.items():
		f.write("Avidemux="+a+"\t"+b+"\n")
		logging.debug("writed %s >>> %s in pullfile"%(a,b))
	f.close()
	# Clean list, getting items and stablish an order in new files
	mylist = []
	for a in mypull:
		mylist.append(a)
	logging.info("Starting to process pull, %s file(s) have been registered."%(len(mylist)))
	# Running
	for a in mylist:
		origin, dest = a , mypull[a]
		# Filepaths origin & dest must come without single quotes in order to work.
		# renaming items # we need to transform this strings:
		echoorigin = origin.replace("'","\'\"\'\"\'")
		echodest = dest.replace("'","\'\"\'\"\'")
				
		# Checking origin and destination:
		skipp = 0
		if itemcheck (origin) != "file":
			logging.warning("file: "+origin+" Does not exist. Skipping")
			skipp=1
		if itemcheck (dest) != "" and skipp == 0:
			logging.warning("file: "+dest+" Already exist. Skipping")
			skipp=1
		if skipp == 0:
			# Re-encoding
			print ("Launching Avidemux")
			# Notify Start 
			info = "Starting encoding %s. %s files pending for now"%(echoorigin,len(mylist)-mylist.index(a))
			os.system("echo '%s' | mutt -s 'Codificando %s' '%s'"%(info,os.path.basename(echoorigin),TRWorkflowconfig.mail_recipients))
			logging.info("Codification has started for "+origin)
			# Encoding
			os.system("avidemux --nogui --load '%s' --audio-codec COPY --video-codec Xvid --force-alt-h264 --video-conf cbr=4500 --output-format MATROSKA --save '%s' --quit"%(echoorigin,echodest))
			logging.info(dest+" converted.")
			# Check final file:
			if itemcheck(dest) == 'file':
				# Notify End
				info = "Encoding finished %s. %s files pending for now"%(echoorigin,len(mylist)-mylist.index(a)-1)
				logging.debug ("Sending mail: "+"echo '%s' | mutt -s 'Codificación de %s Completada' %s"%(info,os.path.basename(echoorigin),TRWorkflowconfig.mail_recipients))
				os.system ("echo '%s' | mutt -s 'Codificación de %s Completada' %s"%(info,os.path.basename(echoorigin),TRWorkflowconfig.mail_recipients))
				# Removig original file
				logging.debug ("removing file: "+origin)
				os.remove (origin)
				logging.info("%s file has been removed from the system."%(origin))
				shdown = TRWorkflowconfig.shdown # at least one file was procesed, the system could be shutted down.
			else:
				# Notify warning. File was not procesed at all.! 
				info = "Something happend with this file %s. Nothing was encoded, review the codification by yourself at %s. %s files pending for now"%(os.path.basename(echoorigin),os.path.dirname(echoorigin),len(mylist)-mylist.index(a)-2)
				logging.debug("Codification Error! : This file was not re-encoded:"+ origin)
				os.system("echo '%s' | mutt -s 'Codification Error!: %s' %s"%(info,os.path.basename(echoorigin),TRWorkflowconfig.mail_recipients))
				logging.info("%s file will remain on the system and deleted from Avidemux.pull"%(origin))
				errordir = os.path.join ( os.path.dirname (origin),"Error")
				errordest = os.path.join (errordir,os.path.basename(origin))
				if itemcheck (errordest) == "":
					os.renames (origin,errordest)

	logging.info("List has been procesed")
	logging.info("Cleaning pull file & looking for more files to process.....")

# Shutting Down the system
if shdown == 1 :
	logging.info("Shutting down the system.....")
	print ("The sistem is sutted down!.  OK?")
	os.system("sudo halt -p") 
