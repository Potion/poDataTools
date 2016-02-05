import os
import argparse
import json
from subprocess import call

class wordpressSync(object):
    def __init__(self, args):
        # Constants
        self.MAMP_PATH = '/Applications/MAMP/bin/php/'
        self.SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        self.EXC_DIR = os.getcwd()

        self.WP_MIGRATE_PRO_FILES_PATH =  self.SCRIPT_DIR + "/wp-migrate/"
        self.WP_MIGRATE_PRO_PLUGINS = ['wp-migrate-db-pro', 'wp-migrate-db-pro-cli', 'wp-migrate-db-pro-media-files']

        self.config = self.load_config(os.path.expanduser(args.configFile))

        # Setup Environment
        installDir = os.path.expanduser(args.installDirectory)
        if not os.path.exists(installDir):
            os.makedirs(installDir)

        if args.mampEnabled:
            self.set_mamp_environment()

        self.create_database()
        self.change_directory(installDir)

        # Install Wordpress
        self.download_wordpress()
        self.config_wordpress()
        self.install_wordpress()

        # Sync with Server
        self.install_migration_plugins()
        self.sync_with_remote()

        # Done!
        self.finish()

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
    # Wordpress install/WP CLI Commands

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
        call(['wp plugin install wp-migrate-db'], shell=True)

        # Install Pro Plugins
        for plugin in self.WP_MIGRATE_PRO_PLUGINS:
            call(['wp plugin install ' + self.WP_MIGRATE_PRO_FILES_PATH + plugin + '.zip'], shell=True)
            call(['wp plugin activate ' + plugin], shell=True)
            call(['wp plugin update ' + plugin], shell=True)
            # NOTE: Should we update them also? Will this work?

    # ------------------------------------------------------
    # Sync down from remote to local using WP Migrate Pro
    def sync_with_remote(self):
        self.log_section_message("Syncing with server...")

        # Show instructions to set license on local install
        registerMessage = "Please go to " + self.config["locations"]["localUrl"] + "/wp-admin."
        registerMessage += "\nLogin using username: " + self.config["info"]["admin_user"] + " and password: " + self.config["info"]["admin_password"]
        registerMessage += "\nGo to Tools->Migrate DB Pro"
        registerMessage += "\nGo to Settings, and enter license."
        registerMessage += "\n\nPress Enter to continue once complete\n\n"
        input(registerMessage)

        # Call Sync Command

        # NOTE: Need to strip trailing slash from URLs if set
        syncCommand = 'wp migratedb pull ' + self.config["locations"]['remoteUrl'] + ' ' + self.config["locations"]['remoteMigrateDBSecret']
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "find", self.config["locations"]["remoteUrl"])
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "replace", self.config["locations"]["localUrl"])
        syncCommand = self.add_option_to_wpcli_command(syncCommand, "media", "remove-and-copy")

        call([syncCommand], shell=True)


    def finish(self):
        self.log_section_message("Installation and syncing complete.")


# ----------------------------------------------------
# Run the program

parser = argparse.ArgumentParser(prog="Wordpress Local Sync", description="Initial a local environment to mirror a remote Wordpress install.")
parser.add_argument("installDirectory", help="The directory to install wordpress into")
parser.add_argument("configFile", help="The configuration file to use")
parser.add_argument("-m", "--mampEnabled",	type=bool, required=False,	help="Enable this flag if you are using MAMP", default="false")

arguments = parser.parse_args()
poWordpressSync = wordpressSync(arguments)