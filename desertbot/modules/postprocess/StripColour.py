# -*- coding: utf-8 -*-
"""
Created on May 11, 2014

@author: Tyranic-Moron
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from desertbot.response import IRCResponse
from zope.interface import implementer

from desertbot.utils import string


@implementer(IPlugin, IModule)
class StripColour(BotModule):
    def actions(self):
        return super(StripColour, self).actions() + [('response-message', 99, self.execute),
                                                     ('response-action', 99, self.execute),
                                                     ('response-notice', 99, self.execute)]

    def help(self, query):
        return "Automatic module that strips colours from responses " \
               "if colours are blocked by channel mode"

    def execute(self, response: IRCResponse):
        if response.target in self.bot.channels:
            channel = self.bot.channels[response.target]
            if 'c' in channel.modes:
                # strip formatting if colours are blocked on the channel
                response.response = string.stripFormatting(response.response)


stripcolour = StripColour()
