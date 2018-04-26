# -*- coding: utf-8 -*-
"""
Created on Feb 05, 2014

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class CommandChar(BotCommand):
    def triggers(self):
        return ['commandchar']

    def help(self, query):
        return "commandchar <char> - changes the prefix character for bot commands (admin-only)"

    @admin("Only my admins can change my command character")
    def execute(self, message: IRCMessage):
        if len(message.ParameterList) > 0:
            self.bot.commandChar = message.ParameterList[0]
            self.bot.config['commandChar'] = self.bot.commandChar
            self.bot.config.writeConfig()
            return IRCResponse(ResponseType.Say,
                               'Command prefix char changed to \'{0}\'!'.format(self.bot.commandChar),
                               message.ReplyTo)
        else:
            return IRCResponse(ResponseType.Say, 'Change my command character to what?', message.ReplyTo)


commandchar = CommandChar()
