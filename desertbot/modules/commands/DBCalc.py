from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import math

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class DBCalc(BotCommand):
    def triggers(self):
        return ['dbcalc']

    def help(self, query):
        return ('dbcalc (hours <hours> / money <money>)'
                ' - tells you how much money is required for a given number of hours,'
                ' or how many hours will be bussed for a given amount of money')

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        if message.parameterList[0].lower() == 'hours':
            return IRCResponse(ResponseType.Say,
                               DBCalc.hours(message.parameterList[1]),
                               message.replyTo)
        elif message.parameterList[0].lower() == 'money':
            return IRCResponse(ResponseType.Say,
                               DBCalc.money(message.parameterList[1]),
                               message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

    @classmethod
    def hours(cls, hours):

        try:
            f_hours = float(hours)
        except ValueError:
            return "Sorry, I don't recognize '{0}' as a number".format(hours)

        try:
            money = (1-(1.07**f_hours))/(-0.07)
        except OverflowError:
            return ("The amount of money you would need for"
                    " that many hours is higher than I can calculate!")

        return "For {0:,} hour(s), the team needs a total of ${1:,.2f}".format(f_hours, money)

    @classmethod
    def money(cls, money):

        try:
            f_money = float(money)
        except ValueError:
            return "Sorry, I don't recognize '{0}' as a number".format(money)

        try:
            hours = math.log((7*f_money)/100 + 1)/math.log(1.07)
        except OverflowError:
            return "???"

        return "With ${0:,.2f}, the team will bus for {1:,.2f} hour(s)".format(f_money, hours)


dbcalc = DBCalc()
