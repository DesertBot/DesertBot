"""
Created on Oct 16, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Notice(BotCommand):
    def triggers(self):
        return ['notice']

    def help(self, query):
        return ('notice <target> <text>'
                ' - makes the bot send the specified text as a notice to the specified target')

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 1:
            return IRCResponse(" ".join(message.parameterList[1:]), message.parameterList[0], ResponseType.Notice)
        else:
            return IRCResponse(self.help(None), message.replyTo)


notice = Notice()
