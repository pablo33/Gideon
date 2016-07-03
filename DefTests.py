#!/usr/bin/python3
# Test Configuration
import unittest, os, shutil
from glob import glob
import TRWorkflowV2
import datetime
import namefilmcleaner

dyntestfolder = 'TESTS'


# Tools for test file movements
def addchilddirectory(directorio):
	""" Returns a list of child directories

	Usage: addchilddirectory(directory with absolute path)"""
	paraañadir = []
	ficheros = os.listdir(directorio)
	for a in ficheros:
		item = os.path.join(directorio, a)
		if os.path.isdir(item):
			paraañadir.append(item)
	return paraañadir

def lsdirectorytree(directory):
	""" Returns a list of a directory and its child directories

	usage:
	lsdirectorytree ("start directory")
	By default, user's home directory

	Own start directory is also returned as result
	"""
	#init list to start, own start directory is included
	dirlist = [directory]
	#setting the first scan
	moredirectories = dirlist
	while len (moredirectories) != 0:
		newdirectories = moredirectories
		moredirectories = list ()
		for element in newdirectories:
			toadd = addchilddirectory(element)
			moredirectories += toadd
		dirlist += moredirectories
	return dirlist

def SetTestPack (namepack):
	namepack = os.path.join(dyntestfolder, namepack)
	# delete old contents in test(n) folder
	if os.path.isdir (namepack):
		shutil.rmtree (namepack)

	# decompress pack
	os.system ('unzip %s.zip -d %s'%(namepack, dyntestfolder))

def FetchFileSet (path):
	''' Fetchs a file set of files and folders'''
	listree = lsdirectorytree (path)
	fileset = set()
	for x in listree:
		contentlist = (glob( os.path.join (x,'*')))
		for a in contentlist:
			fileset.add (a)
	return fileset


#####TESTS########
MD = TRWorkflowV2
modulename = 'TRWorkflowV2.py'

class itemcheck_text_values (unittest.TestCase):
	'''testing itemcheck function'''
	def test_emptystring (self):
		''' an empty string returns another empty string'''
		self.assertEqual (MD.itemcheck(""),"")

	def test_itemcheck (self):
		''' only text are addmitted as input '''
		sample_bad_values = (True, False, None, 33, 3.5)
		for values in sample_bad_values:
			self.assertRaises (MD.NotStringError, MD.itemcheck, values)

	def test_malformed_paths (self):
		''' malformed path as inputs are ommited and raises an error '''
		malformed_values = ("///","/home//")
		for inputstring in malformed_values:
			self.assertRaises (MD.MalformedPathError, MD.itemcheck, inputstring)

class getappstatus (unittest.TestCase):
	""" tests is an application is running
	and gets a list of PIDs """
	known_values = (
		("transmission", False),
		("python3", True),
		)

	def test_getappstatus (self):
		for process, PIDs in self.known_values:
			result = MD.getappstatus (process)
			self.assertEqual (PIDs, result)


class TestPack1 (unittest.TestCase):
	''' processing TestPack1'''

	reftest = 'Test1'
	testfolder = os.path.join (dyntestfolder,reftest)
	hotfolder = os.path.join (testfolder,'Hotfolder')
	TRinboxfolder = os.path.join (testfolder,'TRinboxfolder')
	extensionsls = ['jpg','torrent','png', 'jpeg']

	def test_extfilemove (self):
		''' Move .torrent files and image files to a destination
			'''

		SetTestPack (self.reftest)

		known_movedfiles = set ([
					'TESTS/Test1/TRinboxfolder/Invalid Torrent For Testing Purposes.torrent',
					'TESTS/Test1/TRinboxfolder/Screenshot From 2016 07 02 11 48 40.png',
					'TESTS/Test1/TRinboxfolder/Name in Uppercase.jpg',
					'TESTS/Test1/TRinboxfolder/This Is a Jpeg File.jpg',
					])
		known_filevalues = set ([
			'TESTS/Test1/Hotfolder',
			'TESTS/Test1/Hotfolder/other documents that should remain.txt',
			'TESTS/Test1/Hotfolder/this is a folder-it should remain',
			'TESTS/Test1/TRinboxfolder',
			'TESTS/Test1/TRinboxfolder/Invalid Torrent For Testing Purposes.torrent',
			'TESTS/Test1/TRinboxfolder/Name in Uppercase.jpg',
			'TESTS/Test1/TRinboxfolder/Screenshot From 2016 07 02 11 48 40.png',
			'TESTS/Test1/TRinboxfolder/This Is a Jpeg File.jpg',
			])

		fnresult = set (MD.extfilemove (self.hotfolder,self.TRinboxfolder,self.extensionsls))
		filestructureresult = FetchFileSet (self.testfolder)
		self.assertEqual(known_movedfiles, fnresult)
		self.assertEqual(known_filevalues,filestructureresult)


#####TESTS########
MD2 = namefilmcleaner
modulename = 'namefilmcleaner.py'

class namefilmcleaner (unittest.TestCase):
	'''testing namefilmcleaner library'''
	def test_trimbetween (self):
		''' Trims a string between a pair of defined characters.
		input: "string"
		input: two characters (in order) pe. "[]"
		outputt: processed string
		'''
		wanted_values = ([
			('my testo to save [deleteme]', '[]','my testo to save '),
			('my testo to save [deleteme]', '()','my testo to save [deleteme]'),
			('my testo to save (deleteme)', '()','my testo to save '),
			('my testo to save [] me [me]', '[]','my testo to save  me '),
			('my testo to save [deleteme]', 'm]',''),
			('my testo to save [deleteme]', 'te','my s [deleme]'),
			('my testo to save [Cap 1x10][deleteme]', '[]','my testo to save -Cap 1x10-'),		
			('my testo to save [capitulo 1x10][deleteme]', '[]','my testo to save -capitulo 1x10-'),		
			])

		for i1,i2,string in wanted_values:
			result = MD2.trimbetween(i1,i2)
			self.assertEqual(result,string)

	def test_dotreplacement (self):
		'''replaces character between leters
		
		usage: dotreplacement ("string.with.some.dots.", ". ")
			input: "String.to.process"
			input: "lim" String, must contain two characters: caracter to search and character to replace with.
			output: "String to process" (procesed string)
		'''
		wanted_values = ([
			('my.testo.to.delete.dots.[deleteme]', '. ','my testo to delete dots [deleteme]'),
			('my.testoXtoXdelete.exs.[deleteme]', 'X ','my.testo to delete.exs.[deleteme]'),
			('my.testo.to.delete.exs.[deleteme]', '.-','my-testo-to-delete-exs-[deleteme]'),
			('my.', '. ','my'),
			('my..', '. ','my'),
			('my.abc.[defg].another text', '. ','my abc [defg] another text'),
			('lots of points......6 points', '. ','lots of points......6 points'),
			('lots of points.......7 points', '. ','lots of points.......7 points'),
			('lots of points...ax.....points.hey.', '. ','lots of points...ax.....points.hey'),
			])

		for i1,i2,expectedstring in wanted_values:
			result = MD2.dotreplacement(i1,i2)
			self.assertEqual(result,expectedstring)


	def test_prohibitedwords (self):
		'''  Eliminates words in text entries
			those words matches if they are between spaces.
			input: "string with some words."
			input: ['List','of','words']
			outputt: "string without this words".
		'''
		wanted_values = ([
			('my test to delete some words', ['test','words'],'my to delete some'),
			('my.test.to delete some words', ['test','words'],'my.test.to delete some'),
			('my', ['test','my'],'my'),
			(' my ', ['test','my'],' '),
			('', ['test','my'],''),
			])

		for i1,i2,expectedstring in wanted_values:
			result = MD2.prohibitedwords(i1,i2)
			self.assertEqual(result,expectedstring)


	def test_sigcapfinder (self):
		""" This little Function, scans for a chapter-counter at the end of the 
			filename, it will delete any punctuation character at the end and 
			it will also try to find numbers at the end of the filename. 
			If filename ends in three numbers, it'll change 'nnn' to 'nxnn'.
			This not affects if filename ends in four or more numbers. 'nnnn' so they are treated as a 'year'
			"""
		wanted_values = ([
			('my title 0x23','my title 0x23'),
			('my title 123','my title 1x23'),
			('my title 234-[[[','my title 2x34'),
			('my title ending in a year 1985','my title ending in a year 1985'),
			('my title 3x45-.','my title 3x45'),
			('my title Cap456-.','my title Cap456'),
			])

		for i1,expectedstring in wanted_values:
			result = MD2.sigcapfinder(i1)
			self.assertEqual(result,expectedstring)


	def test_chapid (self):
		""" Checks four last char$ of filename.
			Returns chapter number if a chapter is found.

			Chapters are idenfied with this mask :  nxnn
			"""
		wanted_values = ([
			('my title 0x23','23'),
			('my title 0X24','24'),
			('my title 0x25','25'),
			('my title capx26',''),
			('my title',''),
			('1X34','34'),
			('x34',''),
			])

		for i1,expectedstring in wanted_values:
			result = MD2.chapid(i1)
			self.assertEqual(result,expectedstring)


	def test_littlewords (self):
		''' Change little words starting uppercase to lowercase. This words must be defined.
		words = ["in","to","my", the","and","on","at","en","a","y","de","o","el","la","los","las","del", "lo", "es"]
			'''
		wanted_values = ([
			('My Title To Change And Put Little Words In Lowercase','My Title to Change and Put Little Words in Lowercase'),
			('ONCE UPON A TIME','ONCE UPON a TIME'),
			('El MONSTRUO DEL LAGO NESS','El MONSTRUO DEL LAGO NESS'),
			])

		for i1,expectedstring in wanted_values:
			result = MD2.littlewords(i1)
			self.assertEqual(result,expectedstring)



if __name__ == '__main__':
	unittest.main()

