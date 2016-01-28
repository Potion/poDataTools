import os
import subprocess
from subprocess import call
import sys

def logVerboseMessage(message):
	if(args.verbose):
		print()
		print("-----------------------------------------------------")
		print(message)
		print()

# ------------------------------------------------------
# Setup and Parse Config

import argparse
parser = argparse.ArgumentParser(prog="Wordpress Local Setup", description="Initial a local environment to mirror a remote Wordpress install.")
parser.add_argument("installDirectory", help="The directory to install wordpress into")
parser.add_argument("configFile", help="The configuration file to use")
parser.add_argument("-m", "--mampEnabled",	type=bool, required=False,	help="Enable this flag if you are using MAMP", default="false")
parser.add_argument("-v", "--verbose",	required=False,	help="Enable this flag if you are using MAMP", default="false")

args = parser.parse_args()

# Switch to the install directory
scriptDir = os.path.dirname(os.path.realpath(__file__))
executeDir = os.getcwd()

os.chdir(args.installDirectory)
print(args.installDirectory)
print(os.getcwd())


# ------------------------------------------------------
# Set environment path to MAMP if necessary (avoids having to define in .bash_profie or .zshsrc)
mampPath = '/Applications/MAMP/bin/php/'
if args.mampEnabled == True:
	# Get the Mamp PHP version 
	mampPhpVersions = os.listdir(mampPath)
	latestMampPhpVersion = mampPhpVersions[-1]

	logVerboseMessage("Setting environment path for MAMP PHP/MYSQL")

	# Set PATH Environment
	os.environ["PATH"] = "/Applications/MAMP/bin/php/" + latestMampPhpVersion + "/bin:" + os.environ["PATH"]
	os.environ["PATH"] = "/Applications/MAMP/Library/bin/:" + os.environ["PATH"]

# ------------------------------------------------------
# Load Config

logVerboseMessage("Loading JSON config file...")

import json
from pprint import pprint

with open(executeDir + "/" + args.configFile) as config_file:
	config = json.load(config_file)




# ------------------------------------------------------
# WP CLI Commands

from subprocess import call

def add_option_to_wpcli_command(command, option, value):
	command = command + " --" + option
	if value != "":
		command = command + "='" + value + "'"
	return command


# Pull the correct version of wordpress
logVerboseMessage("Installing Wordpress...")
pullCommand = 'wp core download'

if config["version"]:
	logVerboseMessage("Custom version requested: " + args.version)
	pullCommand += ' --version ' + args.version

call([pullCommand], shell=True)

# Create Wordpress Config
logVerboseMessage("Creating wp-config.php...")

configCommand = 'wp core config'
configCommand = add_option_to_wpcli_command(configCommand, "dbname", config["localDatabase"]["name"])
configCommand = add_option_to_wpcli_command(configCommand, "dbuser", config["localDatabase"]["user"])
configCommand = add_option_to_wpcli_command(configCommand, "dbpass", config["localDatabase"]["pass"])
configCommand = add_option_to_wpcli_command(configCommand, "dbhost", config["localDatabase"]["host"])

call([configCommand], shell=True)

# Install Wordpress
logVerboseMessage("Installing Wordpress...")

installCommand = 'wp core install'
installCommand = add_option_to_wpcli_command(installCommand, "url",				config["locations"]["localUrl"])
installCommand = add_option_to_wpcli_command(installCommand, "title",			config["info"]["title"])
installCommand = add_option_to_wpcli_command(installCommand, "admin_user", 		config["info"]["admin_user"])
installCommand = add_option_to_wpcli_command(installCommand, "admin_password",	config["info"]["admin_password"])
installCommand = add_option_to_wpcli_command(installCommand, "admin_email",		config["info"]["admin_email"])
installCommand = add_option_to_wpcli_command(installCommand, "skip-email", 	"")

print(installCommand)

call([installCommand], shell=True)


# Install WP Migrate
call(['wp plugin install wp-migrate-db'], shell=True)

# Copy WP Migrate Pro files to plugins folder
wpMigratePlugins = ['wp-migrate-db-pro', 'wp-migrate-db-pro-cli', 'wp-migrate-db-pro-media-files']

wpMigrateProFilesPath =  scriptDir + "/wp-migrate/"
for plugin in wpMigratePlugins:
	call(['wp plugin install ' + wpMigrateProFilesPath + plugin + '.zip'], shell=True)
	call(['wp plugin activate ' + plugin], shell=True)

# ------------------------------------------------------
# Sync

# Set up license  for WP Migrate DB Pro
logVerboseMessage("Syncing with server...")
registerMessage = "Please go to " + config["locations"]["localUrl"] + "/wp-admin." 
registerMessage += "\nLogin using username: " + config["info"]["admin_user"] + " and password: " + config["info"]["admin_password"]
registerMessage += "\nGo to Tools->Migrate DB Pro"
registerMessage += "\nGo to Settings, and enter license."
registerMessage += "\n\nPress Enter to continue once complete"
input(registerMessage)

print("\n\n")



#wp migratedb pull http://example.com [secret key] --find=//example.com,/path/to/example.com --replace=//example.dev,/path/to/example.dev --skip-replace-guids --backup=prefix --media=remove-and-copy
syncCommand = 'wp migratedb pull ' + config["locations"]['remoteUrl'] + ' ' + config["locations"]['remoteMigrateDBSecret']
syncCommand = add_option_to_wpcli_command(syncCommand, "find", config["locations"]["remoteUrl"])
syncCommand = add_option_to_wpcli_command(syncCommand, "replace", config["locations"]["localUrl"])
#syncCommand = add_option_to_wpcli_command(syncCommand, "media", "remove-and-copy")

#print(syncCommand)
call([syncCommand], shell=True)


