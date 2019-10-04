from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from desertbot.response import IRCResponse, ResponseType
from zope.interface import implementer

from bs4 import UnicodeDammit
from collections import OrderedDict
import re
from typing import List


@implementer(IPlugin, IModule)
class Trigger(BotCommand):

    def triggers(self):
        return ['trigger']

    def actions(self):
        return super(Trigger, self).actions() + [('message-channel', 1, self.execute),
                                                 ('message-user', 1, self.execute),
                                                 ('action-channel', 1, self.execute),
                                                 ('action-user', 1, self.execute)]

    def help(self, parameters: List):
        command = parameters[0].lower()
        if command in self.triggers():
            # actual command that's been executed is !help trigger <whatever>
            subCommand = paramaters[1].lower()
            if subCommand in self.subCommands:
                subCommandHelp = self.subCommands[subCommand].__doc__
                return f"{self.bot.commandChar}trigger {subCommandHelp}"
            else:
                return f"Valid subcommands for {self.bot.commandChar}trigger: {', '.join(self.subCommands.keys())}"
        else:
            # actual command that's been executed is !trigger <invalid subcommand>
            return f"Valid subcommands for {self.bot.commandChar}trigger: {', '.join(self.subCommands.keys())}"

    def onLoad(self):
        if 'triggers' not in self.bot.storage:
            self.bot.storage['triggers'] = {
                "example": {
                    "regex": ".*reboop.*",      # if a message's text contains reboop somewhere
                    "regexType": "text",        # other possible values, nick? TBD.
                    "command": "reload boop",   # run reload boop
                    "enabled": False            # allow disabling because oof ow
                }
            }

    def execute(self, message: IRCMessage):
        if message.command.lower() in self.triggers():
            if len(message.parameterList) < 1 or message.parameterList[0].lower() not in self.subcommands:
                return IRCResponse(ResponseType.Say, self.help(message.parameterList), message.replyTo)
            else:
                subCommand = message.parameterList[0].lower()
                return self.subCommands[subCommand](self, message)
        else:
            for triggerName, triggerData in self.bot.storage['triggers'].items():
                if not triggerData['enabled']:
                    continue
                # TODO support for more regexTypes
                if triggerData['regexType'] == "text":
                    if re.match(triggerData['regex'], message.messageString, re.IGNORECASE):
                        return self._handleTriggerCommand(message, triggerData['command'])
                elif triggerData['regexType'] == "nick":
                    if re.match(triggerData['regex'], message.user.nick, re.IGNORECASE):
                        return self._handleTriggerCommand(message, triggerData['command'])

    @admin(msg="Only my admins may add new triggers!")
    def _addTrigger(self, message: IRCMessage) -> IRCResponse:
        """
        add <triggerName> <regexTypePrefix>"<regex>" <command> - add a new trigger
        valid regexTypePrefixes are t for text, n for nick - specifies what the regex should match against
        """
        if len(message.parameterList) < 3:
            return IRCResponse(ResponseType.Say, self.help(message.parameterList), message.replyTo)
        else:
            triggerName = message.parameterList[1]
            regex = message.parameterList[2]
            if regex[0] == '"':
                regex = f"t{regex}"  # pre-pend default "text" regexType if not explicitly given
            command = " ".join(message.parameterList[3:])
            regexType = self._regexTypePrefixToTypeName(regex[0])
            regex = regex[2:-1]  # strip out leading regextype and quotemarks surrounding regex
            self._actuallyAddTrigger(triggerName, regex, regexType, command, True)
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} added and now enabled.", message.replyTo)

    def _actuallyAddTrigger(self, triggerName: str, regex: str, regexType: str, command: str, enabled: bool):
        # used by _addTrigger and _importTriggers
        self.bot.storage[triggerName] = {
            "regex": regex,
            "regexType": regexType,
            "command": command,
            "enabled": enabled
        }

    @admin(msg="Only my admins may delete triggers!")
    def _delTrigger(self, message: IRCMessage) -> IRCResponse:
        """
        del <triggerName> - delete the specified trigger
        """
        triggerName = message.parameterList[1]
        if triggerName in self.bot.storage['triggers']:
            del self.bot.storage['triggers'][triggerName]
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} deleted!", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"No trigger named {triggerName} exists.", message.replyTo)

    def _toggleTrigger(self, message: IRCMessage) -> IRCResponse:
        """
        toggle <triggerName> - turn specified trigger on or off
        """
        triggerName = message.parameterList[1]
        if triggerName in self.bot.storage['triggers']:
            self.bot.storage['triggers'][triggerName]["enabled"] = not self.bot.storage['triggers'][triggerName]["enabled"]
            currentStatus = "enabled" if self.bot.storage['triggers'][triggerName]["enabled"] else "disabled"
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} is now {currentStatus}", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"No trigger named {triggerName} exists.", message.replyTo)

    def _listTriggerNames(self, message: IRCMessage) -> List[IRCResponse]:
        """
        list - list names of all triggers, and their current status
        """
        enableds = [triggerName for triggerName in self.bot.storage['triggers'] if self.bot.storage['triggers'][triggerName]['enabled']]
        disableds = [triggerName for triggerName in self.bot.storage['triggers'] if not self.bot.storage['triggers'][triggerName]['enabled']]

        return [
            IRCResponse(ResponseType.Say, f"Enabled triggers: {', '.join(enableds)}", message.replyTo),
            IRCResponse(ResponseType.Say, f"Disabled triggers: {', '.join(disableds)}", message.replyTo)
        ]

    def _showTrigger(self, message: IRCMessage) -> IRCResponse:
        """
        show <triggerName> - show contents of trigger, type-prefixed regex and command
        """
        triggerName = message.parameterList[1]
        if triggerName in self.bot.storage['triggers']:
            triggerData = self.bot.storage['triggers'][triggerName]
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} - {triggerData['regexType']}\"{triggerData['regex']}\" - {triggerData['command']}", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"No trigger named {triggerName} exists.", message.replyTo)

    @admin(msg="Only my admins may export triggers!")
    def _exportTriggers(self, message: IRCMessage) -> IRCResponse:
        """
        export [<trigger name(s)] - exports all triggers - or the specified triggers - to paste.ee, and returns a link
        """
        if len(message.parameterList) > 1:
            # filter the trigger dictionary by the listed triggers
            params = [trigger.lower() for trigger in message.parameterList[1:]]
            triggers = {trigger: self.bot.storage['triggers'][trigger] for trigger in params if trigger in self.bot.storage['triggers']}
        else:
            triggers = self.bot.storage['triggers']

        if len(triggers) == 0:
            return IRCResponse(ResponseType.Say, "There are no triggers to export!", message.replyTo)

        addCommands = []
        for triggerName, triggerData in triggers.items():
            regexTypePrefix = self._regexTypeNameToTypePrefix(triggerName["regexType"])
            cmd = f"{self.bot.commandChar}trigger add {triggerName} {regexTypePrefix}\"{triggerData['regex']}\" {triggerData['command']}"
            addCommands.append(cmd)

        exportText = "\n".join(sorted(addCommands))
        mh = self.bot.moduleHandler
        url = mh.runActionUntilValue('upload-pasteee', exportText,
                                     f"Exported {self.bot.nick} triggers for {self.bot.server}",
                                     60)

        return IRCResponse(ResponseType.Say,
                           f"Exported {len(addCommands)} triggers to {url}",
                           message.replyTo)

    @admin(msg="Only my admins may import triggers!")
    def _importTriggers(self, message: IRCMessage) -> IRCResponse:
        """
        import <url> [<trigger(s)>] - import all triggers from the specified URLs, or only the listed triggers
        """
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say, "You didn't give a url to import from!", message.replyTo)

        if len(message.parameterList) > 2:
            onlyListed = True
            importList = message.parameterList[2:]
        else:
            onlyListed = False
            importList = None

        url = message.parameterList[1]
        try:
            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
        except ValueError:
            return IRCResponse(ResponseType.Say, f"'{url}' is not a valid URL", message.replyTo)
        if not response:
            return IRCResponse(ResponseType.Say, f"Failed to open page at {url}", message.replyTo)

        text = response.content
        text = UnicodeDammit(text).unicode_markup
        lines = text.splitlines()
        numTriggers = 0
        for lineNumber, line in enumerate(lines):
            # Skip over blank lines
            if line == "":
                continue
            splitLine = line.split()
            if splitLine[0].lower() != "{}trigger".format(self.bot.commandChar):
                notAlias = f"Line {lineNumber} at {url} does not begin with {self.bot.commandChar}trigger"
                return IRCResponse(ResponseType.Say, notAlias, message.replyTo)
            subCommand = splitLine[1].lower()
            if subCommand != "add":
                return IRCResponse(ResponseType.Say, f"Line {lineNumber} at {url} is not an add command", message.replyTo)

            triggerName = splitLine[2]
            triggerRegexTypePrefix = splitLine[3][0]
            triggerRegexType = self._regexTypePrefixToTypeName(triggerRegexTypePrefix)
            triggerRegex = splitLine[3][2:-1]
            triggerCommand = " ".join(splitLine[4:])

            # Skip over triggers that weren't listed, if any were listed
            if onlyListed and triggerName not in importList:
                continue

            self._actuallyAddTrigger(triggerName=triggerName, regex=triggerRegex, regexType=triggerRegexType, command=triggerCommand, enabled=True)
            numTriggers += 1

        importMessage = f"Imported {numTriggers} trigger(s) from {url}"
        return IRCResponse(ResponseType.Say, importMessage, message.replyTo)

    def _handleTriggerCommand(self, message: IRCMessage, triggerCommand: str) -> IRCResponse:
        newMessage = IRCMessage(message.type, message.user, message.channel, triggerCommand, self.bot)
        newCommand = newMessage.command.lower()
        if newCommand in self.bot.moduleHandler.mappedTriggers:
            return self.bot.moduleHandler.mappedTriggers[newCommand].execute(newMessage)

    def _regexTypePrefixToTypeName(self, typePrefix: str) -> str:
        return self.regexTypes.get(typePrefix, "text")

    def _regexTypeNameToTypePrefix(self, typeName: str) -> str:
        for prefix, name in self.regexTypes:
            if name == typeName:
                return prefix
        return "t"

    subCommands = OrderedDict([
        ('add', _addTrigger),
        ('del', _delTrigger),
        ('toggle', _toggleTrigger),
        ('list', _listTriggerNames),
        ('show', _showTrigger),
        ('export', _exportTriggers),
        ('import', _importTriggers)
    ])

    # TODO support for more regex types
    regexTypes = {
        "t": "text",
        "n": "nick"
    }


trigger = Trigger()
