"""
Created on Mar 03, 2015

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import json
import random

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from twisted.words.protocols.irc import assembleFormattedText, attributes as A


# Idea for this initially taken from Heufneutje's RE_HeufyBot Aww module,
#  but I made it more generic for aliasing
# https://github.com/Heufneutje/RE_HeufyBot/blob/f45219d1a61f0ed0fd60a89dcaeb2e962962356e/modules/Aww/src/heufybot/modules/Aww.java
# Future plans:
# - multiple fetch types beyond the current random, eg reddit sort types (top rated, hot, best, etc)
@implementer(IPlugin, IModule)
class RedditImage(BotCommand):
    def triggers(self):
        return ['redditimage']

    def help(self, query):
        return ("redditimage <subreddit> [<range>]"
                " - fetches a random image from the top 100 (or given range)"
                " of the specified subreddit")

    def actions(self):
        return super(RedditImage, self).actions() + [("apikeys-avilable", 1, self.onLoad)]

    def onLoad(self):
        self.imgurClientID = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'imgur Client ID')
        self.headers = [('Authorization', 'Client-ID {}'.format(self.imgurClientID))]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0 or len(message.parameterList) > 2:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        if not self.imgurClientID:
            return IRCResponse(ResponseType.Say,
                               '[imgur client ID not found]',
                               message.replyTo)

        subreddit = message.parameterList[0].lower()
        if len(message.parameterList) == 2:
            try:
                if len(message.parameterList[1]) < 20:
                    topRange = int(message.parameterList[1])
                else:
                    raise ValueError
                if topRange < 0:
                    raise ValueError
            except ValueError:
                return IRCResponse(ResponseType.Say,
                                   "The range should be a positive integer!",
                                   message.replyTo)
        else:
            topRange = 100

        url = "https://api.imgur.com/3/gallery/r/{}/time/all/{}"
        url = url.format(subreddit, random.randint(0, topRange))
        try:
            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url,
                                                                  extraHeaders=self.headers)
            j = response.json()
        except json.JSONDecodeError:
            return IRCResponse(ResponseType.Say,
                               "[The imgur API doesn't appear to be responding correctly]",
                               message.replyTo)

        images = j['data']

        if not images:
            return IRCResponse(ResponseType.Say,
                               "The subreddit '{}' doesn't seem to have"
                               " any images posted to it (or it doesn't exist!)"
                               .format(subreddit),
                               message.replyTo)

        image = random.choice(images)

        data = []
        if 'title' in image and image['title'] is not None:
            data.append(image['title'])
        if 'nsfw' in image and image['nsfw']:
            data.append('\x034\x02NSFW!\x0F')
        if 'animated' in image and image['animated']:
            data.append('\x032\x02Animated!\x0F')
        if 'gifv' in image:
            data.append(image['gifv'])
        else:
            data.append(image['link'])

        graySplitter = assembleFormattedText(A.normal[' ', A.fg.gray['|'], ' '])
        return IRCResponse(ResponseType.Say, graySplitter.join(data), message.replyTo)


redditImage = RedditImage()
