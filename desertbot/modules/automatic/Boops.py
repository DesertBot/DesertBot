from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule, ignore
from zope.interface import implementer

import random
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Boops(BotModule):

    def actions(self):
        return super(Boops, self).actions() + [('message-channel', 1, self.respond),
                                               ('message-user', 1, self.respond),
                                               ('action-channel', 1, self.respond),
                                               ('action-user', 1, self.respond)]

    def help(self, arg):
        return 'Responds to boops.'

    @ignore
    def respond(self, message: IRCMessage) -> IRCResponse:
        match = re.search('(^|[^\w])b[o0]{2,}ps?([^\w]|$)', message.messageString, re.IGNORECASE)
        if match:
            return IRCResponse(ResponseType.Say, f"Boop! {random.choice(self.bot.storage['boops'])}", message.replyTo)


boop = Boops()
