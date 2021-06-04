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
from desertbot.utils import string

try:
    import re2
except ImportError:
    import re as re2


@implementer(IPlugin, IModule)
class LogSearch(BotCommand):
    def triggers(self):
        return [
            'firstseen', 'lastseen', 'lastsaw',
            'allseen', 'allsaw',
            'firstsaid', 'lastsaid', 'saidbeforetoday',
            'allsaid', 'allsaidbeforetoday'
        ]

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
        return self._search(message.parameters, logPath, logs,
                            searchForNick=True,
                            includeToday=True,
                            reverse=False)

    def _lastseen(self, message: IRCMessage):
        """lastseen <nick> | Search for the last line someone with the given nick spoke. Includes today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=True,
                            includeToday=True,
                            reverse=True)

    def _lastsaw(self, message: IRCMessage):
        """lastsaw <nick> | Search for the last line someone with the given nick spoke. Does not include today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=True,
                            includeToday=False,
                            reverse=True)

    def _allseen(self, message: IRCMessage):
        """allseen <nick> | Search the logs for all lines said by someone with the given nick. Includes today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=True,
                            includeToday=True,
                            reverse=False,
                            getAll=True)

    def _allsaw(self, message: IRCMessage):
        """allsaw <nick> | Search the logs for all lines said by someone with the given nick. Does not include today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=True,
                            includeToday=False,
                            reverse=False,
                            getAll=True)

    def _firstsaid(self, message: IRCMessage):
        """firstsaid <messagepart> | Search for the first time a given thing was said."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=False,
                            includeToday=True,
                            reverse=False)

    def _lastsaid(self, message: IRCMessage):
        """lastsaid <messagepart> | Search for the last time a given thing was said."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=False,
                            includeToday=True,
                            reverse=True)

    def _saidbeforetoday(self, message: IRCMessage):
        """saidbeforetoday <messagepart> | Search for the last time a given thing was said, before today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=False,
                            includeToday=False,
                            reverse=True)

    def _allsaid(self, message: IRCMessage):
        """allsaid <messagepart> | Search the logs for all lines matching a given thing. Includes today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=False,
                            includeToday=True,
                            reverse=False,
                            getAll=True)

    def _allsaidbeforetoday(self, message: IRCMessage):
        """allsaidbeforetoday <messagepart> | Search the logs for all lines matching a given thing. Does not include today."""
        logPath, logs = self._getLogs(message)
        return self._search(message.parameters, logPath, logs,
                            searchForNick=False,
                            includeToday=False,
                            reverse=False,
                            getAll=True)

    def _search(self, searchTerms, logPath, files, searchForNick, includeToday, reverse, getAll: bool = False):
        candidatePattern = re2.compile(searchTerms, re2.IGNORECASE)
        if searchForNick:
            fullPattern = re2.compile(fr"^\[[^]]+\]\s+<(.?{searchTerms})>\s+.*", re2.IGNORECASE)
        else:
            fullPattern = re2.compile(fr'.*<.*> .*({searchTerms}).*', re2.IGNORECASE)
        if not getAll:
            found = None
        else:
            found = []

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
            lines = contents.rstrip().split('\n')  # remove trailing newline or we end up with a blank line in the list
            if reverse:
                lines = reversed(lines)
            if reverse and includeToday and filename == today:
                lines = list(lines)[1:]
            for line in lines:
                if fullPattern.match(line.rstrip()):
                    if not getAll:
                        # if we're searching for a single result, just return it and break
                        found = f'[{filename[:10]}] {line.rstrip()}'
                        break
                    else:
                        # if we're searching for all results, add formatted line to results and continue to next line
                        found.append(f'[{filename[:10]}] {line.rstrip()}')
                        continue
            if not getAll and found:
                # if this is not a getAll, we return what we found
                return found
            else:
                # otherwise, continue to the next file
                continue
        # we should only reach this stage if this is a getAll, or if it's not a getAll and we found nothing
        if getAll and len(found) > 0:
            pasteLink = self.bot.moduleHandler.runActionUntilValue('upload-dbco',
                                                                   string.stripFormatting("\n".join(found)),
                                                                   10 * 60)
            return f"Link posted! (Expires in 10 minutes) {pasteLink}."
        else:
            return 'Nothing that matches your search terms has been found in the log.'

    _commands = OrderedDict([
        ('firstseen', _firstseen),
        ('lastseen', _lastseen),
        ('lastsaw', _lastsaw),
        ('allseen', _allseen),
        ('allsaw', _allsaw),
        ('firstsaid', _firstsaid),
        ('lastsaid', _lastsaid),
        ('saidbeforetoday', _saidbeforetoday),
        ('allsaid', _allsaid),
        ('allsaidbeforetoday', _allsaidbeforetoday)
    ])


logsearch = LogSearch()
