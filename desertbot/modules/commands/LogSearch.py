import os.path
from collections import OrderedDict
from os import walk
from time import strftime
from typing import Union

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse

try:
    import re2
except ImportError:
    import re as re2


@implementer(IPlugin, IModule)
class LogSearch(BotCommand):
    def triggers(self):
        return ['firstseen', 'lastseen', 'lastsaw', 'firstsaid', 'lastsaid', 'saidbeforetoday']

    def help(self, query: Union[str, None]) -> str:
        command = query[0].lower()
        if command in self._commands:
            return self._commands[command].__doc__
        else:
            return f"{', '.join(self._commands.keys())} - Search the logs by nickname or (part of) a message."

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 1:
            return IRCResponse('Search what?', message.replyTo)

        return IRCResponse(self._commands[message.command](self, message), message.replyTo)

    def _getLogs(self, message):
        basePath = self.bot.logPath
        logPath = os.path.join(basePath, self.bot.server, message.replyTo)
        logs = []
        for (dirpath, dirnames, filenames) in walk(logPath):
            logs.extend(filenames)
            break
        logs.sort()
        return logPath, logs

    def _firstseen(self, message: IRCMessage):
        """firstseen <nick> | Search for the first line someone with the given nick spoke."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, True, True, False)

    def _lastseen(self, message: IRCMessage):
        """lastseen <nick> | Search for the last line someone with the given nick spoke. Includes today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, True, True, True)

    def _lastsaw(self, message: IRCMessage):
        """lastsaw <nick> | Search for the last line someone with the given nick spoke. Does not include today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, True, False, True)

    def _firstsaid(self, message: IRCMessage):
        """firstsaid <messagepart> | Search for the first time a given thing was said."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, False, True, False)

    def _lastsaid(self, message: IRCMessage):
        """lastsaid <messagepart> | Search for the last time a given thing was said."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, False, True, True)

    def _saidbeforetoday(self, message: IRCMessage):
        """saidbeforetoday <messagepart> | Search for the last time a given thing was said, before today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs, False, False, True)

    def _search(self, searchTerms, logPath, files, searchForNick, includeToday, reverse):
        candidatePattern = re2.compile(searchTerms, re2.IGNORECASE)
        if searchForNick:
            fullPattern = re2.compile(fr"^\[[^]]+\]\s+<(.?{searchTerms})>\s+.*", re2.IGNORECASE)
        else:
            fullPattern = re2.compile(fr'.*<.*> .*({searchTerms}).*', re2.IGNORECASE)
        found = None

        today = f"{strftime('%Y-%m-%d')}.log"
        if today in files and not includeToday:
            files.remove(today)

        if reverse:
            files.reverse()
        for filename in files:
            with open(os.path.join(logPath, filename), 'r', errors='ignore') as logfile:
                contents = logfile.read()
            # We do an initial check to see if our searchTerms show up anywhere in the file.
            # If they don't, we know the file contains no matches and move on.
            # If they do, we move on to the more expensive line search.
            if not candidatePattern.search(contents):
                continue
            lines = contents.rstrip().split('\n') # remove trailing newline or we end up with a blank line in the list
            if reverse:
                lines = reversed(lines)
            if reverse and includeToday and filename == today:
                lines = list(lines)[1:]
            for line in lines:
                if fullPattern.match(line.rstrip()):
                    found = line.rstrip()
                    break
            if found:
                return f'[{filename[:10]}] {found}'
        return 'Nothing that matches your search terms has been found in the log.'

    _commands = OrderedDict([
        ('firstseen', _firstseen),
        ('lastseen', _lastseen),
        ('lastsaw', _lastsaw),
        ('firstsaid', _firstsaid),
        ('lastsaid', _lastsaid),
        ('saidbeforetoday', _saidbeforetoday)
    ])


logsearch = LogSearch()
