_Main_: TRWorkflow.py
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
- Put incoming process into a queue. So system will not be overloaded with many simultaneous instances. (now incoming torrents)  
- Mediaworflow.py has been included into TRWorkflow.py  
- Read user home folder and put logs in $HOME/.TRWorkflow/logs  
- Modified namefilcleaner, so it deletes entire words and not partial words.  
- 

Improvements:


TO DO:
------------------------
Namefilm cleaner:
    names ended in four digits are not chapters: pe:  "Karate Kid 1984"  
    endings great than 19xx are not chapters, they are trated as years.  
    


Use an idependent e-mail client. (¿python?)

