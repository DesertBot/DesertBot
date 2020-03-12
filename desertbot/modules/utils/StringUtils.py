from twisted.plugin import IPlugin
from zope.interface import implementer
from collections import OrderedDict
import json
import re
from typing import List

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType

from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as ndld


@implementer(IPlugin, IModule)
class StringUtils(BotCommand):
    def triggers(self):
        return ["tojson", "fromjson"]

    def actions(self):
        return super(StringUtils, self).actions() + [('closest-matches', 1, self.closestMatches)]

    def closestMatches(self, search: str, wordList: List[str],
                       numMatches: int, threshold: float) -> List[str]:
        similarities = sorted([(ndld(search, word), word) for word in wordList])
        closeMatches = [word for (diff, word) in similarities if diff <= threshold]
        topN = closeMatches[:numMatches]
        return topN

    def _tojson(self, message: IRCMessage):
        """converts input string to json-escaped string"""
        return IRCResponse(ResponseType.Say,
                           json.dumps(message.messageString),
                           message.replyTo)

    def _fromjson(self, message: IRCMessage):
        """un-escapes json strings"""
        return IRCResponse(ResponseType.Say,
                           str(json.loads(message.messageString)),
                           message.replyTo)

    commands = OrderedDict([
        ('tojson', _tojson),
        ('fromjson', _fromjson),
    ])

    def execute(self, message: IRCMessage):
        if message.command.lower() in self.commands():
            return self.commands[message.command.lower()](message)
        else:
            return IRCResponse(ResponseType.Say,
                               f"{message.command} is not a recognized StringUtils command",
                               message.replyTo)

    def help(self, query):
        command = query.lower()
        if command in self.commands():
            doc = re.sub(r"\s+", " ", self.commands[command].__doc__)
            return f"{self.bot.commandChar}{command} {doc}"


stringUtils = StringUtils()
