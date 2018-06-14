# -*- coding: utf-8 -*-
"""
Created on May 04, 2014

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from twisted.words.protocols.irc import assembleFormattedText, attributes as A


@implementer(IPlugin, IModule)
class Rainbow(BotCommand):
    def triggers(self):
        return ['rainbow', 'rrainbow']

    def help(self, query):
        return 'rainbow <text> - outputs the specified text with rainbow colours; rrainbow uses background colours'

    colours = [assembleFormattedText(A.fg.white['']),
               assembleFormattedText(A.fg.black['']),
               assembleFormattedText(A.fg.blue['']),
               assembleFormattedText(A.fg.green['']),
               assembleFormattedText(A.fg.lightRed['']),
               assembleFormattedText(A.fg.red['']),
               assembleFormattedText(A.fg.magenta['']),
               assembleFormattedText(A.fg.orange['']),
               assembleFormattedText(A.fg.yellow['']),
               assembleFormattedText(A.fg.lightGreen['']),
               assembleFormattedText(A.fg.cyan['']),
               assembleFormattedText(A.fg.lightCyan['']),
               assembleFormattedText(A.fg.lightBlue['']),
               assembleFormattedText(A.fg.lightMagenta['']),
               assembleFormattedText(A.fg.gray['']),
               assembleFormattedText(A.fg.lightGray['']),
               ]
    
    bgcolours = [assembleFormattedText(A.bg.white['']),
                 assembleFormattedText(A.bg.black['']),
                 assembleFormattedText(A.bg.blue['']),
                 assembleFormattedText(A.bg.green['']),
                 assembleFormattedText(A.bg.lightRed['']),
                 assembleFormattedText(A.bg.red['']),
                 assembleFormattedText(A.bg.magenta['']),
                 assembleFormattedText(A.bg.orange['']),
                 assembleFormattedText(A.bg.yellow['']),
                 assembleFormattedText(A.bg.lightGreen['']),
                 assembleFormattedText(A.bg.cyan['']),
                 assembleFormattedText(A.bg.lightCyan['']),
                 assembleFormattedText(A.bg.lightBlue['']),
                 assembleFormattedText(A.bg.lightMagenta['']),
                 assembleFormattedText(A.bg.gray['']),
                 assembleFormattedText(A.bg.lightGray['']),
                 ]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give me any text to rainbow!", message.replyTo)
        
        if message.command == 'rainbow':
            fg = True
        else:
            fg = False

        try:
            colList = [int(n) for n in message.parameterList[0].split(',')]
        except ValueError:
            if fg:
                colList = [4,8,9,11,12,13]
            else:
                colList = [5,7,8,3,10,2,6]

        outputMessage = u''

        if fg:
            for i, c in enumerate(message.parameters):
                outputMessage += self.colours[colList[i % len(colList)]] + c
        else:
            for i, c in enumerate(message.parameters):
                outputMessage += self.bgcolours[colList[i % len(colList)]] + c

        outputMessage += assembleFormattedText(A.normal[''])

        return IRCResponse(ResponseType.Say, outputMessage, message.replyTo)


rainbow = Rainbow()
