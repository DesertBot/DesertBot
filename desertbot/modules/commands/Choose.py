"""
Created on May 04, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import random

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Choose(BotCommand):
    def triggers(self):
        return ['choose']

    def help(self, query):
        return ('choose <option1>, <option2>[, <optionN>]'
                ' - randomly chooses one of the given options for you')

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say,
                               "You didn't give me any options to choose from! {}"
                               .format(self.help(None)),
                               message.replyTo)

        if ',' in message.parameters:
            options = message.parameters.split(',')
        else:
            options = message.parameters.split()

        choice = random.choice(options).strip()

        return IRCResponse(ResponseType.Say, choice, message.replyTo, metadata={'var': {'chooseChoice': choice}})


choose = Choose()
