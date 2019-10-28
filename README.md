DesertBot [![Build Status](https://travis-ci.com/DesertBot/DesertBot.svg?branch=master)](https://travis-ci.com/DesertBot/DesertBot) [![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/starlitghost/desertbot.svg)](https://hub.docker.com/r/starlitghost/desertbot) [![Updates](https://pyup.io/repos/github/DesertBot/DesertBot/shield.svg)](https://pyup.io/repos/github/DesertBot/DesertBot/)
=========

A modular IRC bot with extensive aliasing capabilities, written in Python.

Features
--------
* [Alias](desertbot/modules/utils/Alias.py) any of the following to create new commands on-the-fly, and then alias *those* aliases to create even more
* Use [Slurp](desertbot/modules/utils/Slurp.py) to extract data from HTML/XML
* Use [Jostle](desertbot/modules/utils/Jostle.py) to extract data from JSON
* Use [Sub](desertbot/modules/utils/Sub.py) or [Chain](desertbot/modules/utils/Chain.py) to link multiple modules together
  * and use [Var](desertbot/modules/utils/Var.py) to store data for use within the same command (eg, a URL you want to slurp multiple times)
* [Follows URLs](desertbot/modules/urlfollow/URLFollow.py) posted in chat to see where they lead (following all redirects), responding with the page title and final hostname
  * with specialised follows to get extra relevant information from Imgur, KickStarter, Steam, Twitch, Twitter, and YouTube links
* Recognizes [sed-like](desertbot/modules/commands/Sed.py) patterns in chat and replaces the most recent match in the last 20 messages
* Also recognizes [`*correction`](desertbot/modules/automatic/AsterFix.py) style corrections and replaces the most likely candidate word in that user's previous message
* [AutoPaste](desertbot/modules/postprocess/AutoPaste.py) detects when single responses are longer than ~2 IRC messages, and submits them to a pastebin service instead, replacing the response with a link
* Consistent help for any module via the [Help](desertbot/modules/commands/Help.py) module
* And many more (take a look in [modules](desertbot/modules))

All of these features can be individually enabled/disabled by loading or unloading the module that provides them

Installation Instructions
-------------------------
* Install Python 3+
* Clone the repo with `git clone https://github.com/DesertBot/DesertBot.git`
* Create a virtualenv to run the bot in, and activate it
* Run `pip install -r requirements.txt` to install all the requirements
* Edit [_defaults.yaml](configs/_defaults.yaml) to set the bot owner and other details
* Copy [server.yaml.example](configs/server.yaml.example) and create a server config (you'll want one of these per IRC network)

Running the Bot
---------------
Activate your virtualenv, and run `python start.py -c configs/server.yaml`

You can run `python start.py -h` for help with the command line args

Docker Instructions
-------------------
This could be streamlined a bit more, but for now:

* Clone the repo with `git clone https://github.com/DesertBot/DesertBot.git`
* Edit [_defaults.yaml](configs/_defaults.yaml) to set the bot owner and other details
* Copy [server.yaml.example](configs/server.yaml.example) and create a server config (you'll want one of these per IRC network)
* Copy [docker-compose-example.yml](docker-compose-example.yml) to docker-compose.yml and edit in the config file you created above
* `docker-compose up -d desertbot-server`
