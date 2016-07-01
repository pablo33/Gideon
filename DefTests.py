#!/usr/bin/python3
# Test Configuration
import unittest
import TRWorkflow
import datetime



#####TESTS########
MD = TRWorkflow

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
		("gedit", False),
		("python3", True),
		)

	def test_getappstatus (self):
		for process, PIDs in self.known_values:
			result = MD.getappstatus (process)
			self.assertEqual (PIDs, result)


if __name__ == '__main__':
	unittest.main()

