# Gideon
-------------

This program aims to automate the process of renaming, classifying, copying and taking care of downloaded torrents, specially movies.	



** Main functions:**

It delivers downloaded torrents by scanning its contents. I mean: stores downloaded files due to its nature and contents at pre-configured folder/s. (video, audio, others)  
It cleans filenames (very useful if you are used to download and rename files)  
It can automatically remove non wanted files (pe. .txt, .url)  
It can send e-mails to notify some done processes (pe. when a torrent have been downloaded)  
It scans a hot folder for new incoming .torrents, or covers, so you can add .torrents on the go and from mobile devices (vía Dropbox pe.)  
It starts transmission service if new .torrents are detected into a specified folder.  
It avoids file copying processes while playing movies.  
It deletes delivered torrents due to a retention period of time.


**Integration with freevo 1.9x**  

It can find and select the most suitable cover from a repository folder and match to its videofile, so Freevo can read it as its cover.  
It can detect chapter-numbers at the end of the file/s, and rename them as nxnn so Freevo can group videofiles as chapters.  


** 3rd party software: **
This programs needs to run the following programs in your system:  

 * Transmission, with rpc API for python3
 * Dropbox (optional)

 ** Notes: **  

Remember to set up _TRWorkflowconfig.py_ first with your paths and preferences.  
Python3 is required to run the code.  
Tested on Ubuntu, it may not work properly in windows  
For the moment there is not a guide to setup this program, so ask me if you want to download and run it.  

Obviously this software comes without any guaranty, so use by your own risk.
