''' INI reader
	'''

__version__ = 1.0
__date__ = "06/12/2014"
__author__ = "pablo33"

import logging

def strip(string):
	""" input a string, and this script will trim start and end spaces and/or tabs.
		"""
	while True:
		go = 1
		if len (string) > 0:
			if string[0] == " " or string[-1] == " ":
				string = string.strip()
				go = 0
				continue
			if string[0] == "\t":
				string = string [1:]
				go = 0
				continue
			if string[-1] == "\t":
				string = string [:-1]
				go = 0
				continue
		if go == 1:
			break
	return string

def split(line,var):
	""" Split a string at first $var encountered

		If not any found, returs line, ''
		"""
	lt1, lt2  = line, ""
	at = line.find(var)
	if at != -1:
		lt1 = line [:at]
		lt2 = line[at+1:]
	return lt1, lt2

def readdict(inifile,var,sep):
	""" This function reads lines from an .ini file and gets parameters 
		to 	return a dictionary

		to read an ini-file like that:
			alias=word1,result1
			alias=word2,result2

		you should call this function as:
			readdict("/pathtofile/file.ini","alias",",")

	input:
		file (path)
		var to read
		sep identifier
	output:
		a dictionary
		"""	
	mydict = {'':''}
	with open(inifile,"r") as f:
		for line in f:
			a,b = split(line[:-1],"=")
			if strip(a) == var:
				logging.debug("Found "+var+" definition line")
				logging.debug("Splitting: "+line[:-1])
				lt1, lt2 = split(b,sep)				
				#Clean empty starting and end spaces
				lt1, lt2 = strip(lt1), strip(lt2)
				#adding to dict
				mydict [lt1] = lt2
	# cleaning empty entry
	mydict.pop("",None)
	return mydict

def readparameters(inifile,param="="):
	"""This function reads parameters from a .ini and returns a dictionary
		name of parameter : value
		"""
	mydict = {'':''}
	with open(inifile,"r") as f:
		for line in f:
			if param in line:
				a,b = split(line[:-1],"=")
				logging.debug("Found: %s %s %s" %(a,param,b))
				mydict [strip(a)] = strip(b)
	# cleaning empty entry
	mydict.pop("",None)
	return mydict

def listtags(inifile,var,sep):
	""" This function reads lines from an .ini file and gets parameters 
		to 	return a list of the same Tag(alias) values.

		to read an ini-file like that:
			alias=string1
			alias=string2
			aliasX=string 3

		you should call this function as:
			readdict("/pathtofile/file.ini","alias","=")

		and you'll get:
			['string1','string2']
			# but not 'string3' so it is another alias.

	input:
		file (path)
		var to read
		sep identifier
	output:
		a list of sttrings
		"""	
	mylist = ['']
	with open(inifile,"r") as f:
		for line in f:
			a,b = split(line[:-1],sep)
			if strip(a) == var:
				#logging.debug("Found: "+line)
				#Cleaning and adding to list
				a1 , b1 = split (b,"\t")
				mylist.append (strip(a1)+"\t"+strip(b1))
	# cleaning empty entry if any registry is found
	if len (mylist) > 1:
		mylist.remove("")
	return mylist

def writedict_string(var,dict,sep=","):
	""" This function outputs a formatted string in a .ini like form.

		to write an ini-file like that:
			alias=word1,result1
			alias=word2,result2

		you should call this function as:
			writedict_string("alias",dictionary,",")
	input:
		alias
		dictionary to write
		sep identifier
	output:
		a formatted string with a new line on each key.
		"""	
	for a,b in dict.items():
		line = var+"="+a+sep+b+"\n"