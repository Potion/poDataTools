#!/usr/bin/env python

import argparse
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
        self.destination = os.path.expanduser(args.localDirectory)
        self.uploadsDir = args.uploadDir
        self.uploadsPath = urllib.parse.urlparse(args.uploadDir).path
        self.numFiles = 0

        print(self.url, self.tempFolder, self.destination)

        # Create temporary storage for files while downloading
        if not os.path.exists(self.tempFolder):
            os.makedirs(self.tempFolder)

        # Get the JSON and Save it
        self.loadJSON();
        self.getFilesFromJson()

        self.saveJson()
        print("-", self.numFiles, "files downloaded")



        print('- Moving webassets to assets dir')

        if os.path.exists(os.path.join(self.destination, self.destination)):
            shutil.rmtree(os.path.join(self.destination, self.destination))
        shutil.move(self.tempFolder, self.destination)

        print('Done.')
        print('')

    # ------------------------------------------------------
    # Load and parse json

    def loadJSON(self):
        req = urllib.request.urlopen(self.url)

        if(req.headers.get_content_charset()):
            encoding = req.headers.get_content_charset()
            self.jsonString = req.read().decode(encoding)
        else:
            self.jsonString = req.read().decode()

        self.jsonString = self.jsonString.replace("\\", "") # Strip backslashes put in by some APIs

    # ------------------------------------------------------
    # Parse unicode and grab urls

    def getFilesFromJson(self):

        linkRegex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = re.findall(linkRegex, self.jsonString)
        print(urls)
        for url in urls:
            parsed = urllib.parse.urlparse(url)

            path = parsed.path
            filename = path.split("/")[-1]
            path = path.split("/")[:-1]
            path = "/".join(path)

            if (path != self.uploadsPath):
                splitPath = path.split(self.uploadsPath)
                try:
                    path = path.split(self.uploadsPath)[1]  # Remove the uploads directory
                    if(path[0] and path[0] is "/"):
                        path = path[1:]  # Remove leading / from path
                    path = os.path.join(self.tempFolder, path)  # Add the tempfolder to the path
                except IndexError: 
                    print("Could not find uploads path '", self.uploadsPath, "' in url ",  path)
                    continue
            else:
                path = self.tempFolder

            # Create the directories if necessary
            if not os.path.exists(path):
                os.makedirs(path)

            # Download the file
            self.downloadFile(url, path, filename)

    # ------------------------------------------------------
    # Download file to disk

    def downloadFile(self, url, path, filename=None):
        if filename == None:
            print("NO FILENAME!")
            filename = url.split('/')[-1]

        request = urllib.request.urlopen(url)

        file = open(os.path.join(path, filename), 'wb')

        if request.getheader("Content-Length"):
            filesize = int(request.getheader("Content-Length"))
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
            status = status + chr(8) * (len(status) + 1)

        file.close()
        self.numFiles += 1




    def saveJson(self):
        print('- Saving json')
        self.jsonString = self.jsonString.replace(self.uploadsDir, "")
        f = open(os.path.join(self.tempFolder, "data.json"), 'w')
        f.write(self.jsonString)
        f.close()

# ------------------------------------------------------
# Set Parser Args
parser = argparse.ArgumentParser(description='-- AssetGenerator --')
parser.add_argument("localDirectory", help="The directory to cache the data + assets into.")
parser.add_argument("apiUrl", action="store", help="API URL")
parser.add_argument("uploadDir", help="The location for the uploads folder on the remote server.")
args = parser.parse_args()

assetGenerator = AssetGenerator(args)
