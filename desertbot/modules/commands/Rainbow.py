"""
Created on May 04, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A


@implementer(IPlugin, IModule)
class Rainbow(BotCommand):
    def triggers(self):
        return ['rainbow', 'rrainbow']

    def help(self, query):
        return ('rainbow <text>'
                ' - outputs the specified text with rainbow colours;'
                ' rrainbow uses background colours')

    colours = [colour(A.fg.white['']),         # 0
               colour(A.fg.black['']),         # 1
               colour(A.fg.blue['']),          # 2
               colour(A.fg.green['']),         # 3
               colour(A.fg.lightRed['']),      # 4
               colour(A.fg.red['']),           # 5
               colour(A.fg.magenta['']),       # 6
               colour(A.fg.orange['']),        # 7
               colour(A.fg.yellow['']),        # 8
               colour(A.fg.lightGreen['']),    # 9
               colour(A.fg.cyan['']),          # 10
               colour(A.fg.lightCyan['']),     # 11
               colour(A.fg.lightBlue['']),     # 12
               colour(A.fg.lightMagenta['']),  # 13
               colour(A.fg.gray['']),          # 14
               colour(A.fg.lightGray['']),     # 15
               ]

    bgcolours = [colour(A.bg.white['']),         # 0
                 colour(A.bg.black['']),         # 1
                 colour(A.bg.blue['']),          # 2
                 colour(A.bg.green['']),         # 3
                 colour(A.bg.lightRed['']),      # 4
                 colour(A.bg.red['']),           # 5
                 colour(A.bg.magenta['']),       # 6
                 colour(A.bg.orange['']),        # 7
                 colour(A.bg.yellow['']),        # 8
                 colour(A.bg.lightGreen['']),    # 9
                 colour(A.bg.cyan['']),          # 10
                 colour(A.bg.lightCyan['']),     # 11
                 colour(A.bg.lightBlue['']),     # 12
                 colour(A.bg.lightMagenta['']),  # 13
                 colour(A.bg.gray['']),          # 14
                 colour(A.bg.lightGray['']),     # 15
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
                colList = [4, 8, 9, 11, 12, 13]
            else:
                colList = [5, 7, 8, 3, 10, 2, 6]

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

        outputMessage += colour(A.normal[''])

        return IRCResponse(ResponseType.Say, outputMessage, message.replyTo)


rainbow = Rainbow()
