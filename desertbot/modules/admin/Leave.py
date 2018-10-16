# -*- coding: utf-8 -*-
"""
Created on Dec 20, 2011

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Leave(BotCommand):
    def triggers(self):
        return ['leave', 'gtfo']

    def help(self, query):
        return "leave/gtfo - makes the bot leave the current channel"

    @admin('Only my admins can tell me to leave')
    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            return IRCResponse(ResponseType.Raw,
                               'PART {} :{}'.format(message.replyTo, message.parameters),
                               '')
        else:
            return IRCResponse(ResponseType.Raw,
                               'PART {} :toodles!'.format(message.replyTo),
                               '')


leave = Leave()
