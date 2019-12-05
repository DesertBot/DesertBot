from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule, ignore
from desertbot.modules.commandinterface import admin
from zope.interface import implementer

import datetime
import random
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Boops(BotModule):
    
    def triggers(self):
        return ['boop']

    def onLoad(self) -> None:
        self.lastTriggered = datetime.datetime.min
        # TODO edit cooldown at runtime?
        self.cooldown = 300

    def actions(self):
        return super(Boops, self).actions() + [('message-channel', 1, self.respond),
                                               ('message-user', 1, self.respond),
                                               ('action-channel', 1, self.respond),
                                               ('action-user', 1, self.respond)]

    def help(self, arg: list) -> str:
        return f"Responds to boops. Admins may use {self.bot.commandChar}boop add/remove <url> to add and remove boops."

    @ignore
    def respond(self, message: IRCMessage) -> IRCResponse:
        # TODO store boops in self.storage as a dict of boopName to boopUrl, for easier identification in add/remove
        if message.command == "boop":
            subcommand = message.parameterList[0]
            if subcommand == "add":
                return self._addBoop(message)
            elif subcommand == "remove":
                return self._removeBoop(message)
            else:
                return IRCResponse(ResponseType.Say, self.help(message.parameterList), message.replyTo)
        else:
            match = re.search('(^|[^\w])b[o0]{2,}ps?([^\w]|$)', message.messageString, re.IGNORECASE)
            if match and (datetime.datetime.utcnow() - self.lastTriggered).seconds >= self.cooldown:
                self.lastTriggered = datetime.datetime.utcnow()
                return IRCResponse(ResponseType.Say, f"Boop! {random.choice(self.storage['boops'])}", message.replyTo)

    @admin("Only my admins may add boops!")
    def _addBoop(self, message: IRCMessage) -> IRCResponse:
        self.storage['boops'].append(message.parameterList[1])
        return IRCResponse(ResponseType.Say, f"Added {message.parameterList[1]} to the list of boops!", message.replyTo)

    @admin("Only my admins may remove boops!")
    def _removeBoop(self, message: IRCMessage) -> IRCResponse:
        if message.parameterList[1] in self.storage['boops']:
            self.storage['boops'].remove(message.parameterList[1])
            return IRCResponse(ResponseType.Say, f"Removed {message.parameterList[1]} from the list of boops!", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, f"Couldn't find {message.parameterList[1]} in the list of boops, did you maybe do a typo?", message.replyTo)


boop = Boops()
