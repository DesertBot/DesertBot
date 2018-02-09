# -*- coding: utf-8 -*-
"""
Created on Dec 07, 2014

@author: Tyranic-Moron
"""

from CommandInterface import CommandInterface
from IRCMessage import IRCMessage
from IRCResponse import IRCResponse, ResponseType

from twisted.conch.manhole_tap import makeService
from twisted.internet.error import CannotListenError
import os


class Manhole(CommandInterface):
    triggers = ['manhole']
    help = "A debug module that uses Twisted's Manhole to poke at the bot's innards"
    runInThread = True

    manhole = None
    port = 4040

    def onLoad(self):
        while self.manhole is None or not self.manhole.running:
            try:
                self.manhole = makeService({
                    "namespace": {"bot": self.bot},
                    "passwd": os.path.join("Data", "manhole.passwd"),
                    "telnetPort": None,
                    "sshPort": str(self.port),
                    "sshKeyDir": os.path.join("Data"),
                    "sshKeyName": "manhole.sshkey",
                    "sshKeySize": 4096
                })
                self.manhole.startService()
            except CannotListenError:
                self.port += 1

    def onUnload(self):
        self.manhole.stopService()

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        if self.checkPermissions(message):
            return IRCResponse(ResponseType.Notice, "Manhole port: {}".format(self.port), message.User.Name)
