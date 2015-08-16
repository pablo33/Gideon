#!/usr/bin/python3

""" 
	This module stores file information about downloaded torrents into text spool file.
	Text spoolfile is like this:
	Torrent=Path/to/torrent/item\titem

		item can be a file or a folder
	"""


# module import
import os, sys
from email.mime.text import MIMEText
from TRWorkflow import emailme
from glob import glob

# ==========================================
# ===============  Utils ===================
# ==========================================

def itemcheck(a):
	if os.path.isfile(a):
	    return 'file'
	if os.path.isdir(a):
	    return 'folder'
	if os.path.islink(a):
	    return 'link'
	return ""

# config import
userpath = os.path.join(os.getenv('HOME'),".TRWorkflow")
userconfig = os.path.join(userpath,"TRWorkflowconfig.py")
logpath =  os.path.join(userpath,"logs")
spoolfile = os.path.join (logpath, "Torrent.spool") # Spool file for incoming torrents

if itemcheck (logpath) != "folder":
	os.makedirs(logpath)
logging_file = os.path.join(logpath,"TRworkflow.log")

# loading user preferences
if itemcheck (userconfig) == "file":
	print ("Loading user configuration....")
	sys.path.append(userpath)
	import TRWorkflowconfig
else:
	print ("There is not a config file. You must create a config file first.")
	print ("Please, run TRWorkflow.py and check your user config. ($HOME/.TRWorkflow/TRWorkflowconfig.py")
	exit()

# ==========================================
# ===============  Functions ===============
# ==========================================

def add_to_pull(TR_DW_DIRECTORY,TR_TORRENT_NAME):
	""" Opens a pull file and writes a new line
	
		"""
	global spoolfile
	f = open(spoolfile,"a")
	# origin must not have any commas in the title:
	f.write("Torrent="+TRWorkflowconfig.TR_DW_DIRECTORY+"\t"+TR_TORRENT_NAME+"\n")
	f.close()
	return


# ==========================================
# ==============  Main code  ===============
# ==========================================

# Fetching input arguments
TR_TORRENT_NAME = sys.argv[1] # Name of the item (can be a folder or a file)
TR_item = os.path.join( TRWorkflowconfig.TR_DW_DIRECTORY, TR_TORRENT_NAME)

# From user configuration:
#TRWorkflowconfig.TR_DW_DIRECTORY
#TRWorkflowconfig.TR_MAILTO
#TRWorkflowconfig.TR_CCMAILTO

# Send notification
msgtext = "New torrent downloaded: %s \n\n" %(TR_TORRENT_NAME)

	# Read and add contents to msg 
if itemcheck (TR_item) == 'folder':
	msgtextmp = "Contents: of %s \n================================================\n" %(TR_TORRENT_NAME)
	mycontents = glob (TR_item + '/*.*' )
	mycontents.sort()
	for a in mycontents:
		msgtextmp += str(a) + "\n"
else:
	msgtextmp = " Torrent is just one file."
msgtext += msgtextmp + "\n\n"


	# enviar e-mail
emailme (TRWorkflowconfig.mailsender, "Torrent Descargado: " + TR_TORRENT_NAME, TRWorkflowconfig.TR_MAILTO, msgtext, TRWorkflowconfig.TR_MAILTOCC)


	# Write downloaded torrent into spool file.
add_to_pull (TRWorkflowconfig.TR_DW_DIRECTORY,TR_TORRENT_NAME)