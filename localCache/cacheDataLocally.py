#!/usr/bin/env python

import argparse
import os
import urllib.request
import urllib.parse
import shutil
import re
import json

class AssetGenerator(object):
    def __init__(self, localCacheDirectory, apiURL):
        super(AssetGenerator, self).__init__()

        self.scriptDir = os.path.dirname(os.path.abspath(__file__))

        self.url = apiURL
        self.tempFolder = os.path.join(self.scriptDir, "temp")
        self.destination = os.path.expanduser(localCacheDirectory)

        self.numFiles = 0

        print(self.url, self.tempFolder, self.destination)

        # Create temporary storage for files while downloading
        if not os.path.exists(self.tempFolder):
            os.makedirs(self.tempFolder)

        # Get the JSON and Save it
        self.loadJSON();
        self.getFilesFromJson()

        self.saveJson()

        # Print status
        print("-", self.numFiles, "files downloaded")
        print('- Moving webassets to assets dir')

        # Copy assets to new location
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

        jsonObj = json.loads(self.jsonString)
        self.jsonString = json.dumps(jsonObj)

    # ------------------------------------------------------
    # Parse unicode and grab urls

    def getFilesFromJson(self):
        linkRegex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urls = re.findall(linkRegex, self.jsonString)

        for url in urls:
            # Remove trailing backslash, which may be an escape character
            url = url.rstrip("\\")

            # Parse the URL
            parsed = urllib.parse.urlparse(url)

            # Get the path + Filename
            path = parsed.path
            filename = path.split("/")[-1]

            # Replace the URL in the JSON with the filename
            self.jsonString = self.jsonString.replace(url, filename)

            # Download the file
            self.downloadFile(url, self.tempFolder, filename)

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
        f = open(os.path.join(self.tempFolder, "data.json"), 'w')
        f.write(self.jsonString)
        f.close()


# ------------------------------------------------------
# Main Execution, script is being run standalone
# Set Parser Args

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='-- AssetGenerator --')
    parser.add_argument("localCacheDirectory", help="The directory to cache the data + assets into.")
    parser.add_argument("apiURL", action="store", help="API URL")

    args = parser.parse_args()

    assetGenerator = AssetGenerator(args.localCacheDirectory, args.apiURL)
