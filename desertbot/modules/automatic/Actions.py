from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule, ignore
from zope.interface import implementer

import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Actions(BotModule):
    def actions(self):
        return super(Actions, self).actions() + [('action-channel', 1, self.handleAction),
                                                 ('action-user', 1, self.handleAction)]

    def help(self, arg):
        return 'Responds to various actions'

    @ignore
    def handleAction(self, message: IRCMessage):
        regex = r"^(?P<action>(\w+s)),?[ ]{}([^a-zA-Z0-9_\|`\[\]\^-]|$)"
        match = re.search(
            regex.format(self.bot.nick),
            message.messageString,
            re.IGNORECASE)
        if match:
            return IRCResponse(re.sub(self.bot.nick, message.user.nick, message.messageString,
                                      flags=re.IGNORECASE), message.replyTo, ResponseType.Do)


actions = Actions()
