This page explains what you must do to set up a local installation of Lexonomy on your own computer or server, from the source code in this repository.

# Dependencies

- Lexonomy is only intended to be run on Linux. It may or may not run on Windows.

- You need [Node.js](https://nodejs.org/) installed on your computer to be able to build Lexonomy's frontend.

- You need [Python3](https://python.org) installed on your computer to run Lexonomy's backend.

# Preparing Lexonomy (part 1)

1. Download the source code from this repository into a directory on your computer, and go to that directory in your terminal.

2. Build the frontend (this takes Lexonomy's frontend code, which has been written in [https://riot.js.org/](Riot.js), and builds it into a single JavaScript bundle):

```sh
make
```

3. Go to the `website` directory of the repository:

```sh
cd website
```

4. Copy `config.js.template` to `config.js` (this is the frontend configuration, you will most likely not need to change anything in it):

```sh
cp config.js.template config.js
```

5. Copy `siteconfig.json.template` to `siteconfig.json` (this is the backend configuration, we will show you later what – if anything – you need to change in it):

```sh
cp siteconfig.json.template siteconfig.json
```

# Configuring Lexonomy's backend

The backend configuration is in `website/siteconfig.json` (but this location can be changed by setting the `$LEXONOMY_SITECONFIG` environmental variable). This file contains some configuration options for your Lexonomy installation. Let's look at those options you will probably want to change at this stage.

**Note:** After changing settings in `siteconfig.json`, you may need to use the `touch` command to force WSGI to reload it:
```sh
touch siteconfig.json
```

## Base URL
```js
"baseUrl": "http://localhost:8080/"
```
This is the URL at which your Lexonomy installation is visible to web browsers. For reasons we will not go into now, Lexonomy needs to know what the URL is.

- For Lexonomy's “home” installation this is `https://www.lexonomy.eu/`.
- If you are testing a local installation on your own desktop computer then this is `http://localhost/`.
- If you are setting up your own installation on a web server somewhere then this should be any URL, such as `http://www.mylexonomy.com/`.

Make sure the path (ie. the final forward slash) is included. If your installation of Lexonomy is meant to be accessible from the Internet at a URL that contains a path, such as `http://www.example.com/mylexonomy/`, then make sure to include the path `/mylexonomy/` in the URL too.

## Root path
```js
"rootPath": "/"
```
This is the path at which Lexonomy listens for incoming HTTP requests on the server. Under normal circumstances this should be the same as the path at the end of your URL, for example `/` or `/mylexonomy/`. If, however, you have a proxy server which listens for HTTP requests at one URL and then forwards them to another, then the first URL should be the `baseUrl` and the second URL's path should be the `rootPath`.

## Port
```js
"port": 8080
```
This is the port number at which Lexonomy listens for incoming HTTP requests.

**Note:** When launched this way, Lexonomy runs on 8080. To allow it to run on a privileged port (<&nbsp;1024), for example 80, you will need to run Lexonomy with superuser permissions (`sudo`).

## Data directory
```js
"dataDir": "../data/"
```
This is the path to the `data` folder where Lexonomy will store all its data, including (importantly) all the dictionaries. Note that the directory name does not have to be `data`, it can be anything you want.

If the path given here is relative, it is interpreted relatively to the web application's current directory (= the `website` directory). It can also be an absolute path, eg. `/home/joebloggs/lexonomydata/`.

Upon first start, Lexonomy automatically creates three subdirectories here:
- `dicts` – a directory with individual dictionaries, each being an SQLite database,
- `uploads` – a directory for temporary storage of user-uploaded imports,
- `sqlite_tmp` – a directory that SQLite will use as its temporary directory.

## Logging
```js
"verbose": false
```
If you set this to `true` Lexonomy will report each HTTP request (except requests for static files) to standard error output – useful for debugging.

## Tracking code
```js
"trackingCode": ""
```
This is an HTML snippet which Lexonomy inserts into every public-facing web page. You can replace it with your own tracking code from Google Analytics, StatCounter or whatever other web analytics service you use, or leave it blank.

## Welcome message
```js
"welcome": "Welcome to your <a href='http://www.lexonomy.eu/'>Lexonomy</a> installation."
```
This is the welcome message displayed on the home page of your Lexonomy installation (left of the log-in box).

## Admin account(s)
```js
"admins": ["root@localhost"]
```  
This is an array of one or more e-mail addresses. People listed here are administrators: they can access everything in Lexonomy (including other people's dictionaries) and, after they log in, they will see options to create/change/delete user accounts, which other users don't see. You probably want to change this to your own e-mail address, like `joebloggs@example.com`.

# Configuring Lexonomy's frontend

The frontend configuration is in `website/config.js`. The only setting in it is a URL which tells the frontend where the backend is:

```js
window.API_URL = "http://localhost:8080/";
```

You should change this to be the same as `baseUrl` in `website/siteconfig.json` (or to a different URL, in the unlikely scenario that you have the backend and the frontend at different URLs).

# Preparing Lexonomy (part 2)

You are still in the `website` directory with your terminal.

6. Install Python dependencies (= Python modules required by the Python backend):

```sh
pip install -r requirements.txt
```

7. Run an initialization script to create user accounts for the administrators listed under `admins` in `website/siteconfig.json`. To do this, go to your terminal, go the `website` directory and run this:

```sh
python3 adminscripts/init.py
```

The script will tell you that it has created user accounts for the administrators and what their passwords are. **Note this information down:** you will need it later to log into your local installation of Lexonomy (and perhaps change the password then).

From now on, you have two options: either running Lexonomy locally in your computer (described in the following section) or running Lexonomy in a Docker container (decribed in the next section after that). 

# Option 1: running Lexonomy locally

Congratulations, your Lexonomy installation is now fully configured and ready to face the world. You should be able to start it by (still in the `website` directory);

```sh
python3 lexonomy.py
```
An instance of Lexonomy will start at the address http://localhost:8080/ (or whataver other port number you had configured in `siteconfig.json`). If you had configured Lexonomy to run on port 80 or some other privileged port, you will need to run Lexonomy with superuser permissions:

```sh
sudo python3 lexonomy.py
```

Either way, you should now be able to navigate to the URL with your web browser, see Lexonomy's home page, and log in with the information you had noted down in step 7 above.

## Running a standalone server

If you have the [Paste](https://pythonpaste.readthedocs.io/en/latest/) Python module installed, it will use that one (it provides a multi-threaded web server). Otherwise it will use a Bottle built-in web server which is single-threaded. To manage the server in a Linux environment, you can use the provided [systemd unit file](website/docs/lexonomy.service)

## Running as CGI or WSGI inside of Apache

You can run Lexonomy inside Apache as CGI or WSGI. For the latter please refer to the relevant [Bottle](http://bottlepy.org) documentation (the Bottle app is WSGI-compatible), for the former you can get inspiration in the [configuration file](website/docs/lexonomy_httpd.conf) which is part of Lexonomy.

## Upgrading to newer versions

You should generally be able to upgrade by copying new files over and running an update script to upgrade DB schemas. The upgrade script is idempotent so you may run it at any time or multiple times with no harm:

```sh
python3 adminscripts/updates.py
```

# Option 2: running Lexonomy in a Docker container

This repository contains a Dockerfile which you can use to "package" your configured installation of Lexonomy into a Docker image. The Docker image can then be either run locally, or uploaded to a server for hosting.

You need to have [Docker](https://www.docker.com/) installed on your computer to do this.

To build a Docker image, navigate to the repository's root directory with your terminal (one level up from `website`) and run:

```sh
sudo docker build ./
```

You will get a long output, at the end of which Docker will inform you that it has created an image and what name it has given it. The name will be a long string like this:

```
sha256:e715179b993a67777c2307bcfc7dc5315005d89af8aa9187564063f0a49a9ee2
```

To run the image you have just created, type this (replace the image name with the name of your image from the previous step):

```sh
sudo docker run -p8080:8080 sha256:e715179b993a67777c2307bcfc7dc5315005d89af8aa9187564063f0a49a9ee2
```

The parameter `-p8080:8080` tells Docker to publish the container's port 8080 as your computer's port 8080. You should now be able to navigate to http://localhost:8080/ and use Lexonomy.

For more information on Docker images and containers, how to run them and stop them, and what else you can do with them, refer to [Docker's own documentation](https://docs.docker.com/).
