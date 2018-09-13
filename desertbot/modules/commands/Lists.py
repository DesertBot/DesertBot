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
        add - add new entry         (entry text as params)
        list - list entries         (optional regex as params)
        search - search for entry   (regex as params, last in params list optionally match ID integer)
        """
        return "TBD"

    def onLoad(self):
        if "lists" not in self.bot.storage:
            self.bot.storage["lists"] = {}
        self.lists= self.bot.storage["lists"]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say, self.help(""), message.replyTo)
        elif len(message.parameterList) == 1 and message.parameterList[0].lower in self.lists:
            return IRCResponse(ResponseType.Say,
                               self._get_random_entry(message.parameterList[0].lower()),
                               message.replyTo)
        elif len(message.parameterList) >= 2:
            listName = message.parameterList[0].lower()
            subcommand = message.parameterList[1].lower()
            paramsList = [param for param in message.parameterList[2:]]

            if subcommand == "add":
                self._add_entry(listName, " ".join(paramsList))
            elif subcommand == "list":
                return self._get_multiple_entries(listName, " ".join(paramsList))
            elif subcommand == "search":
                try:
                    desiredNumber = int(paramsList[-1])
                    paramsList.pop(-1)
                except Exception:
                    desiredNumber = None
                return self._search(listName, " ".join(paramsList), desiredNumber)
            else:
                return IRCResponse(ResponseType.Say, self.help(""), message.replyTo)

    def _get_random_entry(self, listName):
        listLength = len(self.lists[listName])
        chosen = random.choice(self.lists[listName])
        return "Entry #{}/{} - {} - {}".format(chosen["id"], listLength, chosen["timestamp"], chosen["text"])

    def _get_numbered_entry(self, listName, number):
        listLength = len(self.lists[listName])
        try:
            choice = int(number)
        except Exception:
            return "I don't know what you mean by {!r}".format(number)

        if choice >= listLength:
            chosen = self.lists[listName][-1]
        else:
            chosen = self.lists[listName][choice + 1]
        return "Entry #{}/{} - {} - {}".format(chosen["id"], listLength, chosen["timestamp"], chosen["text"])

    def _get_multiple_entries(self, listName, regexPattern=None):
        listLength = len(self.lists[listName])
        if listLength == 0:
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

        # Paste entries found into paste.EE
        pasteString = ""
        for entry in entries:
            pasteString += "Entry #{} - {} - {}".format(entry["id"],  entry["timestamp"], entry["text"])
            pasteString += "\n"

        pasteEElink = self.bot.moduleHandler.runActionUntilValue('upload-pasteee',
                                                                 string.stripFormatting(pasteString),
                                                                 listName,
                                                                 10)

        return "Link posted! (Expires in 10 minutes) {}".format(pasteEElink)

    def _add_entry(self, listName, entryText):
        if listName not in self.lists:
            self.lists[listName] = []
        entryObject = {
            "id": len(self.lists[listName]) + 1,
            "timestamp": datetime.datetime.utcnow().strftime("[%Y-%m-%d] [%H:%M"),
            "text": entryText
        }
        self.lists[listName].append(entryObject)
        self.bot.storage["lists"] = self.lists

    def _search(self, listName, regexPattern, desiredNumber=None):
        listLength = len(self.lists[listName])
        if listLength == 0:
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
            return "Match #{}/{} - {} - {}".format(entries.index(chosen), len(entries), chosen["timestamp"], chosen["text"])
        else:
            chosen = random.choice(entries)
            return "Match #{}/{} - {} - {}".format(entries.index(chosen), len(entries), chosen["timestamp"], chosen["text"])

    def _remove_entry(self, listName, regexPattern):
        listLength = len(self.lists[listName])
        if listLength == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        for entry in entries:
            match = re.search(regexPattern, entry["text"])
            if not match:
                entries.remove(entry)

        if len(entries) == 0:
            return "That list doesn't contain anything matching {!r}!".format(regexPattern)

        elif len(entries) > 1:
            return "There are too many entries matching {!r} in that list, please be more specific.".format(regexPattern)

        else:
            entryCopy = entries[0].copy()
            self.lists[listName].remove(entries[0])
            self.bot.storage["lists"] = self.lists
            return "Entry #{} - {} from list {} was removed".format(entryCopy["id"], entryCopy["text"], listName)

    def _remove_entry_by_id(self, listName, idNumber):
        listLength = len(self.lists[listName])
        if listLength == 0:
            return "That list is empty!"
        entries = [entry for entry in self.lists[listName]]

        for entry in entries:
            if entry["id"] == idNumber:
                entryCopy = entry.copy()
                self.lists[listName].remove(entry)
                self.bot.storage["lists"] = self.lists
                return "Entry #{} - {} from list {} was removed".format(entryCopy["id"], entryCopy["text"], listName)
            else:
                return "Could not find an entry with ID {} in list {}".format(idNumber, listName)


lists = Lists()
