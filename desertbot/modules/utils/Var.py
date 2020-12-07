"""
Created on Mar 09, 2016

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Var(BotCommand):
    def triggers(self):
        return ['var']

    def help(self, query):
        return ("var <varname> <value>"
                " - sets <varname> to <value>, which can be accessed later using $<varname>."
                " the variables don't persist between messages,"
                " so it is only useful as a support function for aliases using sub and/or chain")

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 1:
            return IRCResponse("You didn't give a variable name!", message.replyTo)

        varname = message.parameterList[0]
        value = ' '.join(message.parameters.split(' ')[1:])
        return IRCResponse("", message.replyTo, metadata={'var': {varname: value}})


var = Var()
