import os
import sys

def logVerboseMessage(message):
	if(args.verbose):
		print(message)

# ------------------------------------------------------
# Setup and Parse Config

import argparse
parser = argparse.ArgumentParser(prog="Wordpress Local Setup", description="Initial a local environment to mirror a remote Wordpress install.")
parser.add_argument("installDirectory", help="The directory to install wordpress into")
parser.add_argument("configFile", help="The configuration file to use")
parser.add_argument("-m", "--mampEnabled",	required=False,	help="Enable this flag if you are using MAMP", default="false")
parser.add_argument("-v", "--verbose",	required=False,	help="Enable this flag if you are using MAMP", default="false")

args = parser.parse_args()

# Switch to the install directory
executeDir = os.getcwd()

os.chdir(args.installDirectory)
print(args.installDirectory)
print(os.getcwd())


# ------------------------------------------------------
# Set environment path to MAMP if necessary (avoids having to define in .bash_profie or .zshsrc)
if args.mampEnabled:
	logVerboseMessage("Setting environment path for MAMP PHP/MYSQL")

	from subprocess import call
	import os

	os.environ["PATH"] = "/Applications/MAMP/bin/php/${PHP_VERSION}/bin:" + os.environ["PATH"]
	os.environ["PATH"] = "/Applications/MAMP/Library/bin/:$PATH" + os.environ["PATH"]


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

call([installCommand], shell=True)


# Install WP Migrate
call(['wp plugin install wp-migrate-db'], shell=True)

# Copy WP Migrate Pro to plugins folder
wpMigrateProPath =  os.path.abspath(os.path.dirname(__file__)) + "/wp-migrate-db-pro.zip"
call(['wp plugin install ' + wpMigrateProPath], shell=True)

