#!/usr/bin/env python

import argparse
import fileinput
import os
import json
import urllib.request
import urllib.parse
import shutil
import re

class AssetGenerator(object):
	
	def __init__(self, arg):
		super(AssetGenerator, self).__init__()

		self.scriptDir = os.path.dirname(os.path.abspath(__file__))

		self.arg = arg
		self.url = self.arg.apiUrl
		self.tempFolder = os.path.join(self.scriptDir, "temp")
		self.destination = args.localDirectory
		self.uploadsDir = args.uploadDir
		self.uploadsPath = urllib.parse.urlparse(args.uploadDir).path
		self.numFiles = 0

		print(self.url, self.tempFolder, self.destination)

		# Create temporary storage for files while downloading
		if not os.path.exists(self.tempFolder):
			os.makedirs(self.tempFolder)

		# Get the JSON and Save it
		self.loadAndParseJSON()

		print("-", self.numFiles, "files downloaded")

		print('- Saving json')
		with open(os.path.join(self.tempFolder, "data.json"), 'w') as output:
			json.dump(self.json, output)

		# Replace uploads url with asset path
		f = open(os.path.join(self.tempFolder, "data.json"),'r')
		filedata = f.read()
		f.close()

		newdata = filedata.replace(self.uploadsDir,"")

		f = open(os.path.join(self.tempFolder, "data.json"),'w')
		f.write(newdata)
		f.close()

		print('- Moving webassets to assets dir')

		if os.path.exists(os.path.join(self.destination, self.destination)):
			shutil.rmtree(os.path.join(self.destination, self.destination))
		shutil.move(self.tempFolder, self.destination)

		print('Done.')
		print('')

	#
	#	Load and parse json
	#	
	def loadAndParseJSON(self):
		req = urllib.request.urlopen(self.url)
		encoding = req.headers.get_content_charset()
		self.json = json.loads(req.read().decode(encoding))

		for key, value in self.json.items():
			# print(key, type(value))
			if type(value) is dict:
				self.parseDict(value)

			if type(value) is list:
				self.parseList(value)

	#
	#	Parse dict in json recursively
	#	
	def parseDict(self, content):
		for key in content:
			# print(key, type(content[key]))
			if type(content[key]) is list and len(content[key]) > 0:
				self.parseList(content[key])
			if type(content[key]) is dict:
				self.parseDict(content[key])
			if type(content[key]) is str:
				self.parseUnicode(content[key])

	#
	#	Parse list in json recursively
	#	
	def parseList(self, content):
		for item in content:
			try:
				for key in item:
					# print(key, type(item[key]))
					try:
						if type(item[key]) is list and len(item[key]) > 0:
							self.parseList(item[key])
						if type(item[key]) is dict:
							self.parseDict(item[key])
						if type(item[key]) is str:
							self.parseUnicode(item[key])
					except TypeError:
						print(item[key], type(item[key]))
			except TypeError:
				print(type(content))

	#
	#	Parse unicode and grab urls
	#	
	def parseUnicode(self, content):
		content.encode('ascii', 'ignore')
		linkRegex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
		url = re.findall(linkRegex, content)
		if len(url) > 0:
			for theURL in url:
				parsed = urllib.parse.urlparse(theURL)

				path = parsed.path
				filename = path.split("/")[-1]
				path = path.split("/")[:-1]
				path = "/".join(path)

				if(path!=self.uploadsPath):
					path = path.split(self.uploadsPath)[1] # Remove the uploads directory
					path = path[1:] # Remove leading / from path
					path = os.path.join(self.tempFolder, path) # Add the tempfolder to the path
				else:
					path = self.tempFolder

				# Create the directories if necessary
				if not os.path.exists(path):
					os.makedirs(path)

				# Donwload the file
				self.downloadFile(theURL, path, filename)


	#
	#	Download file to disk
	#	
	def downloadFile(self, url, path, filename=None):
		if filename == None:
			print("NO FILENAME!")
			filename = url.split('/')[-1]

		request = urllib.request.urlopen(url)

		file = open(os.path.join(path, filename), 'wb')
		
		if request.getheaders("Content-Length"):
			filesize = int(request.getheaders("Content-Length")[0])
		else:
			filesize = 1

		print("- Downloading: %s Bytes: %s From: %s" % (filename, filesize, url))

		file_size_dl = 0
		block_sz = 8192
		while True:
		    buffer = request.read(block_sz)
		    if not buffer:
		        break

		    file_size_dl += len(buffer)
		    file.write(buffer)
		    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / filesize)
		    status = status + chr(8)*(len(status)+1)
		    # print(status)

		file.close()
		self.numFiles += 1

parser = argparse.ArgumentParser(description='-- AssetGenerator --')
parser.add_argument("localDirectory", help="The directory to cache the data + assets into.")
parser.add_argument("apiUrl", action="store", help="API URL")
parser.add_argument("uploadDir", help="The location for the uploads folder on the remote server.")
args = parser.parse_args()

assetGenerator = AssetGenerator(args)