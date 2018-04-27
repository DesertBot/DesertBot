# -*- coding: utf-8 -*-
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

tang = {'A': 'ALPHA',
        'B': 'BRAVO',
        'C': 'CHARLIE',
        'D': 'DELTA',
        'E': 'ECHO',
        'F': 'FOXTROT',
        'G': 'GOLF',
        'H': 'HOTEL',
        'I': 'INDIA',
        'J': 'JULIET',
        'K': 'KILO',
        'L': 'LIMA',
        'M': 'MIKE',
        'N': 'NOVEMBER',
        'O': 'OSCAR',
        'P': 'PAPA',
        'Q': 'QUEBEC',
        'R': 'ROMEO',
        'S': 'SIERRA',
        'T': 'TANGO',
        'U': 'UNIFORM',
        'V': 'VICTOR',
        'W': 'WHISKEY',
        'X': 'XRAY',
        'Y': 'YANKEE',
        'Z': 'ZULU',
        '1': 'ONE',
        '2': 'TWO',
        '3': 'THREE',
        '4': 'FOUR',
        '5': 'FIVE',
        '6': 'SIX',
        '7': 'SEVEN',
        '8': 'EIGHT',
        '9': 'NINER',
        '0': 'ZERO',
        '-': 'DASH'}


@implementer(IPlugin, IModule)
class Tango(BotCommand):
    def triggers(self):
        return ['tango']

    def help(self, query):
        return 'tango <words> - reproduces <words> with the NATO phonetic alphabet, because reasons.'

    def execute(self, message: IRCMessage):
        if len(message.ParameterList) == 0:
            return

        response = ' '.join(tang[letter.upper()] if letter.upper() in tang else letter for letter in message.Parameters)
        return IRCResponse(ResponseType.Say,
                           response,
                           message.ReplyTo)


tango = Tango()
