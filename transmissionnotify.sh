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
# DW_DIRECTORY="/home/pablo/transmission/"
# TR_TORRENT_NAME="Star Wars Rebels - Temporada 1 [HDTV][Cap.104][Español Castellano]"

# Mail notification...
# ==============================
# Path of download folder is needed
DW_DIRECTORY="/home/pablo/transmission/" #Please include final slash
MAILTO="manmesanchez74@gmail.com" # one or more recipients in "To"
CCMAILTO="-c pablolabora@gmx.es" # one or more recipients in "CC Copy"

# Composing body text & log
cd /home/pablo/.freevo/start/
echo "Contenido de la descarga:" > lasttorrent.log
echo "===================================================" >> lasttorrent.log
ls "$DW_DIRECTORY$TR_TORRENT_NAME" -h -R -1 >> lasttorrent.log
echo "" >> lasttorrent.log
echo "== Información sobre la unidad de almacenamiento ==" >> lasttorrent.log
df -h /dev/sda1 >> lasttorrent.log
echo "===================================================" >> lasttorrent.log

# Notification
echo "Felicidades, $TR_TORRENT_NAME se ha descargado correctamente!" | mutt -s "Torrent descargado: $TR_TORRENT_NAME" -i lasttorrent.log $CCMAILTO $MAILTO

# Launching auto-archive workflow
# ===============================
# This program copies downloaded file to a definitive storage folder an cleans the main filename.
python3 TOrrentspooler.py """$DW_DIRECTORY""" """$TR_TORRENT_NAME"""

