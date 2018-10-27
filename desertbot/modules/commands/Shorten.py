from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Shorten(BotCommand):
    def triggers(self):
        return ['shorten']

    def help(self, query):
        return ("shorten <url> - Gives you a shortened version of a url, via https://dbco.link")

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say,
                               "You didn't give a URL to shorten!",
                               message.replyTo)

        url = self.bot.moduleHandler.runActionUntilValue('shorten-url',
                                                         message.parameters)

        return IRCResponse(ResponseType.Say, url, message.replyTo)


shorten = Shorten()
