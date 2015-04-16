#=====================================
# Program starter
#=====================================
import os, sys, time

""" Start an executable if there is any file in the indicated directory or subdirectories

	and ends with a defined string (extension):
	usage:  execute with arguments:
	%1 = string with de executable and its command line
	%2 = start directory to scan
	%3 = list of desired extensions to find and launch the executable in case it is found"""

def filetypefound (lista,extension):
	""" checks for file endings with the desired extension,	returns true if any:

	usage: filetypefound (list of directories with absolute path, extension)"""
	for a in lista:
		if checkextension (os.listdir (a), extension) == 1:
			return 1
	return 0


def lsdirectorytree(directory = (os.getenv('HOME'))):
	""" Returns a list of a directory and its child directories

	usage:
	lsdirectorytree ("start directory")
	By default, user's home directory"""
	#init list to start
	dirlist = [directory]
	#setting the first scan
	moredirectories = dirlist
	while len (moredirectories) != 0:
		newdirectories = moredirectories
		#reset flag to 0; we assume from start, that there aren't child directories
		moredirectories = []
		# print ('\n\n\n','nueva iteración', moredirectories)
		for a in newdirectories:
			# checking for items (child directories)
			# print ('Checking directory', a)
			añadir = addchilddirectory (a)
			#adding found items to moredirectories
			for b in añadir:
				moredirectories.append (b)
		#adding found items to dirlist
		for a in moredirectories:
			dirlist.append (a)
	return dirlist

def addchilddirectory (directorio):
	""" Returns a list of child directories

	Usage: addchilddirectory(directory with absolute path)"""
	paraañadir = []
	ficheros = os.listdir (directorio)
	#print ('ficheros encontrados en: ',directorio, ':\n' , ficheros, '\n')
	for a in ficheros:
		item = directorio+'/'+a
		#check, and if directory, it's added to paths-list
		if os.path.isdir(item):
			print('Directory found: '+ item)
			# print('Añadiendo elemento para escanear')
			paraañadir.append (item)
	# print ('este listado hay que añadirlo para el escaneo: ', paraañadir)
	return paraañadir

def checkextension (listado,extension):
	""" Cheks in a list of items if there is any name-file 

	with the passed extension, returns 1 if it is true or 0 if not"""
	separador = '*'
	tira = separador.join(listado)+separador
	if tira.find(extension+separador) != -1:
		#print ('Aquí si hay ficheros: returning 1')
		return 1
	return 0

def launcher (cmd,lsdy,lsext):
	lista=[]
	for a in lsdy:
		listaap = lsdirectorytree (a)
		for i in listaap:
			lista.append(i)

	launch = 0
	for a in lsext:
		if filetypefound (lista,a) == 1:
			launch = 1
	if launch == 1:
		os.system(cmd)
	else:
		# print ('No files found, exiting...')
		pass
	return launch
	

if __name__ == "__main__":

	os.system('clear')
	print('=================================================================')
	#print('Waiting 120 seconds to start..')
	#time.sleep(120)

	launcher (sys.argv[1], list(eval(sys.argv[2])), list(eval(sys.argv[3])) )