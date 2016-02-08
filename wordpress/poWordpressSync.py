import os
import argparse
import json
from subprocess import call
import urllib.request
from shutil import copyfile

class wordpressSync(object):
    def __init__(self, args):
        self.MAMP_PATH = '/Applications/MAMP/bin/php/'
        self.MAMP_ENABLED = args.mampEnabled
        self.SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        self.EXC_DIR = os.getcwd()
        self.INSTALL_DIR = os.path.expanduser(args.localDirectory)



        # Set Constants
        self.WP_MIGRATE_PRO_FILES_PATH =  self.SCRIPT_DIR + "/wp-migrate/"
        self.WP_MIGRATE_PLUGIN_NAME = 'wp-migrate-db'
        self.WP_MIGRATE_PRO_PLUGINS = {'wp-migrate-db-pro': 'https://deliciousbrains.com/dl/wp-migrate-db-pro-latest.zip',
                                       'wp-migrate-db-pro-cli': 'https://deliciousbrains.com/dl/wp-migrate-db-pro-cli-latest.zip',
                                       'wp-migrate-db-pro-media-files': 'https://deliciousbrains.com/dl/wp-migrate-db-pro-media-files-latest.zip'
                                       }
        self.setup_environment()


        self.copy_supporting_files()
        os._exit(0)

        if args.action == 'create':
            self.create()
            if(args.andSync == True):
                self.sync_with_remote()
            self.finishInstallation()

        elif args.action == 'sync':
            self.sync_with_remote()

        elif args.action == 'push':
            self.log_section_message("Attempting push to remote server.")
            userConfirmation = input("This will overwrite the remote server with your local content."
                                     "\nThis can not be undone. Are you sure? \nType y/n and hit enter/return: ")
            if userConfirmation == 'y' or userConfirmation == 'Y':
                self.push_to_remote()
        else:
            self.log_message("Action '" + args.action + "' is not known. Please run -h for help.")


    # ------------------------------------------------------
    # Utils

    # Format log messages
    @staticmethod
    def log_section_message(message):
            print()
            print("-----------------------------------------------------")
            print(message)
            print()

    @staticmethod
    def log_message(message):
        print()
        print(message)
        print()

    # Show directory changes for sanity
    @staticmethod
    def change_directory(directory):
        print("Changing dir from ", os.getcwd(), " to ", directory)
        os.chdir(directory)

    # Strip the last slash from a URL to stay consistent
    @staticmethod
    def strip_trailing_slash(url) -> str:
        if url.endswith("/"):
            return url[:-1]
        return url

    # Format WP-CLI calls
    @staticmethod
    def add_option_to_wpcli_command(command, option, value) -> str:
        command = command + " --" + option
        if value != "":
            command = command + "='" + value + "'"
        return command

    # ------------------------------------------------------
    # Environment Setup

    # Make sure the install dir is active, handle MAMP Path, etc.
    def setup_environment(self):
        if not os.path.exists(self.INSTALL_DIR):
            os.makedirs(self.INSTALL_DIR)

        if self.MAMP_ENABLED == True:
            self.set_mamp_environment()

        self.change_directory(self.INSTALL_DIR)

    # Create the MySQL database using the command line (avoids module dependencies)
    def create_database(self):
        command = 'echo "CREATE DATABASE IF NOT EXISTS ' + self.config["localDatabase"]["name"] + '" | mysql -u ' + self.config["localDatabase"]["user"] + ' -p' + self.config["localDatabase"]["pass"]
        call([command], shell=True)

    # Set PATH for this execution to MAMP PHP and MySQL
    def set_mamp_environment(self):
        # Get the Mamp PHP version
        mampPhpVersions = os.listdir(self.MAMP_PATH)
        latestMampPhpVersion = mampPhpVersions[-1]

        self.log_section_message("Setting environment path for MAMP PHP/MYSQL")

        # Set PATH Environment
        os.environ["PATH"] = "/Applications/MAMP/bin/php/" + latestMampPhpVersion + "/bin:" + os.environ["PATH"]
        os.environ["PATH"] = "/Applications/MAMP/Library/bin/:" + os.environ["PATH"]

    # Load the Configuration file
    def load_config(self, config_file_path) -> object:
        self.log_section_message("Loading JSON config file...")

        with open(self.EXC_DIR + "/" + config_file_path) as config_file:
            jsonFile = json.load(config_file)
            jsonFile["locations"]['localUrl'] = self.strip_trailing_slash(jsonFile["locations"]['localUrl'])
            jsonFile["locations"]['remoteUrl'] = self.strip_trailing_slash(jsonFile["locations"]['remoteUrl'])
            return jsonFile


    # ------------------------------------------------------
    # Actions
    def create(self):
        self.create_database()
        self.change_directory(self.INSTALL_DIR)

        # Install Wordpress
        self.copy_supporting_files()
        self.download_wordpress()
        self.config_wordpress()
        self.install_wordpress()
        self.install_migration_plugins()
        self.finishInstallation()

    # ------------------------------------------------------
    # Wordpress install/WP CLI Commands

    # Check for required files (.gitignore and wp-cli.yml
    # Add if they don't exist, add them
    def copy_supporting_files(self):
        self.log_section_message("Copying required files.")
        support_dir = self.SCRIPT_DIR + "/supporting_files"
        for filename in os.listdir(support_dir):
            if(filename == "_.gitignore"):
                new_filename = ".gitignore"
            else:
                new_filename = filename

            file_path = support_dir + "/" + filename
            new_file_path = self.INSTALL_DIR + "/" + new_filename
            if not os.path.exists(new_file_path):
                copyfile(file_path, new_file_path)
            else:
                self.log_message("File " + new_filename + " already exists, please make sure it is consistent with " + file_path)


    # Download correct version of wordpress
    def download_wordpress(self):
        self.log_section_message("Downloading Wordpress...")

        pullCommand = 'wp core download'

        if self.config["version"] is not None:
            self.log_message('Custom version requested: ' + self.config["version"])
            pullCommand += ' --version ' + self.config["version"]

        call([pullCommand], shell=True)

    # Configure Wordpress (Create wp-config.php)
    def config_wordpress(self):
        self.log_section_message("Configuring Wordpress and validating database connection...")

        configCommand = 'wp core config'
        configCommand = self.add_option_to_wpcli_command(configCommand, "dbname", self.config["localDatabase"]["name"])
        configCommand = self.add_option_to_wpcli_command(configCommand, "dbuser", self.config["localDatabase"]["user"])
        configCommand = self.add_option_to_wpcli_command(configCommand, "dbpass", self.config["localDatabase"]["pass"])
        configCommand = self.add_option_to_wpcli_command(configCommand, "dbhost", self.config["localDatabase"]["host"])

        configCommand = configCommand + " --extra-php <<PHP \ndefine( 'WPMDB_LICENCE', '" + self.config["migrationKeys"]['license'] + "' ); \nPHP"

        call([configCommand], shell=True)

    # Install Wordpress, initializing the MySQL DB Entries
    def install_wordpress(self):
        self.log_section_message("Initializing local DB and Installing Wordpress...")

        installCommand = 'wp core install'
        installCommand = self.add_option_to_wpcli_command(installCommand, "url",            self.config["locations"]["localUrl"])
        installCommand = self.add_option_to_wpcli_command(installCommand, "title",			self.config["info"]["title"])
        installCommand = self.add_option_to_wpcli_command(installCommand, "admin_user", 	self.config["info"]["admin_user"])
        installCommand = self.add_option_to_wpcli_command(installCommand, "admin_password",	self.config["info"]["admin_password"])
        installCommand = self.add_option_to_wpcli_command(installCommand, "admin_email",	self.config["info"]["admin_email"])
        installCommand = self.add_option_to_wpcli_command(installCommand, "skip-email", 	"")

        call([installCommand], shell=True)

    # Install the migration plugins from zip files
    # The Pro files are proprietary so must be installed from .zip
    def install_migration_plugins(self):
        self.log_section_message("Installing migration plugins")

        # Install base plugin
        call(['wp plugin install ' + self.WP_MIGRATE_PLUGIN_NAME], shell=True)

        # Install Pro Plugins

        for plugin in self.WP_MIGRATE_PRO_PLUGINS:
            print(self.WP_MIGRATE_PRO_PLUGINS[plugin] + "?licence_key=" + self.config['migrationKeys']['license'])
            self.download_and_install_wp_migrate_plugin(plugin, self.WP_MIGRATE_PRO_PLUGINS[plugin] + "?licence_key="
                                                        + self.config['migrationKeys']['license']
                                                        + "&site_url=" + self.config["locations"]["localUrl"])

    # Download a plugin from the Delicious Brains server and install it
    def download_and_install_wp_migrate_plugin(self, plugin_name, url):
        print(url)
        urllib.request.urlretrieve(url, "./plugin.zip")

        call(['wp plugin install ./plugin.zip'], shell=True)
        call(['wp plugin activate ' + plugin_name], shell=True)
        call(['wp plugin update ' + plugin_name], shell=True)

        os.remove('./plugin.zip')

    def finishInstallation(self):
        self.log_section_message("Installation complete.")
        self.log_message("You can visit the admin panel for your local site clone at " + self.config["locations"]["localUrl"] + " and log in with your remote site credentials.")

    # ------------------------------------------------------
    # Sync down from remote to local using WP Migrate Pro
    def create_sync_command(self, action, find, replace) -> str:
        syncCommand = 'wp migratedb ' + action + ' ' + self.config["locations"]['remoteUrl'] + ' ' + self.config["migrationKeys"]['remoteSecret']
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "find", find)
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "replace", replace)
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "media", "remove-and-copy")
        return syncCommand

    def sync_with_remote(self):
        self.log_section_message("Syncing with server...")

        # Call Sync Command
        syncCommand = self.create_sync_command('pull', self.config["locations"]["remoteUrl"], self.config["locations"]["localUrl"])
        call([syncCommand], shell=True)

        self.log_section_message("Sync complete.")
        self.log_message("Local site " + self.config["locations"]["localUrl"] + " now mirrors " + self.config["locations"]["remoteUrl"])

    def push_to_remote(self):
        self.log_section_message("Pushing to server...")

        # Call Sync Command
        syncCommand = self.create_sync_command('push', self.config["locations"]["localUrl"], self.config["locations"]["remoteUrl"])
        call([syncCommand], shell=True)

        self.log_section_message("Push complete.")
        self.log_message("Remote site " + self.config["locations"]["remoteUrl"] + " now mirrors " + self.config["locations"]["localUrl"])





# ----------------------------------------------------
# Run the program

parser = argparse.ArgumentParser(prog="Wordpress Local Sync", description="Initial a local environment to mirror a remote Wordpress install.")

parser.add_argument("localDirectory", help="The directory to install or sync wordpress into")
parser.add_argument("configFile", help="The configuration file to use")

parser.add_argument("-m", "--mampEnabled",	action="store_true", required=False, help="Enable this flag if you are using MAMP", default=False)

subparsers = parser.add_subparsers(dest="action", help='The action you would like to perform')

parser_create = subparsers.add_parser('create', help='a help')
parser_create.add_argument("-s", "--andSync",	action="store_true", required=False, help="Sync after creating.", default="false")

parser_sync = subparsers.add_parser('sync', help='a help')

parser_push = subparsers.add_parser('push', help='a help')

arguments = parser.parse_args()

poWordpressSync = wordpressSync(arguments)