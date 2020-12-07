"""
Created on Feb 13, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

import os
import sys
import datetime
from collections import OrderedDict

from twisted.internet import reactor

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class BotControl(BotCommand):
    def triggers(self):
        return ['nick', 'restart', 'shutdown']

    @admin
    def _nick(self, message):
        """nick - changes the bot's nickname"""
        if len(message.parameterList) > 0:
            return IRCResponse('NICK {}'.format(message.parameterList[0]), '', ResponseType.Raw)
        else:
            return IRCResponse('Change my nickname to what?', message.replyTo)

    @admin
    def _restart(self, message):
        """restart - restarts the bot"""
        # can't restart within 10 seconds of starting
        # (avoids chanhistory triggering another restart)
        if datetime.datetime.utcnow() - self.bot.startTime > datetime.timedelta(seconds=10):
            reactor.addSystemEventTrigger('after',
                                          'shutdown',
                                          lambda: os.execl(sys.executable,
                                                           sys.executable,
                                                           *sys.argv))
            if message.parameters:
                self.bot.disconnect(message.parameters)
            else:
                self.bot.disconnect(self.bot.config.getWithDefault('restartMessage', 'restarting'))
            reactor.callLater(2.0, reactor.stop)

    @admin
    def _shutdown(self, message):
        """shutdown - shuts down the bot"""
        # can't shutdown within 10 seconds of starting
        # (avoids chanhistory triggering another shutdown)
        if datetime.datetime.utcnow() - self.bot.startTime > datetime.timedelta(seconds=10):
            if message.parameters:
                self.bot.disconnect(message.parameters)
            else:
                self.bot.disconnect(self.bot.config.getWithDefault('quitMessage', 'quitting'))
            reactor.callLater(2.0, reactor.stop)

    _commands = OrderedDict([
        ('nick', _nick),
        ('restart', _restart),
        ('shutdown', _shutdown),
    ])

    def help(self, query: str) -> str:
        command = query[0].lower()
        if command in self._commands:
            return self._commands[command].__doc__
        else:
            return '{} - pretty obvious'.format(', '.join(self._commands.keys()))

    def execute(self, message: IRCMessage):
        return self._commands[message.command.lower()](self, message)


botcontrol = BotControl()
