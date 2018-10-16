"""
Created on Dec 06, 2016

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Currency(BotCommand):
    def triggers(self):
        return ['currency']

    def help(self, query):
        return ("currency [<amount>] <from> in <to>"
                " - converts <amount> in <from> currency to <to> currency")

    runInThread = True

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 3:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        try:
            amount = float(message.parameterList[0])
            offset = 1
        except ValueError:
            amount = 1.0
            offset = 0

        ccFrom = message.parameterList[offset].upper()
        ccTo = message.parameterList[offset + 2:]
        ccTo = ",".join(ccTo)
        ccTo = ccTo.upper()

        url = "https://exchangeratesapi.io/api/latest"
        params = {
            'base': ccFrom,
            'symbols': ccTo,
            }
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url, params=params)
        j = response.json()
        rates = j['rates']

        if not rates:
            return IRCResponse(ResponseType.Say,
                               "Some or all of those currencies weren't recognized!",
                               message.replyTo)

        data = []
        for curr, rate in rates.items():
            data.append("{:.2f} {}".format(rate*amount, curr))

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        return IRCResponse(ResponseType.Say, graySplitter.join(data), message.replyTo)


currency = Currency()
