"""
Created on Dec 20, 2011

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Source(BotCommand):
    def triggers(self):
        return ['source']

    def help(self, query):
        return "source - returns a link to {0}'s source".format(self.bot.nick)

    def execute(self, message: IRCMessage):
        sourceURL = self.bot.config.getWithDefault('source',
                                                   'https://github.com/DesertBot/DesertBot/')
        return IRCResponse(ResponseType.Say,
                           sourceURL,
                           message.replyTo)


source = Source()
