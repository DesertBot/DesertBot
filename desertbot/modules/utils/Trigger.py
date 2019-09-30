from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

from collections import OrderedDict
import re
from typing import List

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


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
        return "Doing trigger stuff."

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
                if triggerData['regexType'] == "text":
                    if re.match(triggerData['regex'], message.messageString, re.IGNORECASE):
                        return self._handleTriggerCommand(message, triggerData['command'])
                elif triggerData['regexType'] == "nick":
                    if re.match(triggerData['regex'], message.user.nick, re.IGNORECASE):
                        return self._handleTriggerCommand(message, triggerData['command'])

    @admin(msg="Only my admins may add new triggers!")
    def _addTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger add triggerName "regex" command
        # Some prefixes before the regex could specify what part of the message it looks at, eg n"regex" for nick. It would default to the text. (t)
        pass

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
        # .trigger del triggerName
        pass

    def _toggleTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger toggle triggerName
        triggerName = message.parameterList[1]
        if triggerName in self.bot.storage['triggers']:
            self.bot.storage['triggers'][triggerName]["enabled"] = not self.bot.storage['triggers'][triggerName]["enabled"]
            currentStatus = "enabled" if self.bot.storage['triggers'][triggerName]["enabled"] else "disabled"
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} is now {currentStatus}", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"No trigger named {triggerName} exists.", message.replyTo)

    def _listTriggerNames(self, message: IRCMessage) -> IRCResponse:
        # .trigger list (just names)
        return IRCResponse(ResponseType.Say, str(self.bot.storage['triggers'].keys()), message.replyTo)

    def _showTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger show triggerName (contents - regex and command)
        triggerName = message.parameterList[1]
        if triggerName in self.bot.storage['triggers']:
            triggerData = self.bot.storage['triggers'][triggerName]
            return IRCResponse(ResponseType.Say, f"Trigger {triggerName} - {triggerData['regexType']}\"{triggerData['regex']}\" - {triggerData['command']}", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"No trigger named {triggerName} exists.", message.replyTo)

    @admin(msg="Only my admins may export triggers!")
    def _exportTriggers(self, message: IRCMessage) -> IRCResponse:
        # .trigger export triggerName/all (export to paste, in .trigger add format)
        pass

    @admin(msg="Only my admins may import triggers!")
    def _importTriggers(self, message: IRCMessage) -> IRCResponse:
        # .trigger import <paste.ee address>
        pass

    def _handleTriggerCommand(self, message: IRCMessage, triggerCommand: str) -> IRCResponse:
        newMessage = IRCMessage(message.type, message.user, message.channel, triggerCommand, self.bot)
        newCommand = newMessage.command.lower()
        if newCommand in self.bot.moduleHandler.mappedTriggers:
            return self.bot.moduleHandler.mappedTriggers[newCommand].execute(newMessage)

    subCommands = OrderedDict([
        ('add', _addTrigger),
        ('del', _delTrigger),
        ('toggle', _toggleTrigger),
        ('list', _listTriggerNames),
        ('show', _showTrigger),
        ('export', _exportTriggers),
        ('import', _importTriggers)
    ])


trigger = Trigger()
