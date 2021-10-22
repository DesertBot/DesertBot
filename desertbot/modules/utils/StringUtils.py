import json
import re
from collections import OrderedDict
from typing import List

from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as ndld
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class StringUtils(BotCommand):
    def triggers(self):
        return ["tojson", "fromjson", "prevmsg", "prev_or_args"]

    def actions(self):
        return super(StringUtils, self).actions() + [('closest-matches', 1, self.closestMatches),
                                                     ('message-channel', 1, self._storeMessage),
                                                     ('message-user', 1, self._storeMessage),
                                                     ('action-channel', 1, self._storeMessage),
                                                     ('action-user', 1, self._storeMessage)]

    def closestMatches(self, search: str, wordList: List[str],
                       numMatches: int, threshold: float) -> List[str]:
        similarities = sorted([(ndld(search, word), word) for word in wordList])
        closeMatches = [word for (diff, word) in similarities if diff <= threshold]
        topN = closeMatches[:numMatches]
        return topN

    def _tojson(self, message: IRCMessage):
        """converts input string to json-escaped string"""
        return IRCResponse(json.dumps(message.parameters), message.replyTo)

    def _fromjson(self, message: IRCMessage):
        """un-escapes json strings"""
        return IRCResponse(str(json.loads(message.parameters)), message.replyTo)

    def _storeMessage(self, message: IRCMessage):
        """stores the current message for _prevmsg to return later"""
        if message.command and message.command.lower() in self.bot.moduleHandler.mappedTriggers:
            # ignore bot commands
            return

        if 'tracking' in message.metadata:
            # ignore internal messages from alias processing
            if any(m in message.metadata['tracking'] for m in ['Sub', 'Chain', 'Alias']):
                return

        self.messages[message.replyTo] = message

    def _prevmsg(self, message: IRCMessage):
        """returns the previous message from the current channel"""
        if message.replyTo not in self.messages:
            return IRCResponse("No previous message stored for this channel yet", message.replyTo)
        msg = self.messages[message.replyTo]
        return IRCResponse(msg.messageString, message.replyTo)

    def _prev_or_args(self, message: IRCMessage):
        """returns the previous message from the current channel,
        or the command arguments if given"""
        if message.parameters:
            return IRCResponse(message.parameters, message.replyTo)
        else:
            return self._prevmsg(message)

    commands = OrderedDict([
        ('tojson', _tojson),
        ('fromjson', _fromjson),
        ('prevmsg', _prevmsg),
        ('prev_or_args', _prev_or_args),
    ])

    def execute(self, message: IRCMessage):
        command = message.command.lower()
        if command in self.commands:
            return self.commands[command](self, message)
        else:
            return IRCResponse(f'"{message.command}" is not a recognized StringUtils command', message.replyTo)

    def help(self, query):
        command = query.lower()
        if command in self.commands:
            doc = re.sub(r"\s+", " ", self.commands[command].__doc__)
            return f"{self.bot.commandChar}{command} {doc}"

    def onLoad(self):
        self.messages = {}


stringUtils = StringUtils()
