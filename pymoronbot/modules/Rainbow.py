# -*- coding: utf-8 -*-
"""
Created on May 04, 2014

@author: Tyranic-Moron
"""

from pymoronbot.moduleinterface import ModuleInterface
from pymoronbot.message import IRCMessage
from pymoronbot.response import IRCResponse, ResponseType

from twisted.words.protocols.irc import assembleFormattedText, attributes as A


class Rainbow(ModuleInterface):
    triggers = ['rainbow', 'rrainbow']
    help = 'rainbow <text> - outputs the specified text with rainbow colours; rrainbow uses background colours'

    colours = [assembleFormattedText(A.fg.lightRed['']),
               #assembleFormattedText(A.fg.orange['']),
               assembleFormattedText(A.fg.yellow['']),
               assembleFormattedText(A.fg.lightGreen['']),
               assembleFormattedText(A.fg.lightCyan['']),
               assembleFormattedText(A.fg.lightBlue['']),
               assembleFormattedText(A.fg.lightMagenta['']),
               ]
    
    bgcolours = [assembleFormattedText(A.bg.red['']),
                 assembleFormattedText(A.bg.orange['']),
                 assembleFormattedText(A.bg.yellow['']),
                 assembleFormattedText(A.bg.green['']),
                 assembleFormattedText(A.bg.cyan['']),
                 assembleFormattedText(A.bg.blue['']),
                 assembleFormattedText(A.bg.magenta['']),
                 ]

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        if len(message.ParameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give me any text to rainbow!", message.ReplyTo)

        outputMessage = u''

        if message.Command == 'rainbow':
            for i, c in enumerate(message.Parameters):
                outputMessage += self.colours[i % len(self.colours)] + c
        else:
            for i, c in enumerate(message.Parameters):
                outputMessage += self.bgcolours[i % len(self.bgcolours)] + c

        outputMessage += assembleFormattedText(A.normal[''])

        return IRCResponse(ResponseType.Say, outputMessage, message.ReplyTo)
