import datetime
import random
import re

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.utils import string
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Lists(BotCommand):
    def triggers(self):
        return ["list"]

    def help(self, query):
        """
        List module basic command syntax:
        .list <list_name> [subcommand] [params]

        Valid subcommands:
        <None> - get random entry from list
        <Integer> - get specific entry from list
        add - add new entry           (entry text as params)
        last - get last entry
        list - list entries           (optional regex as params)
        search - search for entry     (regex as params, last param optional match ID integer)
        remove - remove an entry      (regex as params, only remove if matches only single entry)
        removebyid - remove an entry  (ID as param)
        """
        prefix = "{}list <list_name>".format(self.bot.commandChar)
        helpDict = {
            "<nothing>": "returns a random entry from the named list",
            "<number>": "returns a specific entry from the named list",
            "add": "add <list entry> - adds the given text to the named list",
            "last": "last - returns the last entry from the named list",
            "list": "list <regex search>"
                    " - uploads the named list to paste.ee and gives you a link."
                    " If a regex search is given, only matching entries are uploaded",
            "search": "search <regex> <number>"
                      " - regex search entries, returning a random matching one."
                      " If a number is given, return the nth matching entry",
            "remove": "remove <regex> - remove the matching entry, only if there is only one match",
            "removebyid": "removebyid <id> - remove an entry by id"
        }
        if len(query) == 1:
            return ("{} <nothing>/<number>/add/list/search/remove/removebyid - manages named lists."
                    " Use {}help list <subcommand> for help with the subcommands"
                    .format(prefix, self.bot.commandChar))
        else:
            if query[1].lower() in helpDict:
                return "{} {}".format(prefix, helpDict[query[1].lower()])
            else:
                return ("{!r} is not a valid subcommand, use {}help list for a list of subcommands"
                        .format(query[1], self.bot.commandChar))

    def onLoad(self):
        if "lists" not in self.bot.storage:
            self.bot.storage["lists"] = {}
        self.lists = self.bot.storage["lists"]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say, self.help(["lists"]), message.replyTo)
        elif len(message.parameterList) == 1:
            if message.parameterList[0].lower() in self.lists:
                return IRCResponse(ResponseType.Say,
                                   self._getRandomEntry(message.parameterList[0].lower()),
                                   message.replyTo)
            else:
                return IRCResponse(ResponseType.Say,
                                   "I don't have a list named {!r}"
                                   .format(message.parameterList[0]),
                                   message.replyTo)
        elif len(message.parameterList) >= 2:
            listName = message.parameterList[0].lower()
            subcommand = message.parameterList[1].lower()
            paramsList = [param for param in message.parameterList[2:]]

            if subcommand == "add":
                text = self._addEntry(listName, " ".join(paramsList))
            elif listName not in self.lists:
                text = ("I don't have a list named {!r}, maybe add some entries to it to create it?"
                        .format(listName))
            elif subcommand == "last":
                text = self._getLastEntry(listName)
            elif subcommand == "list":
                text = self._getMultipleEntries(listName, " ".join(paramsList))
            elif subcommand == "search":
                try:
                    desiredNumber = int(paramsList[-1])
                    paramsList.pop(-1)
                except ValueError:
                    desiredNumber = None
                text = self._search(listName, " ".join(paramsList), desiredNumber)
            elif subcommand == "remove":
                if len(paramsList) == 0:
                    text = "You didn't give me anything to match against!"
                else:
                    text = self._removeEntry(listName, " ".join(paramsList))
            elif subcommand == "removebyid":
                if len(paramsList) != 1:
                    text = "Please give me one and ONLY one ID to remove."
                else:
                    text = self._removeEntryByID(listName, int(paramsList[0]))
            else:
                try:
                    desiredNumber = int(subcommand)
                    text = self._getEntryByID(listName, desiredNumber)
                except ValueError:
                    text = self.help(["lists"])

            return IRCResponse(ResponseType.Say, text, message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, self.help(["lists"]), message.replyTo)

    def _getRandomEntry(self, listName):
        """
        Get a random entry from the list with the given name
        """
        chosen = random.choice(self.lists[listName])
        return "Entry #{} - {} - {}".format(chosen["id"], chosen["timestamp"], chosen["text"])

    def _getEntryByID(self, listName, number):
        """
        Get a specific entry from the list with the given name.
        If that number entry doesn't exist in the given list, return an error.
        """
        try:
            choice = int(number)
        except ValueError:
            return "I don't know what you mean by {!r}".format(number)

        chosen = None
        for entry in self.lists[listName]:
            if entry["id"] == choice:
                chosen = entry

        if chosen is None:
            return "There is no entry with the id {} in the {!r} list!".format(number, listName)
        return "Entry #{} - {} - {}".format(chosen["id"], chosen["timestamp"], chosen["text"])

    def _getLastEntry(self, listName):
        """
        Return the last entry from the given list
        """
        chosen = self.lists[listName][-1]
        return "Entry #{} - {} - {}".format(chosen["id"], chosen["timestamp"], chosen["text"])

    def _getMultipleEntries(self, listName, regexPattern=None):
        """
        Get multiple entries from the list with the given name as a paste.ee link
        If regexPattern is None, just use the whole list,
        otherwise make a list of all entries matching the regexPattern.
        """
        if len(self.lists[listName]) == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        # If given a regexPattern, remove all the entries that don't match it
        if regexPattern is not None:
            for entry in entries:
                match = re.search(regexPattern, entry["text"])
                if not match:
                    entries.remove(entry)

        if len(entries) == 0:
            return "That list doesn't contain anything matching {!r}!".format(regexPattern)

        # Paste entries found into pastebin service
        pasteString = ""
        for entry in entries:
            pasteString += "Entry #{} - {} - {}".format(entry["id"],
                                                        entry["timestamp"],
                                                        entry["text"])
            pasteString += "\n"

        mh = self.bot.moduleHandler
        pasteLink = mh.runActionUntilValue('upload-dbco',
                                           string.stripFormatting(pasteString),
                                           10*60)

        return "Link posted! (Expires in 10 minutes) {}".format(pasteLink)

    def _getNextAvailableID(self, listName):
        """
        Get the next available ID for the given list
        """
        if len(self.lists[listName]) == 0:
            # List is empty, return 1. New entry will be first entry.
            return 1
        else:
            # Get the ID for the last entry in the list and give the new ID as 1 larger than that
            lastEntry = self.lists[listName][-1]
            return int(lastEntry["id"]) + 1

    def _addEntry(self, listName, entryText):
        """
        Add a new entry to the given list with the given text.
        If there is no list with the given name, create it first.
        """
        if listName not in self.lists:
            self.lists[listName] = []
        entryObject = {
            "id": self._getNextAvailableID(listName),
            "timestamp": datetime.datetime.utcnow().strftime("[%Y-%m-%d] [%H:%M]"),
            "text": entryText
        }
        self.lists[listName].append(entryObject)
        self.bot.storage["lists"] = self.lists
        return ("Entry #{} - {} - {} added to list {}".format(entryObject["id"],
                                                              entryObject["timestamp"],
                                                              entryObject["text"], listName))

    def _search(self, listName, regexPattern, desiredNumber=None):
        """
        Search the list with the given name using the given regex pattern.
        If desiredNumber is not none, try to return a specific match
        from the list of entries matching the regex.
        """
        if len(self.lists[listName]) == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        for entry in entries:
            match = re.search(regexPattern, entry["text"])
            if not match:
                entries.remove(entry)

        if len(entries) == 0:
            return "That list doesn't contain anything matching {!r}!".format(regexPattern)

        if desiredNumber is not None:
            if desiredNumber >= len(entries):
                chosen = entries[-1]
            else:
                chosen = entries[desiredNumber + 1]
            return "Match #{}/{} - {} - {}".format(entries.index(chosen) + 1, len(entries),
                                                   chosen["timestamp"], chosen["text"])
        else:
            chosen = random.choice(entries)
            return "Match #{}/{} - {} - {}".format(entries.index(chosen) + 1, len(entries),
                                                   chosen["timestamp"], chosen["text"])

    def _removeEntry(self, listName, regexPattern):
        """
        Try to remove an entry from the list of the given name using the given regexPattern.
        Only removes an entry if there is only one entry matching the given regexPattern.
        """
        if len(self.lists[listName]) == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        for entry in entries:
            match = re.search(regexPattern, entry["text"])
            if not match:
                entries.remove(entry)

        if len(entries) == 0:
            return "That list doesn't contain anything matching {!r}!".format(regexPattern)

        elif len(entries) > 1:
            return ("There are too many entries matching {!r} in that list,"
                    " please be more specific."
                    .format(regexPattern))

        else:
            entryCopy = entries[0].copy()
            self.lists[listName].remove(entries[0])
            self.bot.storage["lists"] = self.lists
            return ("Entry #{} - {} from list {} was removed"
                    .format(entryCopy["id"], entryCopy["text"], listName))

    def _removeEntryByID(self, listName, idNumber):
        """
        Remove an entry by its ID from the list with the given name.
        """
        if len(self.lists[listName]) == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        for entry in entries:
            if entry["id"] == idNumber:
                entryCopy = entry.copy()
                self.lists[listName].remove(entry)
                self.bot.storage["lists"] = self.lists
                return ("Entry #{} - {} from list {} was removed"
                        .format(entryCopy["id"], entryCopy["text"], listName))
        return "Could not find an entry with ID {} in list {}".format(idNumber, listName)


lists = Lists()
