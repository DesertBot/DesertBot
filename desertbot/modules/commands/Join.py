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
class Join(BotCommand):
    def triggers(self):
        return ['join']

    def help(self, query):
        return 'join <channel> - makes the bot join the specified channel(s)'

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            responses = []
            for param in message.parameterList:
                channel = param
                if not channel.startswith('#'):
                    channel = '#' + channel
                responses.append(IRCResponse(ResponseType.Raw, 'JOIN {0}'.format(channel), ''))
            return responses
        else:
            return IRCResponse(ResponseType.Say,
                               "{0}, you didn't say where I should join".format(message.user.nick),
                               message.replyTo)


join = Join()
