#!/bin/sh 
sleep 1

# For testing purposes=========================
# Enviromental variables from Transmission:
#    TR_APP_VERSION
#    TR_TIME_LOCALTIME
#    TR_TORRENT_DIR
#		(this is only the temporal downloading path)	
#    TR_TORRENT_HASH
#    TR_TORRENT_ID
#    TR_TORRENT_NAME
#		(thie is the torrent name (file or folder), it not include fullpath.

cd $HOME/.freevo/start
# Launching auto-archive workflow
# ===============================
# This program sends a notification mail, copies downloaded file to a definitive storage folder an cleans the main filename.
python3 TOrrentspooler.py """$TR_TORRENT_NAME"""
