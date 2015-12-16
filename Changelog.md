g_Main_: TRWorkflow.py
----------------------

OK - Finding and selecting titles to must not be Case sensitive.  
OK - Find series on folders and rename 2x01.???  
	Sleepy Hollow - Temporada 1 -Cap 101-.mkv  >>  Sleepy Hollow - Temporada 1 -Cap 1x01.mkv  
OK - A log per file  
OK - A log of logs with information of the torrent  
OK - A log cleaner no more than 50 torrents logs are allowed.   
OK - Match covers and movies.  
OK - Move downloaded files from a Drop-box folder to "Downloads Folder" wich is where Transmission gets torrents (and TR WORKFLOW finds and match covers)  
OK - Make an .INI file containing a list of destinations of downloaded torrents intead of .py config file.  
OK - Print report and send e-mail with the results of the changes. (user-log)  
OK - Alert vía e-mail on video codec value.  
OK - Bash to re-convert stored files stored into a spool  
OK - Prohibited words must not be case sensitive.  

1.5 OK - First registry into changelog. Software is Stable.

2.0 OK
- Put incoming process into a queue. So system will not be messed with many simultaneous instances. (now incoming torrents)  
- Mediaworflow.py modeule has been included into TRWorkflow.py  
- Read user home folder and put logs in $HOME/.TRWorkflow/logs  
- Modified namefilcleaner, so it deletes entire words and not partial words.  
- Auto Store config file at user config path ("$HOME/.TRWorkflow/TRworkflowconfig.py")  
- 2015/08/15 Use an idependent e-mail client. smtp.lib in python.
- 2015/12/15 Included Component diagram.
- 2015/12/16 draw the Main service activity diagram. (TRWorkflow.py)
- 2015/12/16 draw TRWorkflow - dtsp_function - Activity Diagram (process of torrent spool-file)



Improvements:

TO DO:
------------------------

Send a free-storage status by e-mail on each downloaded torrent. using Python code.

La forma de dar de alta las líneas en al torrent-spool es muy patatera. Tiene el path de la descarga de torrents fija.  


Process a folder that have one picture, and fetch it as a cover.

Send information about delivery process.

Develop case of various folders.

Procesar una cuenta de e-mail a modo de hot-folder. Tomar los torrents adjuntos o los magnets del contenido del mensaje.  



