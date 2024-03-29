# Jetson Benefits Team Build Guide

## Required Downloads
* git
* python 3.6 (or latest) + pip
* virtualenv
* node + npm

## Recommended Downloads
* Sublime / VSCode
* Gitbash / anaconda prompt
* Anaconda (python extender)
* Chrome

## Installation Process
### If you have questions/errors and are on a mac: ask Andrew, windows: ask Justin
1. Install the above required downloads
2. Clone the Jetson team repo into a local directory [Repo Link](https://github.com/loganallen/JetsonBenefits)
3. Install the Python packages: navigate to the root directory for the project and run `npm install`
4. CREATE a virtual environment (do this **once**): `virtualenv env` (on windows:`py -3 -m venv env`) (put this wherever, do NOT commit it to the repo)
5. Enter the virtual environment: `source env/bin/activate` (on windows: `env\scripts\activate.bat`)
6. Install the django requirements: `pip install -r requirements.txt`
7. Exit the virtual environment: `deactivate`

### MYSQL Setup
1. Configure your `.bash_profile` to have the necessary MySQL environmental variables
* export MYSQL_HOST='localhost'
* export MYSQL_USER={your_user(could be root)}
* export MYSQL_PASSWORD={your_mysql_pswd}
* export MYSQL_DB='jetson_database'
2. Make sure your `mysql server` is running

## Development Process
1. Make sure to `git pull` from remote master before implementing changes
2. Run `npm install` to ensure all python packages are included
3. After making JS changes, you need to run `npm run build` to compile the JS
4. Enter the virtual environment and run `npm start` to start the dev server
5. Navigate to `localhost:8000` on your browser to view our webpage
6. Exit the virtual environment: `deactivate`

The file `package.json` is a npm file that holds the specifcs about our javascript environment. It makes available the following commands:
* `npm start`: starts the django server: short for `python manage.py runserver`
* `npm run start-test`: start server so you can access from a different device in network - use command `ipconfig getifaddr en0` to get your computer's ip
* `npm run autobuild`: re-compiles our javascript files everytime there is an update, will run and listen until terminated
* `npm run build`: compiles our javascript files just once

For **example** run `npm start` to start the dev server instead of remembering the full command.

## Rare Errors and how to fix them
* "OSError" something about package.json being missing
	1. Make sure to run `npm run build` before `npm start`
* "Invalid configuration object" referring to webpack
	1. ``` npm uninstall webpack ```
	2. ``` npm install webpack@2.1.0-beta.22 --save-dev ```
* "filesystem.statSync is not a function"
	1. ``` npm install babel-loader@7.1.1 --save-dev ```

## Database changes
1. `python manage.py makemigrations`
2. `python manage.py migrate`
