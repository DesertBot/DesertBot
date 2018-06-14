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

    colours = [assembleFormattedText(A.fg.white['']),        #0
               assembleFormattedText(A.fg.black['']),        #1
               assembleFormattedText(A.fg.blue['']),         #2
               assembleFormattedText(A.fg.green['']),        #3
               assembleFormattedText(A.fg.lightRed['']),     #4
               assembleFormattedText(A.fg.red['']),          #5
               assembleFormattedText(A.fg.magenta['']),      #6
               assembleFormattedText(A.fg.orange['']),       #7
               assembleFormattedText(A.fg.yellow['']),       #8
               assembleFormattedText(A.fg.lightGreen['']),   #9
               assembleFormattedText(A.fg.cyan['']),         #10
               assembleFormattedText(A.fg.lightCyan['']),    #11
               assembleFormattedText(A.fg.lightBlue['']),    #12
               assembleFormattedText(A.fg.lightMagenta['']), #13
               assembleFormattedText(A.fg.gray['']),         #14
               assembleFormattedText(A.fg.lightGray['']),    #15
               ]
    
    bgcolours = [assembleFormattedText(A.bg.white['']),        #0
                 assembleFormattedText(A.bg.black['']),        #1
                 assembleFormattedText(A.bg.blue['']),         #2
                 assembleFormattedText(A.bg.green['']),        #3
                 assembleFormattedText(A.bg.lightRed['']),     #4
                 assembleFormattedText(A.bg.red['']),          #5
                 assembleFormattedText(A.bg.magenta['']),      #6
                 assembleFormattedText(A.bg.orange['']),       #7
                 assembleFormattedText(A.bg.yellow['']),       #8
                 assembleFormattedText(A.bg.lightGreen['']),   #9
                 assembleFormattedText(A.bg.cyan['']),         #10
                 assembleFormattedText(A.bg.lightCyan['']),    #11
                 assembleFormattedText(A.bg.lightBlue['']),    #12
                 assembleFormattedText(A.bg.lightMagenta['']), #13
                 assembleFormattedText(A.bg.gray['']),         #14
                 assembleFormattedText(A.bg.lightGray['']),    #15
                 ]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say,
                               "You didn't give me any text to rainbow!",
                               message.replyTo)
        
        if message.command == 'rainbow':
            fg = True
        else:
            fg = False

        startPos = 0
        try:
            colList = [int(n) for n in message.parameterList[0].split(',')]
            startPos = len(message.parameterList[0]) + 1
        except ValueError:
            if fg:
                colList = [4,8,9,11,12,13]
            else:
                colList = [5,7,8,3,10,2,6]

        if not message.parameters[startPos:]:
            return IRCResponse(ResponseType.Say,
                               "You didn't give me any text to rainbow after the colours!",
                               message.replyTo)

        outputMessage = u''

        if fg:
            for i, c in enumerate(message.parameters[startPos:]):
                outputMessage += self.colours[colList[i % len(colList)]] + c
        else:
            for i, c in enumerate(message.parameters[startPos:]):
                outputMessage += self.bgcolours[colList[i % len(colList)]] + c

        outputMessage += assembleFormattedText(A.normal[''])

        return IRCResponse(ResponseType.Say, outputMessage, message.replyTo)


rainbow = Rainbow()
