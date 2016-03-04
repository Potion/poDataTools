This is a small command-line tool to add MAMP's PHP and MySQL to your PATH only in the open shell.

This is preferred to putting it in your .bash_profile if you are using other installs of PHP or MySQL, and is the only way if you are using ZSH since ZSH does not support exporting functions.

See [http://stackoverflow.com/questions/4145667/how-to-override-the-path-of-php-to-use-the-mamp-path/29990624#29990624](http://stackoverflow.com/questions/4145667/how-to-override-the-path-of-php-to-use-the-mamp-path/29990624#29990624)

Usage:

```
source ./setMampPath.sh
```