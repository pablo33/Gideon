''' This program checks the name of the filename, then, 
	
	matches a cover from a source directory, and returns it.
	from config: path where covers are stored. usually: Torrentinbox var.
		or TRinbox in a dropbox folder or the like.

	input: filename of the film
	output: path and name of the cover.
	'''

# module import
import os, logging
global TRWorkflowconfig

from glob import glob

__version__ = 1.1
__date__ = "28/12/2014"
__author__ = "pablo33"
#=====================================
# Functions
#=====================================
def listcovers(path):
	''' Return a list of covers-files
	input: relative path, or full-path
	output: list of image-files with relative or full-path
		'''
	# We need a final slash to path
	if path[-1] != "/":
		path += "/"
	# Initializing Lista
	lista = []
	# Listing
	for a in ("jpg","png","jpeg"):
		listb = glob(path+"*."+a)
		listc = glob(path+"*."+a.upper())
		for a in listb:
			lista.append(a)
		for a in listc:
			lista.append(a)
	lista.sort()
	return lista

'''
def words(string):
	"""Separate words from a string in a list
	input: string
	output: list of words
		"""
	words = []
	word = ""
	for a in string:
		if a in " ._()[]+-%&\"\'":
			if word != "":
				words.append(word)
			word = ""
			continue
		word += a
	if words != "":
		words.append(word)
	return words
'''

def matchfilm(film,lista):
	''' Selects a item from a list with the best match.
		it is intended to find a cover file within a list of possible covers.

		input: filename.ext or full-path/filename.ext of a movie.
		input: list of items to match (filenames.ext or full-path/filenames.ext) (of covers)
		output: item of the list (of covers) that best matches as "cover", and punctuation of match
		'''
	# We want only the name of the file, without extension.
	filmname = os.path.splitext(os.path.basename(film))[0]
	match = 0
	coveritem = ""
	for a in lista:
		# Get only the filename without extension
		name = os.path.splitext(os.path.basename(a))[0]
		matchw = 0
		for b in name.split(): # for b in words(name): /// I replaced this function. 
			if b.upper() in filmname.upper():
				matchw += len(b)
		if matchw > match:
			coveritem, match = a, matchw
	# We need at least a match of 4 points to return a reasonable match
	if match < 5:
		return "", 0
	return coveritem, match
