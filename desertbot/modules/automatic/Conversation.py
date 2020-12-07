import re

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule, BotModule, ignore
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class Conversation(BotModule):
    def actions(self):
        return super(Conversation, self).actions() + [('message-channel', 1, self.converse),
                                                      ('message-user', 1, self.converse)]

    def help(self, arg):
        return 'Responds to greetings and such'

    @ignore
    def converse(self, message: IRCMessage):
        greetings = ["(wa+s+|')?so?u+p",
                     "hi(ya)?",
                     "hello",
                     "hey",
                     "'?[yl]o",
                     "(good |g'?)?((mornin|evenin)[g']?|ni(ght|ni)|afternoon|day)",
                     "greetings",
                     "bonjour",
                     "salut(ations)?",
                     "howdy",
                     "o?hai",
                     "mojn",
                     "hej",
                     "dongs",
                     "ahoy( hoy)?",
                     "hola",
                     "bye",
                     "herrow"
                     ]

        regex = (r"^(?P<greeting>{0})( there)?,?[ ]{1}([^a-zA-Z0-9_\|`\[\]\^-]|$)"
                 .format('|'.join(greetings), self.bot.nick))

        match = re.search(regex,
                          message.messageString,
                          re.IGNORECASE)
        if match:
            return IRCResponse('{0} {1}'.format(match.group('greeting'), message.user.nick), message.replyTo)


conversation = Conversation()
