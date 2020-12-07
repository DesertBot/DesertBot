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
        return "shorten <url> - Gives you a shortened version of a url, via https://dbco.link"

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse("You didn't give a URL to shorten!", message.replyTo)

        url = self.bot.moduleHandler.runActionUntilValue('shorten-url',
                                                         message.parameters)

        if not url:
            return IRCResponse("No url returned from dbco.link, "
                               "are both pb and mongodb running?", message.replyTo)

        return IRCResponse(url, message.replyTo)


shorten = Shorten()
