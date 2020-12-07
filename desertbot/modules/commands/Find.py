"""
Created on May 20, 2014

@author: StarlitGhost
"""
import re

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse
from desertbot.utils import string


@implementer(IPlugin, IModule)
class Find(BotCommand):
    def triggers(self):
        return ['find', 'google', 'g']

    def help(self, query):
        return ('find/google/g <searchterm>'
                ' - returns the first google result for the given search term')

    def execute(self, message: IRCMessage):
        try:
            results = self.bot.moduleHandler.runActionUntilValue('search-web', message.parameters)

            if not results:
                return IRCResponse('[google developer key missing]', message.replyTo)

            if 'items' not in results:
                return IRCResponse('No results found for query!', message.replyTo)

            firstResult = results['items'][0]

            title = firstResult['title']
            title = re.sub(r'\s+', ' ', title)
            content = firstResult['snippet']
            # replace multiple spaces with single ones (includes newlines?)
            content = re.sub(r'\s+', ' ', content)
            content = string.unescapeXHTML(content)
            url = firstResult['link']
            replyText = '{1}{0}{2}{0}{3}'.format(string.graySplitter, title, content, url)

            return IRCResponse(replyText, message.replyTo)
        except Exception as x:
            self.logger.exception("Exception when finding a thing {}".format(message.parameters))
            return IRCResponse(str(x.args), message.replyTo)


find = Find()
