"""
@date: 2021-02-06
@author: HelleDaryd
"""

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
import re2 as re

WIKIPEDIA_URL_RE = re.compile(r"(?i)en\.wikipedia\.org/wiki/(?P<title>(\S+))")
@implementer(IPlugin, IModule)
class Wikipedia(BotCommand):
    def actions(self):
        return super(Wikipedia, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows English Wikipedia URLs'

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = WIKIPEDIA_URL_RE.search(url)
        if not match:
            return

        title = match.group('title')

        response = self.bot.moduleHandler.runActionUntilValue("wikipedia", title)
        if response:
            return str(response), url
        return

wikipedia = Wikipedia()
