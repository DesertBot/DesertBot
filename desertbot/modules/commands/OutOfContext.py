import random
import time
from collections import OrderedDict
from typing import List, Union
from weakref import WeakKeyDictionary

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage, TargetTypes
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse
from desertbot.utils import string
from desertbot.utils.regex import re


@implementer(IPlugin, IModule)
class OutOfContext(BotCommand):
    messageLimit = 50

    def actions(self):
        return super(OutOfContext, self).actions() + [("message-channel", 1, self.storeMessage),
                                                      ("action-channel", 1, self.storeMessage)]

    def triggers(self):
        return ["outofcontext"]

    def _add(self, message: IRCMessage):
        """add - Adds a quote to the OutOfContext log. The quote will be pulled from a message line buffer."""
        if len(message.parameterList) < 2:
            return IRCResponse("Add what?", message.replyTo)
        if message.targetType == TargetTypes.USER:
            return IRCResponse("You can only add messages from channels.", message.replyTo)

        regex = re.compile(re.escape(" ".join(message.parameterList[1:])), re.IGNORECASE)
        if len(self.messageStore) == 0 or message.channel not in self.messageStore:
            return IRCResponse("Sorry, there are no messages in my buffer.", message.replyTo)

        matches = list(filter(regex.search, self.messageStore[message.channel]))
        if len(matches) == 0:
            return IRCResponse("Sorry, that didn't match anything in my message buffer.", message.replyTo)
        if len(matches) > 1:
            return IRCResponse("Sorry, that matches too many lines in my message buffer.", message.replyTo)

        todayDate = time.strftime("[%Y-%m-%d] [%H:%M]")
        quote = f"{todayDate} {matches[0]}"
        if message.replyTo not in self.storage:
            self.storage[message.replyTo] = []
        if len(self.storage[message.replyTo]) > 0 and self.storage[message.replyTo][-1] == quote:
            return IRCResponse("That quote has already been added to the log!", message.replyTo)
        else:
            self.storage[message.replyTo].append(quote)
            return IRCResponse(f"Quote '{quote}' was added to the log!", message.replyTo)

    def _remove(self, message: IRCMessage):
        """remove <regex> - remove a quote from the OutOfContext log."""
        if len(message.parameterList) < 2:
            return IRCResponse("Remove what?", message.replyTo)
        if len(self.storage) == 0 or message.replyTo not in self.storage:
            return IRCResponse("There are no quotes in the log.", message.replyTo)
        regex = re.compile(" ".join(message.parameterList[1:]), re.IGNORECASE)
        matches = list(filter(regex.search, self.storage[message.replyTo]))
        if len(matches) == 0:
            return IRCResponse("That message is not in the log.", message.replyTo)
        if len(matches) > 1:
            return IRCResponse(f"Unable to remove quote, {len(matches)} matches found.", message.replyTo)
        return self._removeQuote(message.replyTo, matches[0])

    def _removebyid(self, message: IRCMessage):
        """removebyid <quoteid> - remove the quote with the specified ID from the OutOfContext log."""
        if len(message.parameterList) < 2:
            return IRCResponse("Remove what?", message.replyTo)
        if not string.isNumber(message.parameterList[1]):
            return IRCResponse("You didn't specify a valid ID.", message.replyTo)
        if len(self.storage) == 0 or message.replyTo not in self.storage:
            return IRCResponse("There are no quotes in the log.", message.replyTo)
        index = int(message.parameterList[1]) - 1
        quotes = self.storage[message.replyTo]
        if index < len(quotes):
            return self._removeQuote(message.replyTo, quotes[index])
        return IRCResponse("That message is not in the log.", message.replyTo)

    def _list(self, message: IRCMessage):
        """list (<search/searchnick <regex>>) - post the OutOfContext log. A search regex can be provided to filter\
         the list."""
        params = [x for x in message.parameterList[1:]]
        if len(params) > 0:
            subsubcommand = params.pop(0).lower()
            if subsubcommand == "searchnick":
                return self._postList(message.replyTo, " ".join(params), True)
            elif subsubcommand == "search":
                return self._postList(message.replyTo, " ".join(params), False)
            else:
                return self._postList(message.replyTo, "", False)
        else:
            return self._postList(message.replyTo, "", False)

    def _search(self, message: IRCMessage):
        """search <regex> - look up quotes in the OutOfContext log. This search operation will look at \
        the content of the quotes."""
        if len(message.parameterList) < 2:
            return IRCResponse("Search what?", message.replyTo)
        return self._getQuote(message.replyTo, " ".join(message.parameterList[1:]), False, -1)

    def _searchnick(self, message: IRCMessage):
        """searchnick <regex> - look up quotes in the OutOfContext log. This search operation will \
        look at the nick that said the quoted line."""
        nick = message.user.nick
        if len(message.parameterList) > 1:
            nick = message.parameterList[1]
        return self._getQuote(message.replyTo, nick, True, -1)

    def _id(self, message: IRCMessage):
        """id <quoteid> - look up the quote that has the given ID."""
        if len(message.parameterList) < 2 or not string.isNumber(message.parameterList[1]):
            return IRCResponse("You didn't specify a valid ID.", message.replyTo)
        return self._getQuote(message.replyTo, "", False, int(message.parameterList[1]) - 1)

    def _random(self, message: IRCMessage):
        """random - return a random quote from the OutOfContext log."""
        return self._getQuote(message.replyTo, "", False, -1)

    def _removeQuote(self, source, quote):
        self.storage[source].remove(quote)
        return IRCResponse(f"Quote '{quote}' was removed from the log!", source)

    def _postList(self, source, searchString, searchNickname):
        if len(self.storage) == 0 or source not in self.storage:
            return IRCResponse("There are no quotes in the log.", source)
        regex = re.compile(searchString, re.IGNORECASE)
        matches = []
        if searchNickname:
            for x in self.storage[source]:
                if x[21] == "*":
                    match = re.search(regex, x[:x.find(" ", 23)])
                else:
                    match = re.search(regex, x[x.find("<") + 1:x.find(">")])
                if match:
                    matches.append(x)
        else:
            for x in self.storage[source]:
                if re.search(regex, x[x.find(">") + 1:]):
                    matches.append(x)
        if len(matches) == 0:
            return IRCResponse(f"No matches for '{searchString}' found.", source)

        pasteLink =  self.bot.moduleHandler.runActionUntilValue('upload-dbco',
                                                                string.stripFormatting("\n".join(matches)),
                                                                10 * 60)

        return IRCResponse(f"Link posted! (Expires in 10 minutes) {pasteLink}.", source)

    def _getQuote(self, source, searchString, searchNickname, index):
        if len(self.storage) == 0 or source not in self.storage:
            return IRCResponse("There are no quotes in the log.", source)
        regex = re.compile(searchString, re.IGNORECASE)
        matches = []
        if searchNickname:
            for x in self.storage[source]:
                if x[21] == "*":
                    match = re.search(regex, x[:x.find(" ", 23)])
                else:
                    match = re.search(regex, x[x.find("<") + 1:x.find(">")])
                if match:
                    matches.append(x)
        else:
            for x in self.storage[source]:
                if re.search(regex, x[x.find(">") + 1:]):
                    matches.append(x)
        if len(matches) == 0:
            return IRCResponse(f"No matches for '{searchString}' found.", source)
        if index < 0 or index > len(matches) - 1:
            index = random.randint(0, len(matches) - 1)
        return IRCResponse(f"Quote #{index + 1}/{len(matches)}: {matches[index]}", source)

    def _unrecognizedSubcommand(self, subCommand):
        return (f"unrecognized subcommand f'{subCommand}', "
                f"available subcommands for outofcontext are: {', '.join(self.subCommands.keys())}")

    def onLoad(self) -> None:
        self.messageStore = WeakKeyDictionary()
        self._helpText = ("{1}outofcontext ({0}) - adds, removes or requests things from the OutOfContext quote list. "
                          "Use '{1}help outofcontext <subcommand>' for subcommand help. "
                          .format('/'.join(self.subCommands), self.bot.commandChar))

    def help(self, query: Union[List[str], None]) -> str:
        if len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                return ('{1}outofcontext {0}' .format(re.sub(r"\s+", " ", self.subCommands[subCommand].__doc__),
                        self.bot.commandChar))
            else:
                return self._unrecognizedSubcommand(subCommand)
        else:
            return self._helpText

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            subCommand = message.parameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(self._unrecognizedSubcommand(subCommand), message.replyTo)
            return self.subCommands[subCommand](self, message)
        else:
            return IRCResponse(self._helpText, message.replyTo)

    def storeMessage(self, message: IRCMessage):
        if message.command or message.targetType == TargetTypes.USER:
            return

        if message.channel not in self.messageStore:
            self.messageStore[message.channel] = []

        if message.type == 'ACTION':
            self.messageStore[message.channel]\
                .append(f'* {message.user.nick} {string.stripFormatting(message.messageString)}')
        else:
            self.messageStore[message.channel]\
                .append(f'<{message.user.nick}> {string.stripFormatting(message.messageString)}')

        if len(self.messageStore[message.channel]) > self.messageLimit:
            self.messageStore[message.channel].pop(0)

    subCommands = OrderedDict([
         ('add', _add),
         ('remove', _remove),
         ('removebyid', _removebyid),
         ('list', _list),
         ('search', _search),
         ('searchnick', _searchnick),
         ('id', _id),
         ('random', _random)]
     )


outOfContext = OutOfContext()
