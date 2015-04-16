# TRWorkflow
-------------

This program aims to process downloaded torrents, specially movies.	 


Yes, you say process, but what does this program do?


** Main functions:**

It delivers downloaded torrents by scanning its contents. I mean: stores downloaded files due to its nature and contents at pre configured folder/s. (video, audio, others)  
It cleans filenames (very useful if you are used to download and rename files)  
It can automatically remove non wanted files (pe. .txt, .url)  
It can send e-mails to notify some processes (pe. when a torrent have been downloaded)  
It starts transmission service if a new .torrent is detected into a specified folder.  
It scans a hot folder for new incoming .torrents, or covers, so you can add .torrents on the go and from mobile devices (vía Dropbox pe.)  
Scans and gets videofiles properties and stores their information as a log file. (You'l need to install mplayer).  
As videofiles can be scanned, they can be stored at a tmp-folder, and stored into a queue and send a warning e-mail. (Useful if your Hardware freezes playing videos and you need to recompress them, usually into a xVid codec) You'll need avidemux to do that.  


Well, this is good, but what about this:  
    ** Integration with freevo 1.9x / 2 **  

It can find and select the most suitable cover from a folder and match to its videofile, so Freevo can read it as its cover.  
It can detect chapter-numbers at the end of the file/s, rename then as nxnn so Freevo can group videofiles as chapters.  


** 3rd party software: **
This programs needs to run the following programs in your system:  

 * Transmission
 * Dropbox
 * Mutt (and a mail account)
 * mplayer
 * Avidemux

 ** Notes: **  

Remember to set up _TRWorkflowconfig.py_ first with your paths and preferences.  
Python3 is required to run the code.  
Tested on Ubuntu, it may not work properly in windows (I haven't tested it)  
For the moment there is not a guide to setup this program, so ask me if you want to download and run it.  

Obviously this software comes without any guaranty, so use by your own risk.
