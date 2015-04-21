""" Opens pull file, checks elements, send-e-mail with notification
	process files with avidemux, delete originals, notify each file,
	re-write avidemux-pull, notify the end of process.

	This process will go on until pull is empty.
	"""

__version__ = 1.0
__date__ = "12/12/2014"
__author__ = "pablo33"

import os, logging, readini, TRWorkflowconfig

#=== Logging Module ====
global logpath

logfile = os.path.join(logpath,"process.log")

logging.basicConfig(
    level = TRWorkflowconfig.loginlevel,
    format = '%(asctime)s : %(levelname)s : %(message)s',
    filename = logfile,
    filemode = 'a', # uncomment this to overwrite log file.
)

def itemcheck(a):
	if os.path.isfile(a):
	    return 'file'
	if os.path.isdir(a):
	    return 'folder'
	if os.path.islink(a):
	    return 'link'
	return ""

# ======= START ================
logging.info("==================  New Start ====================")
pullfile = os.path.join(logpath,"Avidemux.pull")
if itemcheck (pullfile) == "":
	logging.info("Thereis nothing to do, Avidemux Pull file does not exist....")
	print ("Thereis nothing to do, Avidemux Pull file does not exist....")
	exit("Exiting...")
# Read pull file and put it into a dict
mylist = []
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
			info = "Starting encoding %s. %s files pending for now"%(a,len(mylist)-mylist.index(a))
			os.system("echo '%s' | mutt -s 'Codificando %s' '%s'"%(info,os.path.basename(origin),TRWorkflowconfig.mail_recipients))
			logging.info("Codification has started for "+origin)
			# Encoding
			os.system("avidemux --nogui --load '%s' --audio-codec COPY --video-codec Xvid --force-alt-h264 --video-conf cbr=4500 --output-format MATROSKA --save '%s' --quit"%(origin,dest))
			logging.info(dest+" converted.")
			# Notify End
			info = "Encoding finished %s. %s files pending for now"%(a,len(mylist)-mylist.index(a)-1)
			logging.debug("Sending mail: "+"echo '%s' | mutt -s 'Codificación de %s Completada' %s"%(info,os.path.basename(origin),TRWorkflowconfig.mail_recipients))
			os.system("echo '%s' | mutt -s 'Codificación de %s Completada' %s"%(info,os.path.basename(origin),TRWorkflowconfig.mail_recipients))
			# Removig original file
			logging.debug("removing file: "+origin)
			os.remove(origin)
			logging.info("%s file has been removed from the system."%(origin))
	logging.info("List has been procesed")
	logging.info("Cleaning pull file & looking for more files to process.....")

# Shutting Down the system
if TRWorkflowconfig.shdown == 1 :
	logging.info("Shutting down the system.....")
	os.system("sudo halt -p")
