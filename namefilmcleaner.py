''' This program cleans the name-file of a film title

	it is intended to clean things like [DVDRip],
	substitute dotts that should be spaces in names or the like.
	it is composed of various functions, so you can easily change
	or add more configurations '''

# module import, normal mode
import os, logging, re, TRWorkflowconfig


# sys.path.append ('/home/pablo/python3')

__version__ = "1.2"
__date__ = "26/04/2015"
__author__ = "pablo33"
#=====================================
# Function  myfunction
#=====================================
def trimbetween(a, lim):
	''' Trims a string between a pair of defined characters.
	input: "string"
	input: two characters (in order) pe. "[]"
	outputt: processed string

	inform the argument by two caracters
	p.e.  source: "La.Espada.Magica.DVDRip.[www.DivxTotal.com].LeoParis", "[]"
	results in : "La.Espada.Magica.DVDRip..LeoParis"

	'''
	cc = 0
	while True :
		st = a.find(lim[0])
		end = a.find(lim[1])
		if st > end and end != -1:
			a = a[0:end]+"\t"+a[end+1:] # We add a tab to mark this place and restart
			continue
		if st == -1 or end == -1 or st == end :
			break
		else:
			word = a[st+1:end]
			trim = 1
			# If there is a Chapter id. we do not want to loose it >> so trim = 0
			for i in TRWorkflowconfig.chapteridentifier :
				if word.find(i) != -1 or word == i :
					a = a[0:st]+"-"+word+"-"+a[end+1:]
					trim = 0
			if trim == 1:
				a = a[0:st]+a[end+1:]
	a = a.replace("\t",lim[1]) # we substitute tabs with end limit.
	return a


def dotreplacement(a,lim):
	'''replaces character between leters
	
	usage: dotreplacement ("string.with.some.dots.", ". ")
		input: "String.to.process"
		input: "lim" String, must contain two characters: caracter to search and character to replace with.
		output: "String to process" (procesed string)
	'''
	leters = "1234567890abcdefghijklmnñopqrstuvwxyzABCDEFGHIJKLMNÑOPQRSTUVWXYZ-+*()[]_"
	while True :
		logging.debug(a)
		st = a.find(lim[0])
		if a[0] == lim[0]:
			a = lim[1]+a[1:]
		elif a[-1] == lim[0]:
			a = a[0:-1]
		elif st == -1:
			break
		elif not (a[st-1] in leters and a[st+1] in leters):
			break
		else:
			a = a[0:st]+lim[1]+a[st+1:]
	return a

def prohibitedwords(a,lista):
	'''  Eliminates words in text entries
		those words matches if they are between spaces.
		input: "string with some words."
		input: ['List','of','words']
		outputt: "string without this words".
	'''

	for pw in lista:
		# words in the middle
		x = a.upper().find(" "+pw.upper()+" ")
		if x >= 0:
			a = a[:x]+a[x+len(pw)+1:]
		# words at the end
		if len (pw)+1 < len (a):
			if a.upper().endswith(" "+pw.upper()):
				a = a[:-len(pw)-1]
		# words at the begining
		if len (pw)+1 < len (a):
			if a.upper().startswith(pw.upper()+" "):
				a = a[len(pw)+1:]
	return a

def sigcapfinder(filename):
	""" This little Function, scans for a chapter-counter at the end of the 
		filename, it will delete any punctuation character at the end and 
		it will also try to find numbers at the end of the filename. 
		If filename ends in three numbers, it'll change 'nnn' to 'nxnn'.
		This not affects if filename ends in four or more numbers. 'nnnn' so they are treated as a 'year'
		for example:

		sigcapfinder("my title 123") returns>> "my title 1x23"
		sigcapfinder("my title 123-[[[") returns>> "my title 1x23"
		sigcapfinder("my title ending in a year 1985") returns "my title ending in a year 1985"
		"""
	if filename == "":
		logging.warning("Empty filename to find chapter!")
		return filename
	base = filename
	# chapter = 0 # for now, we assume there isn't any chapter in filename.
	# we trim not wanted characters at the end:
	count = 0
	print (base)
	for a in base[::-1]:
		print ('considering char',a)
		if a in '[]-:,*+_.':
			count +=1
			print (a,">>",count)
			continue
		break
	if count != 0:
		base = base [0:-count]		
		logging.debug("namebase has changed to "+base)
		print (base)
	if base == "" or len(base) < 5:
			logging.warning("filename made of simbols or very short, returning same filename")
			return filename
	
	# finding a final identifier, cleaning odd chars before capter
	expr = '[-. ]\d[xX]\d{2}'
	mo = re.search (expr, base[-5:])
	try:
		grupo = mo.group()
	except:
		pass
	else:
		base = base[:-5]+' '+base[-4:]
		return base


	# finding 3 final numbers
	expr = '[-. ]\d{3}'
	mo = re.search (expr, base[-4:])
	try:
		grupo = mo.group()
	except:
		print ("No final counter expression was found in %s." % base)
		pass
	else:
		base = base[:-4]+' '+base[-3:-2]+'x'+base[-2:]
	return base

def chapid(item):
	''' Checks four last char$ of filename.
		Returns chapter number if a chapter is found.

		Chapters are idenfied with this mask :  'nxnn'
		input: fullpath (or not) of filename
		output: number of chapter (string) _or_
		output: ""  if no chapter is found.
		'''
	name = os.path.splitext(os.path.basename(item))[0]
	if len (name) < 4:
		logging.debug("Filename ("+name+")has less than 4 char$, there isn't a chapter identifier:")
		return ""
	tf = name[-4:]
	numbers = "1234567890"
	if not (tf[0] in numbers and tf[1].upper() == "X" and tf[2] in numbers and tf[3] in numbers):
		logging.debug("Name "+name+" has no Chapter identifier.")
		return ""
	return tf[-2:]

def littlewords(filename):
	''' Change little words starting uppercase to lowercase. This words must be defined.
		'''
	words = ["the","and","on","at","en","a","y","de","o","el","la","los","las","del", "lo", "es"]
	for a in words:
		wa=" "+a[0].upper()+a[1:]+" "
		wb=" "+a+" "
		filename = filename.replace(wa,wb)
	return filename

def clearfilename(filename):
	""" Process several filters for filename cleaning
		input: filename without extension, please
		output: filename without extension, of course
		"""
	logging.info("# Cleaning filename: "+filename)
	filenametmp = filename

	
	#1 replacing dots, underscores & half  between leters.
	filenametmp = dotreplacement(filenametmp, ". ")
	filenametmp = dotreplacement(filenametmp, "_ ")
	filenametmp = dotreplacement(filenametmp, "- ")

	#2 trimming brackets
	filenametmp = trimbetween(filenametmp, "[]")
	
	#3 Replacing prohibited words.
	
	while True:
		filenametmp2 = prohibitedwords (filenametmp,TRWorkflowconfig.prohibited_words)
		if filenametmp == filenametmp2 :
			break
		filenametmp = filenametmp2

	while True:
		loop = 0
		#4 Trimming first and last spaces
		filenametmp = filenametmp.strip()
		if filenametmp[0] == " " or filenametmp[-1] == " ":
			loop = 1
		#5 Trimming first and last dots.
		if filenametmp[-1] == ".":
			filenametmp = filenametmp [:-1]
			loop = 1
		if filenametmp[0] == ".":
			filenametmp	= filenametmp [1:]
			loop = 1
		if loop == 0 :
			break

	#6 Finding and placing a Chapter-counter
	filenametmp = sigcapfinder(filenametmp)

	#7 Formatting as Title Type
	filenametmp = filenametmp.title()

	#8 Replacing little words to lowerCase
	filenametmp = littlewords (filenametmp)
	
	return filenametmp

