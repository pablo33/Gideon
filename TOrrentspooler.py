#!/usr/bin/python3

""" 
	This module stores file information about downloaded torrents into text spool file.
	Text spoolfile is like this:
	Torrent=Path/to/torrent/item\titem

		item can be a file or a folder
	"""

# module import
import os, sys

# Fetching input arguments
DW_DIRECTORY = sys.argv[1] # Place where the item is (full-path)
TR_TORRENT_NAME = sys.argv[2] # Name of the item (can be a folder or a file)

# ==========================================
# ===============  Utils ===================
# ==========================================
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

# ==========================================
# ===============  Functions ===============
# ==========================================

def add_to_pull(DW_DIRECTORY,TR_TORRENT_NAME):
	""" Opens a pull file and writes a new line
	
		"""
	f = open(spoolfile,"a")
	# origin must not have any commas in the title:
	f.write("Torrent="+DW_DIRECTORY+"\t"+TR_TORRENT_NAME+"\n")
	f.close()
	return


# ==========================================
# Main code
# ==========================================

# Write downloaded torrent into the spool file.

# Getting user folder for loggin....
logpath = os.getenv('HOME')+"/.TRWorkflow/logs/"
spoolfile = addslash (logpath, "logpath")+"Torrent.spool"

if itemcheck (logpath) == "":
	os.makedirs(logpath)

add_to_pull (DW_DIRECTORY,TR_TORRENT_NAME)
