"""
Created on Dec 07, 2014

@author: StarlitGhost
"""
import os

from twisted.conch.manhole_tap import makeService
from twisted.internet.error import CannotListenError
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Manhole(BotCommand):
    def triggers(self):
        return ['manhole']

    def help(self, query):
        return "A debug module that uses Twisted's Manhole to poke at the bot's innards"

    manhole = None
    port = 4040

    def onLoad(self):
        while self.manhole is None or not self.manhole.running:
            try:
                self.manhole = makeService({
                    "namespace": {"bot": self.bot},
                    "passwd": os.path.join("data", "manhole.passwd"),
                    "telnetPort": None,
                    "sshPort": "tcp:{}:interface=127.0.0.1".format(self.port),
                    "sshKeyDir": os.path.join("data"),
                    "sshKeyName": "manhole.sshkey",
                    "sshKeySize": 4096
                })
                self.manhole.startService()
            except CannotListenError:
                self.port += 1

    def onUnload(self):
        self.manhole.stopService()

    @admin
    def execute(self, message: IRCMessage):
        return IRCResponse("Manhole port: {}".format(self.port), message.user.nick, ResponseType.Notice)


manhole = Manhole()
