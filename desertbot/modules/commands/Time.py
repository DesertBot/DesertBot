# -*- coding: utf-8 -*-
"""
Created on Jan 20, 2017

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer
from typing import List

from collections import OrderedDict

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import parsedatetime


@implementer(IPlugin, IModule)
class Time(BotCommand):
    def triggers(self):
        return ['time', 'date']

    def onLoad(self):
        self.cal = parsedatetime.Calendar()

    def _time(self, query):
        """time <natural language time query> - returns time from natural language queries
        (eg: in 100 minutes (at 18:00) => 19:40:00)"""
        (date, _) = self.cal.parseDT(query)
        return "{:%H:%M:%S%z}".format(date)

    def _date(self, query):
        """date <natural language date query> - returns dates from natural language queries
        (eg: friday next week => 2017-02-03)"""
        (date, _) = self.cal.parseDT(query)
        return "{:%Y-%m-%d}".format(date)

    _commands = OrderedDict([
        ('time', _time),
        ('date', _date),
        ])

    def help(self, query: List[str]):
        return self._commands[query[0].lower()].__doc__

    def execute(self, message: IRCMessage):
        response = self._commands[message.command](self, message.parameters)
        return IRCResponse(ResponseType.Say, response, message.replyTo)


time = Time()
