# -*- coding: utf-8 -*-
"""
Created on Dec 20, 2011

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Nick(BotCommand):
    def triggers(self):
        return ['nick', 'name']

    def help(self, query):
        return "nick <nick> - changes the bot's nick to the one specified"

    @admin
    def execute(self, message: IRCMessage):
        if len(message.ParameterList) > 0:
            return IRCResponse(ResponseType.Raw, 'NICK %s' % (message.ParameterList[0]), '')
        else:
            return IRCResponse(ResponseType.Say, 'Change my %s to what?' % message.Command, message.ReplyTo)


nick = Nick()
