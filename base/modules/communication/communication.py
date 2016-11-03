#!/usr/bin/python3

import os
import importlib

class communication(object):
	def __init__(self, status):
		self.status = status
		self.isClosed = False

	def close(self):
		self.isClosed = True

	def run(self):
		while not self.isClosed:
			pass


class start(object):
	def __init__(self, status):
		cwd = os.getcwd()+"/modules/communication/checks"
		for name in os.listdir(cwd):
			print(name)
			name = "modules/communication/checks" + name
			importlib.import_module(name)
			print(check())
		# comm_status = communication(status)
		# comm_status.run()