"""
Created on May 10, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import pyhedrals as dice


@implementer(IPlugin, IModule)
class Roll(BotCommand):
    def triggers(self):
        return ['roll', 'rollv']

    def help(self, query):
        return ('roll(v) - dice roller, \'rollv\' outputs every roll.'
                ' supported operators are'
                ' #d#(kh#/kl#/dh#/dl#/!/r/ro/s/sa/sd), + - * / % ^ ( ) #comments'
                ' | see https://git.io/PyMoBo-Roll for example usage'
                ' and a detailed explanation of the dice modifiers')

    def onLoad(self):
        self.roller = dice.DiceRoller()

    def execute(self, message: IRCMessage):
        verbose = False
        if message.command.lower().endswith('v'):
            verbose = True

        try:
            result = self.roller.parse(message.parameters)
        except OverflowError:
            return IRCResponse(ResponseType.Say,
                               'Error: result too large to calculate',
                               message.replyTo)
        except (ZeroDivisionError,
                dice.UnknownCharacterException,
                dice.SyntaxErrorException,
                dice.InvalidOperandsException,
                RecursionError,
                NotImplementedError) as e:
            return IRCResponse(ResponseType.Say,
                               'Error: {}'.format(e),
                               message.replyTo)

        if verbose:
            rollStrings = self.roller.getRollStrings()
            rollString = ' | '.join(rollStrings)

            if len(rollString) > 200:
                rollString = "LOTS O' DICE"

            response = '{} rolled: [{}] {}'.format(message.user.nick, rollString, result)

        else:
            response = '{} rolled: {}'.format(message.user.nick, result)

        if self.roller.description:
            response += ' {}'.format(self.roller.description)

        return IRCResponse(ResponseType.Say, response, message.replyTo,
                           {'rollTotal': result})


roll = Roll()
