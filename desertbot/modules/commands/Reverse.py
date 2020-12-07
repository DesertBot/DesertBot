"""
Created on Nov 07, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Reverse(BotCommand):
    def triggers(self):
        return ['reverse', 'backwards']

    def help(self, query):
        return 'reverse <text> - reverses the text given to it'

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            return IRCResponse(message.parameters[::-1], message.replyTo)
        else:
            return IRCResponse('Reverse what?', message.replyTo)


reverse = Reverse()
