# -*- coding: utf-8 -*-
"""
Created on Feb 13, 2018

@author: Tyranic-Moron
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


@implementer(IPlugin, IModule)
class BotControl(BotCommand):
    def triggers(self):
        return ['restart', 'shutdown']

    @admin
    def _restart(self, message):
        """restart - restarts the bot"""
        # can't restart within 10 seconds of starting (avoids chanhistory triggering another restart)
        if datetime.datetime.utcnow() - self.bot.startTime > datetime.timedelta(seconds=10):
            self.bot.quitting = True
            reactor.addSystemEventTrigger('after',
                                          'shutdown',
                                          lambda: os.execl(sys.executable, sys.executable, *sys.argv))
            if message.Parameters:
                self.bot.quit(message=message.Parameters)
            else:
                self.bot.quit(message=self.bot.config.getWithDefault('restartMessage', 'restarting'))
            reactor.callLater(2.0, reactor.stop)

    @admin
    def _shutdown(self, message):
        """shutdown - shuts down the bot"""
        # can't shutdown within 10 seconds of starting (avoids chanhistory triggering another shutdown)
        if datetime.datetime.utcnow() - self.bot.startTime > datetime.timedelta(seconds=10):
            self.bot.quitting = True
            if message.Parameters:
                self.bot.quit(message=message.Parameters)
            else:
                self.bot.quit(message=self.bot.config.getWithDefault('quitMessage', 'quitting'))
            reactor.callLater(2.0, reactor.stop)

    _commands = OrderedDict([
        (u'restart', _restart),
        (u'shutdown', _shutdown),
    ])

    def help(self, query: str) -> str:
        command = query[0].lower()
        if command in self._commands:
            return self._commands[command].__doc__
        else:
            return u'{} - pretty obvious'.format(u', '.join(self._commands.keys()))

    def execute(self, message: IRCMessage):
        return self._commands[message.command.lower()](self, message)


botcontrol = BotControl()
