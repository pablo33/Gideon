#!/usr/bin/python3
# Test Configuration
import unittest, os, shutil
from glob import glob
import TRWorkflowV2
import datetime

dyntestfolder = 'TESTS'


# Tools
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
					'TESTS/Test1/TRinboxfolder/Name In Uppercase.jpg',
					'TESTS/Test1/TRinboxfolder/This Is a Jpeg File.jpg',
					])
		known_filevalues = set ([
			'TESTS/Test1/Hotfolder',
			'TESTS/Test1/Hotfolder/other documents that should remain.txt',
			'TESTS/Test1/Hotfolder/this is a folder-it should remain',
			'TESTS/Test1/TRinboxfolder',
			'TESTS/Test1/TRinboxfolder/Invalid Torrent For Testing Purposes.torrent',
			'TESTS/Test1/TRinboxfolder/Name In Uppercase.jpg',
			'TESTS/Test1/TRinboxfolder/Screenshot From 2016 07 02 11 48 40.png',
			'TESTS/Test1/TRinboxfolder/This Is a Jpeg File.jpg',
			])

		fnresult = set (MD.extfilemove (self.hotfolder,self.TRinboxfolder,self.extensionsls))
		filestructureresult = FetchFileSet (self.testfolder)
		self.assertEqual(known_movedfiles, fnresult)
		self.assertEqual(known_filevalues,filestructureresult)


if __name__ == '__main__':
	unittest.main()

