"""
Created on Feb 14, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, ignore
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import copy
try:
    import re2
except ImportError:
    import re as re2
import re
import sre_constants

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Sed(BotCommand):
    def actions(self):
        return super(Sed, self).actions() + [('message-channel', 1, self.handleSed),
                                             ('message-user', 1, self.handleSed),
                                             ('action-channel', 1, self.storeMessage),
                                             ('action-user', 1, self.storeMessage)]

    def triggers(self):
        return ['sed']

    historySize = 20

    def help(self, query):
        return ('s/search/replacement/[flags] [input for c flag]'
                ' - matches sed-like regex replacement patterns and'
                ' attempts to execute them on the latest matching line from the last {}\n'
                'flags are'
                ' g (global),'
                ' i (case-insensitive),'
                ' o (only user messages),'
                ' v (verbose, ignores whitespace),'
                ' c (chained)\n'
                'Example usage:'
                ' "I\'d eat some tacos" -> s/some/all the/ -> "I\'d eat all the tacos"'
                .format(self.historySize))

    def onLoad(self):
        self.messages = {}
        self.unmodifiedMessages = {}

    @ignore
    def handleSed(self, message):
        if message.command and message.command.lower() in self.bot.moduleHandler.mappedTriggers:
            return

        match = self.match(message.messageString)

        return self.sed(message, match)

    def execute(self, message: IRCMessage):
        match = self.match(message.parameters)

        return self.sed(message, match)

    def sed(self, message, match):
        if match:
            search, replace, flags, text = match
            response = self.substitute(search, replace, flags, text, message, message.replyTo)

            if response is not None:
                responseType = ResponseType.Say
                if response.type == 'ACTION':
                    responseType = ResponseType.Do

                return IRCResponse(responseType, response.messageString, message.replyTo)

            else:
                return IRCResponse(ResponseType.Say,
                                   "No text matching '{}' found in the last {} messages"
                                   .format(search, self.historySize),
                                   message.replyTo)

        else:
            self.storeMessage(message)

    @classmethod
    def match(cls, message):
        """Returns (search, replace, flags) if message is a replacement pattern, otherwise None"""
        if not (message.startswith('s/') or message.startswith('S/')):
            return
        parts = re.split(r'(?<!\\)/', message)
        if len(parts) < 3:
            return
        search, replace = parts[1:3]
        if len(parts) >= 4:
            flags = parts[3].split(' ')[0]
        else:
            flags = ''
        if len(parts) >= 4:
            text = ' '.join('/'.join(parts[3:]).split(' ')[1:])
        else:
            text = ''
        return search, replace, flags, text

    def substitute(self, search, replace, flags, text, inputMessage, channel):
        # Apparently re.sub understands escape sequences in the replacement string;
        #  strip all but the backreferences
        replace = replace.replace('\\', '\\\\')
        replace = re.sub(r'\\([1-9][0-9]?([^0-9]|$))', r'\1', replace)

        if channel not in self.messages:
            self.messages[channel] = []
            self.unmodifiedMessages[channel] = []

        messages = self.unmodifiedMessages[channel] if 'o' in flags else self.messages[channel]

        if 'g' in flags:
            count = 0
        else:
            count = 1

        subFlags = 0
        if 'i' in flags:
            subFlags |= re.IGNORECASE
        if 'v' in flags:
            subFlags |= re.VERBOSE

        if 'c' in flags:
            newMessage = copy.copy(inputMessage)

            try:
                searchC = re2.compile(search, subFlags)
                new = searchC.sub(replace, text, count)
            except sre_constants.error as e:
                newMessage.messageString = "[Regex Error in Sed pattern: {}]".format(e.message)
                return newMessage

            if new != text:
                newMessage.messageString = new
                self.storeMessage(newMessage, False)
            else:
                newMessage.messageString = text
                self.storeMessage(newMessage, False)

            return newMessage

        for message in reversed(messages):
            try:
                searchC = re2.compile(search, subFlags)
                new = searchC.sub(replace, message.messageString, count)
            except sre_constants.error as e:
                newMessage = copy.copy(inputMessage)
                newMessage.messageString = "[Regex Error in Sed pattern: {}]".format(e.message)
                return newMessage

            new = new[:300]

            if searchC.search(message.messageString):
                newMessage = copy.copy(message)
                newMessage.messageString = new
                self.storeMessage(newMessage, False)
                return newMessage

        return None

    def storeMessage(self, message, unmodified=True):
        if message.replyTo not in self.messages:
            self.messages[message.replyTo] = []
            self.unmodifiedMessages[message.replyTo] = []
        userList = self.unmodifiedMessages[message.replyTo]
        userList.append(message)
        self.messages[message.replyTo] = userList[-self.historySize:]

        if unmodified:
            userList = self.unmodifiedMessages[message.replyTo]
            userList.append(message)
            self.unmodifiedMessages[message.replyTo] = userList[-self.historySize:]


sed = Sed()
