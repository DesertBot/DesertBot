"""
Created on May 04, 2014

@author: StarlitGhost
"""
import random

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class Choose(BotCommand):
    def triggers(self):
        return ['choose']

    def help(self, query):
        return ('choose <option1>, <option2>[, <optionN>]'
                ' - randomly chooses one of the given options for you')

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse("You didn't give me any options to choose from! {}"
                               .format(self.help(None)), message.replyTo)

        if ',' in message.parameters:
            options = message.parameters.split(',')
        else:
            options = message.parameters.split()

        choice = random.choice(options).strip()

        return IRCResponse(choice, message.replyTo, metadata={'var': {'chooseChoice': choice}})


choose = Choose()
