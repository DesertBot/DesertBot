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
class Do(BotCommand):
    def triggers(self):
        return ['do']

    def help(self, query):
        return 'do <text> - makes the bot perform the specified text'

    def execute(self, message: IRCMessage):
        if len(message.ParameterList) > 0:
            return IRCResponse(ResponseType.Do, message.Parameters, message.ReplyTo)
        else:
            return IRCResponse(ResponseType.Do, 'Do what?', message.ReplyTo)


do = Do()
