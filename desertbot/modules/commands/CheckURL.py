# -*- coding: utf-8 -*-
"""
Created on Aug 2, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from desertbot.utils.api_keys import load_key

@implementer(IPlugin, IModule)
class CheckURL(BotCommand):
    def triggers(self):
        return ['checkurl']

    def help(self, query):
        return "checkurl <url> - checks if the given url is available for registration"

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 1:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        urlToCheck = message.parameterList[0]
        apiKey = load_key("WebCargo")
        urlF = "https://api.webcargo.io/availability?key={}&domain={}"
        url = urlF.format(apiKey, urlToCheck)

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        if not response:
            return IRCResponse(ResponseType.Say,
                               "[WebCargo domain checker failed to respond]",
                               message.replyTo)

        j = response.json()

        if "message" in j:
            return IRCResponse(ResponseType.Say,
                               "{!r} is not a valid url".format(urlToCheck),
                               message.replyTo)

        if "is_available" in j:
            if j["is_available"]:
                return IRCResponse(ResponseType.Say,
                                   "{!r} is available!".format(urlToCheck),
                                   message.replyTo)
            else:
                return IRCResponse(ResponseType.Say,
                                   "{!r} is not available".format(urlToCheck),
                                   message.replyTo)

checkURL = CheckURL()
