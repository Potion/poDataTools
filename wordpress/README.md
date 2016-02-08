# Potion Wordpress Tool
A script for syncing Wordpress installs between servers, both local and remote.

## Requirements
- Python 3 
	- Install instructions at [http://brew.sh](http://brew.sh)
- WP-Cli
	- Command line interface for wordpress
	- Install instructions at [http://wp-cli.org](http://wp-cli.org)

## Structure
The following structure is used by Potion (and this script) to create a seamless Wordpress process, including version control and backups.

- Git repository
	- The Git repository holds the site's theme and plugins.
		- wp-content
			- Theme
				- Default themes are ignored
				- Site-specific themes version-controlled 
			- Plugins
		- .gitignore
			- Duplicated from here
			- Ignores all built-in wordpress files
		- README.md
			- Should fully explain:
			- Remote URLs
			- Connection information
			- Etc.
		- wp-cli.yml
			- Duplicated from here 
			- wp-cli configuration file
			- Needed to allow rewrite module, used by script to generate permalinks 
- Servers
	- Can be any combination of local or staging installs
	- Consist of a git repository clone with Wordpress installed in the same folder
	- Remote server should be the main content server, should be pull only once initial site is setup.
	- Remote server
		- During initial site setup (structure) can be pushed to from local
		- Consists of a git repository clone and a wordpress install
		- Theme changes should be pulled from GitHub for deployment
	- Local Server
		- Should exist in your local web directory (i.e. /Applictions/Mamp/htdocs if using MAMP)
		- Should be regulary sync'd with remote server when working locally.
		- Theme changes should be commited and pusehd to github.

##  Config File
All functionality in this script uses a JSON config file. This file should be different in each location and not commited to the repository.

You can copy the ```config_template.json``` file and rename it for each site. Avoid using ```config_template.json``` directly, it is a sample file that should be used as an example only.

Below is a commented version to use for reference:

```
{
	"version":null, # Version of Wordpress to clone, defaults to latest if null 
	"info": {
		"title":"My CMS Title", # The title to give your local site
		"admin_user":"admin", # The user for your local site. Overwritten if syncing
		"admin_password":"admin", # The password for your local site. Overwritten if syncing
		"admin_email":"your@email.com" # Your email address
	},

	"locations": {
		"remoteUrl":"http://wwww.yourwebsite.com/wordpressDir/", # The remote site you want to clone
		"localUrl":"http://localhost:8888/yourWebsite" # The local location your clone will exist at
	},

	"migrationKeys": {
		"license": "my-license-key-from-wp-migrate-db-pro", # Your wp-migrate-db-pro license key
		"remoteSecret":"my-remote-site-secret-key" # Your wp-migrate-db remote secret
	},

	"localDatabase": {
		"name":"your_Local_empty_db", # Local Database name (created if it doesn't exist)
		"user":"root", # Your local MySQL user name
		"pass":"root", # Your local MySQL password
		"host":"localhost:8889" # Your local host
	}
}

```


  
## Starting a new site
To create a brand-new site, 




	



Create local mysql database

Clone Repository for CMS into sites directory

Install WP-CLI

Copy config-template

Edit copy

