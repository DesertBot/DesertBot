# -*- coding: utf-8 -*-
"""
Created on Dec 20, 2011

@author: Tyranic-Moron
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
        return "source - returns a link to {0}'s source".format(self.bot.nickname)

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        return IRCResponse(ResponseType.Say, self.bot.sourceURL, message.ReplyTo)


source = Source()
