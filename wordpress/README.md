# Potion Wordpress Tool
A script for syncing Wordpress installs between servers, both local and remote.

## Requirements
- Python 3 
	- Install instructions at [http://brew.sh](http://brew.sh)
- WP-Cli
	- Command line interface for wordpress
	- Install instructions at [http://wp-cli.org](http://wp-cli.org)
- MAMP (optional)
	- Install instructions at [https://www.mamp.info/en/](https://www.mamp.info/en/)

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
		"host":"localhost:8889" # Your local host MySQL port
	}
}

```


  
## Starting a new site
To create a brand-new site:


1. Install WP-CLI

2. Install Python 3

3. Install MAMP (optional)

4. Create local mysql database. Go to your local phpMyAdmin and create a new database.

5. Clone Repository for CMS into Sites directory (/Users/YourName/Sites/YourProject_CMS)

6. Add poDataTools submodule at the root of your Git repo.

7. Create a copy of the config-template.json file (i.e. yourproject_cms.json) in the poDataTools/wordpress folder. Note: the file needs to stay in that folder.

8. Edit yourproject_cms.json. You can skip the "remoteSecret" field, since the first installation is local.

9. Run installation script from the poDataTools/wordpress folder. If you are using MAMP, make sure you use the flag `--mampEnabled`

```
python3 poWordpressTool.py --mampEnabled /Users/YourName/Sites/YourProject_CMS yourproject_cms.json create
```



## Deploy site to deployment server
To deploy the local site to the client's deployment server:


1. SSH to the deployment server
	```
	ssh myusername@myclientserver.com
	```

2. Make sure Git is instaled on the server, or install it.

3. Configure git so it has Potion's user for installations:
	```
	git config --global user.name "potioninstallation"
	git config --global user.email orders@potiondesign.com
	git config --list
	```
	Note: Remember to add the potioninstallation user as a contributor to your Github repository.

4. Generate Git SSH key, if neeeded, and add it to the Github account.
	
	[https:///help.github.com/articles/checking-for-existing-ssh-keys/](https:///help.github.com/articles/checking-for-existing-ssh-keys/)
	[https:///help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/](https:///help.github.com/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent/)
	[https:///help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/](https:///help.github.com/articles/adding-a-	new-ssh-key-to-your-github-account/)

	
	Note: If pbcopy is not installed on the server, try this:
	
	```
	cat ~/.ssh/id_rsa.pub
	```
	
	copy the ssh key and past it in your Github account

5. Clone your site's Github repository in the appropriate folder on the deployment server

6. Create a database for Wordpress in PHPMyAdmin on the deployment server

7. Install wpCli on the deployment server
	
	[http://wp-cli.org/docs/installing/](http://wp-cli.org/docs/installing/)
	```
	curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
	```

8. Download or copy Wordpress in the repository folder on the deployment site
	```
	wp core download
	```
	(or copy the wordpress files from the local repository to the deployment server)

9. Update wp-config.php on the deployment site
	
	Note: make sure that the remote wordpress folder has permission 755 or lower.

10. Install Wordpress on the deployment site
	
	Go to www.myclientserver.com/wordpress/wp-admin
	
	And follow the usual procedure to setup Wordpress.

11. Use WP Migrate Pro to push the local site to the deployment site
	- Go to the remote server WP Migrate Pro > Settings.
		- Copy the Server URL + secret key.
		- Enable Push + Pull.
	- Go to the local WP migrate Pro > Migrate
		- Select Push
		- Copy remote URL + secret key
		- Do the Push
