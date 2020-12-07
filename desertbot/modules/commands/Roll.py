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
                ' #d#(kh#/kl#/dh#/dl#/!/r/ro/c/s/sa/sd), + - * / % ^ ( ) #comments'
                ' | see https://git.io/pyhedrals-help for example usage'
                ' and a detailed explanation of the dice modifiers')

    def onLoad(self):
        self.roller = dice.DiceRoller()

    def execute(self, message: IRCMessage):
        verbose = False
        if message.command.lower().endswith('v'):
            verbose = True
            
        if not message.parameters.strip():
            return IRCResponse(('Error: roll what? (roll expects #d# dice expressions, '
                                f'see {self.bot.commandChar}help roll for details)'), message.replyTo)

        try:
            result = self.roller.parse(message.parameters)
        except OverflowError:
            return IRCResponse('Error: result too large to calculate', message.replyTo)
        except (ZeroDivisionError,
                dice.UnknownCharacterException,
                dice.SyntaxErrorException,
                dice.InvalidOperandsException,
                RecursionError,
                NotImplementedError) as e:
            return IRCResponse('Error: {}'.format(e), message.replyTo)

        if verbose:
            rollString = ' | '.join(result.strings())

            if len(rollString) > 200:
                rollString = "LOTS O' DICE"

            response = '{} rolled: [{}] {}'.format(message.user.nick, rollString, result.result)

        else:
            response = '{} rolled: {}'.format(message.user.nick, result.result)

        if result.description:
            response += ' {}'.format(result.description)

        return IRCResponse(response, message.replyTo, metadata={'var': {'rollTotal': result.result}})


roll = Roll()
