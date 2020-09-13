#!/usr/bin/python3
# Test Configuration
import unittest, os, shutil, datetime
from glob import glob
import Gideon

dyntestfolder = Gideon.dyntestfolder


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
MD = Gideon

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

class TestPack2_CoverServiceA (unittest.TestCase):
	''' processing TestPack2, Cover Service'''

	reftest = 'Test2'
	testfolder = os.path.join (dyntestfolder,reftest)
	Videofolder = os.path.join (testfolder,'VideoFolder')
	Imagerepos = os.path.join (testfolder,'Imagerepos')

	SetTestPack (reftest)

	def test_selectcover(self):
		''' Selects the most suitable cover due on film-filename.
		covers are fetched from a folder, all of them at the same level.
			'''
		known_values = (
			('JJ_This is a video of Jack Smith with no cover.avi','Cover for Jack Smith video.png'),
			('This is a serie of Grijander with no cover 1x.avi','Cover for serie of Grijander.png'),
			('Secret Agent.avi',''),
			)
		for filename, cover in known_values:
			result = MD.selectcover (filename, self.Imagerepos)
			print ("\n\tSelecting a suitable cover for:",filename)
			self.assertEqual (cover, result)

	def test_listcovers(self):
		''' Return a list of covers-files
			input: relative path, or full-path
			output: list of image-files with relative or full-path
			'''
		known_values = [
			'Cover for Jack Smith video.png',
			'Cover for serie of Grijander.png',
			'a picture for nothing.png',
			'spare cover.png',
			]
		result = MD.listcovers (self.Imagerepos)
		self.assertEqual (set(known_values), set(result))

	def test_VideoSACFilelist(self):
		''' Look for videfiles with no associated cover '''

		known_filevalues = set ([
			'TESTS/Test2/VideoFolder/subfolder/Secret Agent.avi',
			'TESTS/Test2/VideoFolder/JJ_This is a video of Jack Smith with no cover.avi',
			])

		result = MD.VideoSACFilelist (self.Videofolder)
		self.assertEqual (known_filevalues, result)

class TestPack2_CoverServiceB (unittest.TestCase):
	''' processing TestPack2, Cover Service'''

	reftest = 'Test2'
	testfolder = os.path.join (dyntestfolder,reftest)
	Videofolder = os.path.join (testfolder,'VideoFolder/')
	Imagerepos = os.path.join (testfolder,'Imagerepos/')
	inivideodest = os.path.join (dyntestfolder,'Videodest.ini_textfile.ini')

	SetTestPack (reftest)

	def test_CoverService (self):
		''' Look for, assign and move cover files.'''

		known_filevalues = set ([
			'TESTS/Test2/Imagerepos',
			'TESTS/Test2/Imagerepos/a picture for nothing.png',
			'TESTS/Test2/Imagerepos/spare cover.png',
			'TESTS/Test2/Imagerepos/Cover for serie of Grijander.png',
			'TESTS/Test2/VideoFolder',
			'TESTS/Test2/VideoFolder/AAThis is a video with a cover.jpg',
			'TESTS/Test2/VideoFolder/AAThis is a video with a cover.mpeg',
			'TESTS/Test2/VideoFolder/JJ_This is a video of Jack Smith with no cover.avi',
			'TESTS/Test2/VideoFolder/JJ_This is a video of Jack Smith with no cover.png',
			'TESTS/Test2/VideoFolder/subfolder',
			'TESTS/Test2/VideoFolder/subfolder/Secret Agent.avi',
			'TESTS/Test2/VideoFolder/subfolder/This is a serie with a cover 2x.png',
			'TESTS/Test2/VideoFolder/subfolder/This is a serie with a cover 2x01.avi',
			'TESTS/Test2/VideoFolder/subfolder/This is a serie with a cover 2x02.avi',
			'TESTS/Test2/VideoFolder/subfolder/This is a serie with a cover 2x03.avi',
			'TESTS/Test2/VideoFolder/subfolder/This is a serie with a cover 2x04.avi',
			'TESTS/Test2/VideoFolder/This is a serie of Grijander with no cover 1x01.avi',
			'TESTS/Test2/VideoFolder/This is a serie of Grijander with no cover 1x02.avi',
			'TESTS/Test2/VideoFolder/This is a serie of Grijander with no cover 1x03.avi',
			'TESTS/Test2/VideoFolder/This is a serie of Grijander with no cover 1x04.avi',
			])

		MD.CoverService (self.Videofolder, self.Imagerepos, self.inivideodest)
		filestructureresult = FetchFileSet (self.testfolder)
		self.assertEqual(known_filevalues,filestructureresult)

class getrecipients (unittest.TestCase):
	""" given a topic, return a set of associated recipients """
	mail_topic_recipients = {
	'someonemail@gmx.es' 		: set([1,2,3,4,5,6,7,8,9,10]),
	'manme.xx33@gmail.com' : set([7,]),
	'one@gmail.com:another@hotmail.com' : set([3,]),
	}

	known_values = 	(
		(1,	set(['someonemail@gmx.es'])),
		(7,	set(['someonemail@gmx.es','manme.xx33@gmail.com'])),
		(3,	set(['someonemail@gmx.es','one@gmail.com:another@hotmail.com'])),
		(0,	set()),
		)

	def test_getrecipients(self):
		for topic, target in self.known_values:
			result = MD.getrecipients (topic, self.mail_topic_recipients)
			self.assertEqual (target, result)	

class Relatedcover (unittest.TestCase):
	'''Return the possiblecovers for an item '''
	known_values = (
		("filename.avi", set(['filename.jpg','filename.png'])),
		("filename1x01.avi", set(['filename1x.jpg','filename1x.png'])),
		("filename3x33.avi", set(['filename3x.jpg','filename3x.png'])),
		("a/full/path/to/filename.avi", set(['a/full/path/to/filename.jpg','a/full/path/to/filename.png'])),
		)
	def test_Relatedcover (self):
		for example, target in self.known_values:
			result = MD.Relatedcover (example)
			self.assertEqual (target, result)	

class Selectcase (unittest.TestCase):
	""" Selects a case to deliver the torrent files and an operational behaviour for files.
		Actual Matrix represents:
		[0] nfiles
		[1] nvideos
		[2] naudios
		[3] nnotwanted
		[4] ncompressed
		[5] nimagefiles
		[6] nother
		[7] nebook
		[8] ncomic

		[9] nfolders
		[10] folderlevels
		"""
	known_values = (
		(1,[0,0,0,0,0,0,0,0,0,  0,0], None , 0),
		(2,[1,1,0,0,0,0,0,0,0,  1,1], None , 1),
		(3,[60,1,0,55,0,4,0,0,0,  1,1], None, 2),
		(4,[25,0,13,0,0,1,0,0,0,  1,1], None, 3),
		(5,[26,0,13,1,0,1,0,0,0,  1,1], None, 3),
		(6,[26,0,13,1,0,1,0,0,0,  1,1], 'Telegram', 3),
		(7,[27,0,13,1,0,1,1,0,0,  1,1], None, 0),
		(8,[27,0,13,1,0,1,1,0,0,  1,1], 'Telegram', 4),  # If there is a no suitable case, and inputtype is 'Telegram', then Case is 4
		(9,[4,0,0,3,1,0,0,0,0, 1,1], None, 0),  # Compressed file
		(10,[1,0,0,0,0,0,0,1,0, 1,1], 'Telegram', 6),  # e-book file
		(11,[1,0,0,0,0,0,0,1,0, 1,1], None, 6),  # e-book file
		(12,[1,0,0,0,0,0,0,0,1, 1,1], 'Telegram', 5),  # Comic file file
		(13,[61,0,61,0,0,0,0,0,0, 6,2], None, 7),  # Audio files in a discography
		(14,[313,0,226,0,0,87,0,0,0, 37,4], None, 7),  # Audio files in a discography
		(15,[2,2,0,0,0,0,0,0,0 ,1,1], None, 9), # One folder with two or more videos videos.
		)
	def test_Selectcase (self):
		for testID, example, inputtype, target in self.known_values:
			M = MD.Matrix(testID)

			M.nfiles = example[0]
			M.nvideos = example[1]
			M.naudios = example[2]
			M.nnotwanted = example[3]
			M.ncompressed = example[4]
			M.nimagefiles = example[5]
			M.nother = example[6]
			M.nbooks = example[7]
			M.ncomics = example[8]
			
			M.nfolders = example[9]
			M.folderlevels = example[10]

			print (testID,end='-')
			result = MD.Selectcase (M, inputtype)
			self.assertEqual (target, result[0])

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
		(["transmission-gtkX"], False),
		(["python3"], True),
		(["transmission-gtkX","python3"], True),
		(["transmission-gtkX","pythonX"], False),		
		)

	def test_getappstatus (self):
		for process, status in self.known_values:
			result = MD.getappstatus (process)
			self.assertEqual (status, result)

class fileclasify (unittest.TestCase):
	""" Tipify a file by its extension
		"""
	known_values = (
		("filename.avi", 'video' ),
		("filename.mp3", 'audio' ),
		("filename.txt", 'notwanted' ),
		("filename.jpg", 'image' ),
		("filename.rar", 'compressed' ),
		("filename.xxx", 'other' ),
		("filename.epub", 'ebook' ),
		("filename.MOBI", 'ebook' ),
		("filename.mobi", 'ebook' ),
		("filename.cbr", 'comic' ),
		)
	def test_addmatrix (self):
		for example, target in self.known_values:
			result = MD.fileclasify (example)
			self.assertEqual (target, result)

class test_nextfilenumber (unittest.TestCase):
	""" test for nextfilenumber function """
	known_values = (
		("file.jpg", 		"file(0).jpg"),
		("file1.jpg", 		"file1(0).jpg"),
		("file(0).jpg", 	"file(1).jpg"),
		("file(222).jpg", 	"file(223).jpg"),
		("file33", 			"file33(0)"),
		("file(33)", 		"file(34)"),
		("file(-1)", 		"file(-1)(0)"),
		("file.",			"file(0)."),
		("file(10).", 		"file(11)."),
		("file(X).jpg", 	"file(X)(0).jpg"),
		)
	def test_known_input (self):
		for inputfile, outputfile in self.known_values:
			result = MD.nextfilenumber (inputfile)
			self.assertEqual (outputfile, result)
	def test_mad_values (self):
		self.assertRaises (MD.EmptyStringError, MD.nextfilenumber, "")
		pass	

class test_getaliaspaths (unittest.TestCase):
	""" test for nextfilenumber function """
	testfile = dyntestfolder+"/Videodest.ini_textfile.ini"

	aliasdict = {
		'Sleepy Hollow temporada 1': 'series/Sleepy Hollow Temp 1',
		'Sleepy Hollow temporada 2': 'series/Sleepy Hollow Temp 2',
		'star wars rebels': 'Series infantiles',
		'a level up':'../Novedades',
			}


	def test_known_input (self):
		result = MD.getaliaspaths (self.testfile)
		self.assertEqual (self.aliasdict, result)

class test_Getsubpath (unittest.TestCase):
	""" returns the besta matched sub-path by matching strings on a list"""
	aliasdict = {
		'Sleepy Hollow temporada 1': 'series/Sleepy Hollow Temp 1',
		'Sleepy Hollow temporada 2': 'series/Sleepy Hollow Temp 2',
		'star wars rebels': 'Series infantiles'
			}

	known_values = (
		("a name with no match",		 		("",0)),
		("Sleepy Hollow temp 1", 				("series/Sleepy Hollow Temp 1",13)),
		("Sleepy Hollow temporada 2", 			("series/Sleepy Hollow Temp 2",22)),
		("temporada 2", 						("series/Sleepy Hollow Temp 2",10)),
		("Star   rebels   wars", 				("Series infantiles",14)),
		)
	def test_known_input (self):
		for filmname, matched in self.known_values:
			result = MD.Getsubpath (filmname,self.aliasdict)
			self.assertEqual (matched[0], result[0])

class test_matchfilm (unittest.TestCase):
	""" returns the besta matched sub-path by matching strings on a list"""
	matchlist = [
		'a path/Sleepy Hollow temporada 1.jpg',
		'Sleepy Hollow temporada 2',
		'star wars rebels',
		'Jurassic Park 1.jpg',
		'Jurassic Park 2 - Los mundos perdidos.jpg',
		'Jurassic Park 3.jpg',
		'La casa de la pradera.jpg',
		'Carátula de Zambezia.jpg',
		'el hombre araña llamado spiderman 2.jpg',
			]

	known_values = (
		("a name with no match",		 		("",0)),
		("Sleepy Hollow 1",		 				("a path/Sleepy Hollow temporada 1.jpg",0)),
		("sLeePy 2 temporada",			 		("Sleepy Hollow temporada 2",0)),
		("star",		 						("star wars rebels",0)),
		("wars rebels",		 					("star wars rebels",0)),
		("Jurassic Park 1",		 				("Jurassic Park 1.jpg",0)),
		("Jurassic Park 2",		 				("Jurassic Park 2 - Los mundos perdidos.jpg",0)),
		("Jurassic Park 3",		 				("Jurassic Park 3.jpg",0)),
		("La cosa de hacer",		 			("",0)),
		("Zambezia",		 					("Carátula de Zambezia.jpg",0)),
		("Spiderman 2",		 					("el hombre araña llamado spiderman 2.jpg",0)),

		)
	def test_known_input (self):
		for filmname, matched in self.known_values:
			result = MD.matchfilm (filmname,self.matchlist)
			print ('Matched film:', filmname, result)
			self.assertEqual (matched[0], result[0])

class TestPack3 (unittest.TestCase):
	''' processing TestPack3'''

	reftest = 'Test3'
	testfolder = os.path.join (dyntestfolder,reftest)
	hotfolder = os.path.join (testfolder,'Telegram Desktop')
	Downloadfolder = os.path.join (testfolder,'Downloads')

	SetTestPack (reftest)


	def test_fileinuse (self):
		""" Scans a folder for files.
			Returns True if any file is in use (is being writted)
			Otherwise returns False
			"""		
		# open a file:
		testfilepath = os.path.join (self.testfolder, "fileinuse.txt")
		f = open(testfilepath,"a")  #opens file with name of "test.txt"
		f.write("This file is now opened and i'm writting on it \n")
		self.assertEqual (MD.fileinuse(testfilepath), True)  # Checks a file that it is beign written.
		self.assertEqual (MD.folderinuse(self.testfolder), True)  # Checks if any file inside the folder is beign used.
		f.close()
		self.assertEqual (MD.fileinuse(testfilepath), False)  # Cheks a file that it is closed.
		self.assertEqual (MD.folderinuse(self.testfolder), False)


	def test_Telegramfd (self):
		""" Checks a folder content and returns its pointers to be added to process.
		As content for this folders usually are downloaded or copied,
		this function will check the size and the last modification time in order to
		return the pack.
		It will treat folders and files as inputs.
		compressed files will be ignored, as they sometimes are multifile and have passwords.
		"""
		# This file is delivered openned while this test.
		testfilepath = os.path.join (self.hotfolder, "fileinuse.txt")
		f = open(testfilepath,"a")  #opens file with name of "test.txt"
		f.write("This file is now opened and i'm writting on it \n")


		known_values = set ([
			('TESTS/Test3/Telegram Desktop/Printer output.pdf', '.file'),
			('TESTS/Test3/Telegram Desktop/This is a Zero avi file.avi', '.file'),
			('TESTS/Test3/Telegram Desktop/File not in use.CBR', '.file'),
			('TESTS/Test3/Telegram Desktop/This is a dummy rar file.rar', '.rar'),
			])

		Entries = MD.Telegramfd (self.hotfolder)
		self.assertEqual (known_values, set(Entries))

		f.close ()

	def test_Retrievefilesdict (self):
		""" Given a pointer, returns a dictionary with its contents """

		known_values = (
				(
					('TESTS/Test3/Telegram Desktop/File not in use.CBR','.file'),
					{0: {'name': 'File not in use.CBR', 'size': 0}},
					),
				(	
					('TESTS/Test3/Emptyfoldertest/This is a folder', '.folder'),
					{0: {'name': 'This is a folder/Videofile.avi', 'size': 0},
					 1: {'name': 'This is a folder/Text Document.txt', 'size': 64},
					 2: {'name': 'This is a folder/Subfolder to analyze/Document in a sub-folder.txt', 'size': 410}},
					)
					)
		for testvalue, goal in known_values:
			Fullfilepath, Filetype = testvalue
			itemdict = MD.Retrievefilesdict (Fullfilepath, Filetype)
			self.assertEqual (len (goal), len (itemdict))
			for key in goal:
				self.assertEqual (itemdict[key],goal[key])

	def test_CleanEmptyFolders (self):
		""" Given an upper folder, it scans and deletes empty subdirectories and the upper level
		if it is also empty """

		known_values = (
			('TESTS/Test3/Emptyfoldertest/An empty folder', False),
			('TESTS/Test3/Emptyfoldertest/This is a folder', True),
		)

		for testvalue, goal in known_values:
			MD.CleanEmptyFolders (testvalue)
			result = os.path.exists (testvalue)
			print (testvalue)
			self.assertEqual (goal,result)

class test_Utils_Functions (unittest.TestCase):
	"""Testing inputs and outputts """

	def test_toHumanSizeReadable (self):

		known_values=(
			(500,'500 bytes'),
			(0,'0 bytes'),
			(945, '945 bytes'),
			(356900, '357 Kb'),
			(500000, '500 Kb'),
			(356345333, '356.3 Mb'),
			(1345333, '1.3 Mb'),
			(988345333, '1.0 Gb'),
			(1233987654, '1.2 Gb'),
			)

		for Vinput, expected in known_values:
			result = MD.toHumanSizeReadable (Vinput)
			#print (Vinput,">>",result)
			self.assertEqual (expected, result)			



#####TESTS########
MD2 = Gideon

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
			('lots of points......6 points', '. ','lots of points .....6 points'),
			('lots of points.......7 points', '. ','lots of points ......7 points'),
			('lots of points...ax.....points.hey.', '. ','lots of points ..ax.....points.hey'),
			('No point is there', '. ','No point is there'),
			('One final point is here.', '. ','One final point is here'),
			('Hey temporada 1 capitulo 1.www_.Somedominio.com', '_.','Hey temporada 1 capitulo 1.www..Somedominio.com'),
			('Mar.Gente.Of_.A.H.I.L.D.N-4x16.HDTV_.XviD_.www_.SomeDominio.com_', '_.','Mar.Gente.Of..A.H.I.L.D.N-4x16.HDTV..XviD..www..SomeDominio.com'),
			('', '. ',''),
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
			('1my test to delete some words', ['test','words'],'1my to delete some'),
			('2my.test.to delete some words', ['test','words'],'2my.test.to delete some'),
			('3my.test.to delete some final url Www.DivxTotal.com', ['www.divxtotal.com','words'],'3my.test.to delete some final url'),
			('4my.test.to delete (some) [nonwanted] words enclosed', ['some','nonwanted'],'4my.test.to delete words enclosed'),
			('my', ['test','my'],'my'),
			(' my ', ['test','my'],' '),
			('', ['test','my'],''),
			])

		for i1,i2,expectedstring in wanted_values:
			result = MD2.prohibitedwords(i1,i2)
			self.assertEqual(result,expectedstring)

	def test_prohibitedchunks (self):
		'''  Eliminates chunks in text entries
			those chunks of text matches always and are not case sensitive.
			input: "string with some text."
			input: ['List','of','text']
			outputt: "string with some .".
		'''
		wanted_values = ([
			('1my TesT to delete some words', ['test','words'],'1my  to delete some '),
			('title@cinemaquest', ['@cinema'], 'titlequest'),
			('1my test to delete some words', ['test','words'],'1my  to delete some '),
			('2my.test.to delete some words', ['test','words'],'2my..to delete some '),
			('3my.test.to delete some final url Www.DivxTotal.com', ['www.divxtotal.com','words'],'3my.test.to delete some final url '),
			('4my.test.to delete (some) [nonwanted] words enclosed', ['some','nonwanted'],'4my.test.to delete () [] words enclosed'),
			('my', ['test','my'],''),
			(' my ', ['test','my'],'  '),
			('', ['test','my'],''),
			])

		for i1,i2,expectedstring in wanted_values:
			result = MD2.prohibitedchunks (i1,i2)
			self.assertEqual(result,expectedstring)


	def test_Chapterfinder (self):
		""" This little Function, scans for a chapter-counter, 
			it will delete any punctuation characters if it is at the end of the filename (if any)
			it will also try to find numbers at the end of the filename. 
			If filename ends in three numbers, it'll change 'nnn' to 'nxnn'.
			This not affects if filename ends in four or more numbers. 'nnnn' so they are treated as a 'year'
			It will find expressions like nnxnn and return the chapter or None, in case it is not found.
			"""
		wanted_values = ([
			('my title 0X23',				('My Title 0x23', '0x23', 'My Title')),
			('1x35my title 3x33',			('1x35.My Title 3X33', '1x35', None)),
			('My serie1x55my title',		('My Serie 1x55.My Title', '1x55', 'My Serie')),
			('my title 123',				('My Title 1x23', '1x23', 'My Title')),
			('my title 234-[[[',			('My Title 2x34', '2x34', 'My Title')),
			('ending in a year 1985',		('Ending in a Year 1985', None, None)),
			('my title 3x45-.',				('My Title 3x45', '3x45', 'My Title')),
			('my title Cap456-.',			('My Title ep456', 'ep456', 'My Title')),
			('my serie 2x33.and a subtitle',('My Serie 2x33.and a Subtitle', '2x33', 'My Serie')),
			('serie ep01',					('Serie ep01', 'ep01', 'Serie')),
			('serie EP02',					('Serie ep02', 'ep02', 'Serie')),
			('serie s2e1',					('Serie s2e1', 's2e1', 'Serie')),
			('serie s02E01',				('Serie s02e01', 's02e01', 'Serie')),
			('serie ep33 something',		('Serie ep33.Something', 'ep33', 'Serie')),
			('serie s33_e45',				('Serie s33.e45', 's33.e45', 'Serie')),
			('Serie temporada456',			('Serie Temporada456', None, None)),
			('Serie 456.__',				('Serie 4x56', '4x56', 'Serie')),
			('alg1x02.titulo456',			('Alg 1x02.Titulo456', '1x02', 'Alg')),
			('algo1x02',					('Algo 1x02', '1x02', 'Algo')),
			('alg1x02.titulo456',			('Alg 1x02.Titulo456', '1x02', 'Alg')),
			('LaZona 1x02',					('Lazona 1x02', '1x02', 'Lazona')),
			('LaZona Temporada 2 cap.3',	('Lazona 2x03', '2x03', 'Lazona')),
			('LaZona Chapter3 temporada4',	('Lazona 4x03', '4x03', 'Lazona')),
			('LaZona Temp2 cap3',			('Lazona 2x03', '2x03', 'Lazona')),
			('Chance temporada 1 capitulo 1.www_.DivxTotaL.com',	('Chance 1x01', '1x01', 'Chance')),
			])

		for i1,expectedtuple in wanted_values:
			result = MD2.Chapterfinder(i1)
			self.assertEqual(result,expectedtuple)

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
		DefTest >> OK	'''
		wanted_values = ([
			('My Title To Change And Put Little Words In Lowercase','My Title to Change and Put Little Words in Lowercase'),
			('ONCE UPON A TIME','ONCE UPON a TIME'),
			('El MONSTRUO DEL LAGO NESS','El MONSTRUO DEL LAGO NESS'),
			])

		for i1,expectedstring in wanted_values:
			result = MD2.littlewords(i1)
			self.assertEqual(result,expectedstring)

	def test_clearfilename (self):
		''' Process several filters for filename cleaning
		input: filename without extension, please
		output: filename without extension, of course
			'''
		wanted_values = ([
			('Change temporada 1 capitulo 1.www_.somedomain.com','Change Temporada 1 Capitulo 1 Somedomain'),
			('VelsMAR.Gente.Of_.S.H.E.L.D.O.M-4x16.HDTV_.XviD_.www_.somedomain.com_','Velsmar Gente of S H E L D o M 4X16 Somedomain'),
			('08 Z. La ciudad perdida DVDRip www.DivxTotaL.com','08 Z. la Ciudad Perdida'),
			('Savva. El corazón del guerrero (microHD) (EliteTorrent.net)','Savva. el Corazón del Guerrero'),
			('LaZona_101_www.DivxTotaL.com','Lazona 101'),			
			])

		for i1,expectedstring in wanted_values:
			result = MD2.clearfilename(i1)
			self.assertEqual(result,expectedstring)

	def test_GetPasswordFromFilename (self):
		''' Fetch the text after the last @ symbol and before a symbol (' .-_~#,;: ').
		Returns an empty string if @ is the last character or there is not @ present
			'''
		wanted_values = ([
			('foo@word', 'word'),
			('foo@lalala@word', 'word'),
			('foo@lalala@word.part1', 'word'),
			('@',None),
			('lalalafoobar.lala',None),
			('lalalafoobar',None),
			('',None),
			('foolalala@',None),
			('foolalala@pass.','pass'),
			('foolalala@WORD.part1','WORD'),
			('foolalala@foo.__@here_.','here'),
			('foolalala@.',None),
			('foolalala@.__##~nopass',None),
			('foolalala@.__##~-',None),
			('@foolalala@.__##~-',None),
			('@@@@.',None),
			])

		for i1,expectedstring in wanted_values:
			result = MD2.GetPasswordFromFilename (i1)
			self.assertEqual(result,expectedstring)


if __name__ == '__main__':
	unittest.main()

