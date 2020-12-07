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


@implementer(IPlugin, IModule)
class CheckURL(BotCommand):
    def triggers(self):
        return ['checkurl']

    def help(self, query):
        return "checkurl <url> - checks if the given url is available for registration"

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 1:
            return IRCResponse(self.help(None), message.replyTo)

        urlToCheck = message.parameterList[0]
        apiKey = self.bot.moduleHandler.runActionUntilValue("get-api-key", "WebCargo")
        url = "https://api.webcargo.io/availability"
        params = {
            'key': apiKey,
            'domain': urlToCheck,
        }

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url, params=params)

        if not response:
            if response.status_code == 500:
                return IRCResponse("{!r} doesn't contain a valid TLD", message.replyTo)

            return IRCResponse("[WebCargo domain checker failed to respond]", message.replyTo)

        j = response.json()

        if "message" in j:
            return IRCResponse("{!r} is not a valid url".format(urlToCheck), message.replyTo)

        if "is_available" in j:
            if j["is_available"]:
                return IRCResponse("{!r} is available!".format(urlToCheck), message.replyTo)
            else:
                return IRCResponse("{!r} is not available".format(urlToCheck), message.replyTo)


checkURL = CheckURL()
