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
        return IRCResponse(json.dumps(message.parameters), message.replyTo)

    def _fromjson(self, message: IRCMessage):
        """un-escapes json strings"""
        return IRCResponse(str(json.loads(message.parameters)), message.replyTo)

    commands = OrderedDict([
        ('tojson', _tojson),
        ('fromjson', _fromjson),
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


stringUtils = StringUtils()
