from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

import random
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Animals(BotModule):
    def actions(self):
        return super(Animals, self).actions() + [('message-channel', 1, self.respond),
                                                 ('message-user', 1, self.respond),
                                                 ('action-channel', 1, self.respond),
                                                 ('action-user', 1, self.respond)]

    def help(self, arg):
        return 'Responds to animal noises.'

    def onLoad(self) -> None:
        defaultReactions = {
            1: "{user} critically fails at being {article} {animal}.",
            8: "{user} is not {article} {animal}.",
            14: "{user} /might/ be {article} {animal}.",
            19: "{user} is DEFINITELY {article} {animal}.",
            20: "{user} is {article} CRITICAL {animal}!"
        }
        self.animalResponses = self.bot.storage["animals"]
        self.animalReactions = dict(self.bot.storage["animalCustomReactions"])  # copy stored dict so we can extend with defaultReactions
        for _, animalName in self.animalResponses.items():
            self.animalReactions["animalName"] = dict(defaultReactions)

    def respond(self, message: IRCMessage) -> IRCResponse:
        for match, animal in self.animalResponses.items():
            if re.search(r'^{}([^\s\w]+)?$'.format(match), message.messageString, re.IGNORECASE):
                roll = random.randint(1, 20)
                reaction = self.animalReactions[animal][roll]
                return IRCResponse(ResponseType.Say, reaction, message.replyTo)


animals = Animals()
