from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

import re

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

    def onLoad(self):
        if 'triggers' not in self.bot.storage:
            self.bot.storage['triggers'] = {
                "example": {
                    "regex": ".*boop.*",        # if a message's text contains boop somewhere
                    "regexType": "text",        # other values, nick? TBD.
                    "command": "reload boop",   # run reload boop
                    "enabled": False            # allow disabling because oof ow
                }
            }

    def execute(self, message: IRCMessage):
        if message.command.lower() in self.triggers():
            pass
        else:
            for triggerName, triggerData in self.bot.storage['triggers']:
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

    @admin(msg="Only my admins may delete triggers!")
    def _delTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger del triggerName
        pass

    def _toggleTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger toggle triggerName
        pass

    def _listTriggerNames(self, message: IRCMessage) -> IRCResponse:
        # .trigger list (just names)
        pass

    def _showTrigger(self, message: IRCMessage) -> IRCResponse:
        # .trigger show triggerName (contents - regex and command)
        pass

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


trigger = Trigger()
