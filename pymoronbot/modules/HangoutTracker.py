# -*- coding: utf-8 -*-
"""
Created on Dec 13, 2011

@author: Tyranic-Moron
"""

import re
import datetime

from pymoronbot.moduleinterface import ModuleInterface
from pymoronbot.message import IRCMessage
from pymoronbot.response import IRCResponse, ResponseType
from pymoronbot.utils import string


class Data(object):
    lastCode = None
    lastDate = None
    lastUser = None


class HangoutTracker(ModuleInterface):
    triggers = ['hangout', 'hangoot']
    help = 'hangout - gives you the last posted G+ hangout link'
    acceptedTypes = ['PRIVMSG','ACTION','JOIN']

    def onLoad(self):
        if 'HangoutTracker' not in self.bot.dataStore:
            self.bot.dataStore['HangoutTracker'] = {}

        self.hangoutDict = self.bot.dataStore['HangoutTracker']

    def _syncHangoutDict(self):
        self.bot.dataStore['HangoutTracker'] = self.hangoutDict
        self.bot.dataStore.sync()

    def shouldExecute(self, message):
        """
        @type message: IRCMessage
        """
        if message.Type in self.acceptedTypes:
            return True

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        match = re.search('^hango+?u?t$', message.Command, re.IGNORECASE)
        if match or ((message.Type == 'JOIN') and (message.User.Name == 'Emily[iOS]')):
            if message.ReplyTo not in self.hangoutDict:
                self.hangoutDict[message.ReplyTo] = None
                self._syncHangoutDict()
            if self.hangoutDict[message.ReplyTo] is None:
                return IRCResponse(ResponseType.Say,
                                   'No hangouts posted here yet',
                                   message.ReplyTo)

            hangout = self.hangoutDict[message.ReplyTo]

            timeDiff = datetime.datetime.utcnow() - hangout.lastDate
            url = 'https://talkgadget.google.com/hangouts/_/{0}'.format(hangout.lastCode)
            byLine = 'first linked {0} ago'.format(string.deltaTimeToString(timeDiff))

            if ((message.Type == 'JOIN') and (message.User.Name == 'Emily[iOS]')):
                response = 'Welcome Back, Lady Emily.  Here\'s the hangout for your streaming pleasure: http://bit.ly/DBHangoutReloaded'
            else:
                response = 'Last hangout linked: {0} ({1})'.format(url, byLine)

            return IRCResponse(ResponseType.Say, response, message.ReplyTo)

        match = re.search(r'google\.com/hangouts/_/(?P<code>[^\?\s]+)',
                          message.MessageString,
                          re.IGNORECASE)

        if not match:
            return

        if message.ReplyTo not in self.hangoutDict or self.hangoutDict[message.ReplyTo] is None:
            self.hangoutDict[message.ReplyTo] = Data()
        elif match.group('code') == self.hangoutDict[message.ReplyTo].lastCode:
            return

        self.hangoutDict[message.ReplyTo].lastCode = match.group('code')
        self.hangoutDict[message.ReplyTo].lastUser = message.User.Name
        self.hangoutDict[message.ReplyTo].lastDate = datetime.datetime.utcnow()

        self._syncHangoutDict()

        return
