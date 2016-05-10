#!/usr/bin/env python

import argparse
import os
import urllib.request
import urllib.parse
import shutil
import re
import json
import sys
import datetime
import math


# Convenience func to convert filesizes
# size is in kB
# from http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def convertSize(size):
    if (size == 0):
        return '0B'
    size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    s = round(size / p, 2)
    return '%s %s' % (s, size_name[i])

class AssetGenerator(object):
    def __init__(self, localCacheDirectory, apiURL):
        super(AssetGenerator, self).__init__()

        # Vars to report what we did on complete
        self.startTime = datetime.datetime.now()
        self.totalBytes = 0
        self.numFiles = 0

        # Our current path
        self.scriptDir = os.path.dirname(os.path.abspath(__file__))

        # Store member vars
        self.url = apiURL
        self.tempFolder = os.path.join(self.scriptDir, "temp")
        self.destination = os.path.expanduser(localCacheDirectory)

        # Create temporary storage for files while downloading
        if not os.path.exists(self.tempFolder):
            os.makedirs(self.tempFolder)

        # Get the JSON and Save it
        print("Loading file from '{0}'...".format(self.url))
        self.loadJSON()

        print('\nRetrieving files...')
        self.getFilesFromJson()

        print('\nFinished retrieving files.')
        print("- {0} files downloaded".format(self.numFiles))
        print("- Total size of all files: {0}".format(convertSize(self.totalBytes/1000)))

        print("\n Finishing Up...")
        print('- Saving json')
        self.saveJson()

        # Print status
        print('- Moving files to assets dir {0}'.format(localCacheDirectory))

        # Copy assets to new location
        if os.path.exists(os.path.join(self.destination, self.destination)):
            shutil.rmtree(os.path.join(self.destination, self.destination))
        shutil.move(self.tempFolder, self.destination)

        totalTime = datetime.datetime.now() - self.startTime

        print('\nCompleted, total execution time: {0}.'.format(totalTime))
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

            # Download the file
            self.downloadFile(url, self.tempFolder, filename)

            # Replace the URL in the JSON with the filename
            self.jsonString = self.jsonString.replace(url, filename)

    # ------------------------------------------------------
    # Download file to disk

    def downloadFile(self, url, path, filename=None):
        if filename == None:
            print("NO FILENAME!")
            filename = url.split('/')[-1]

        filepath = os.path.join(path, filename)

        print("- Downloading: %s from: %s" % (filename, url))
        filename, headers = urllib.request.urlretrieve(url, filepath, reporthook=self.downloadProgress)

        # Record total amount the script has downloaded
        self.totalBytes += int(headers['Content-Length'])


        self.numFiles += 1

    def downloadProgress(self,count, blocksize, totalsize):

        readsofar = count * blocksize

        # The last block may contain a lot of empty data,
        # which will throw off progress reporting
        if readsofar > totalsize:
            readsofar = totalsize

        percent = int(readsofar * 100 / totalsize)

        if percent <= 99:
            progressString = "-- Retrieved {0}/{1} bytes ({2}%)".format(readsofar, totalsize, percent)
            sys.stdout.write(progressString)

            # Clear for next progress write
            for c in progressString:
                sys.stdout.write("\b")
            sys.stdout.flush()
        else:
            finishedString = "-- Finished downloading {0} bytes.\n".format(totalsize)
            sys.stdout.write(finishedString)

    def saveJson(self):
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
