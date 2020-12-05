"""
Created on Jan 27, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from urllib.parse import urlparse
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class URLFollow(BotCommand):
    def actions(self):
        return super(URLFollow, self).actions() + [('action-channel', 1, self.handleURL),
                                                   ('action-user', 1, self.handleURL),
                                                   ('message-channel', 1, self.handleURL),
                                                   ('message-user', 1, self.handleURL),
                                                   ('urlfollow', 1, self.dispatchToFollows)]

    def triggers(self):
        return ['urlfollow', 'follow']

    def help(self, query):
        return ('Automatic module that follows urls '
                'and grabs information about the resultant webpage')

    def onLoad(self):
        self.autoFollow = True

    def execute(self, message: IRCMessage):
        if message.parameterList[0].lower() == 'on':
            self.autoFollow = True
            return IRCResponse(ResponseType.Say, 'Auto-follow on', message.replyTo)
        if message.parameterList[0].lower() == 'off':
            self.autoFollow = False
            return IRCResponse(ResponseType.Say, 'Auto-follow off', message.replyTo)

        return self.handleURL(message, auto=False)

    def handleURL(self, message: IRCMessage, auto: bool=True):
        if auto and message.command:
            return
        if auto and not self.autoFollow:
            return
        if auto and self.checkIgnoreList(message):
            return

        match = re.search(r'(?P<url>(https?://|www\.)[^\s]+)', message.messageString, re.IGNORECASE)
        if not match:
            if not auto:
                return IRCResponse(ResponseType.Say,
                                   '[no url recognized]',
                                   message.replyTo,
                                   metadata={'var': {'urlfollowURL': '[no url recognized]'}})
            return

        url = match.group('url')
        follows = self.bot.moduleHandler.runActionUntilValue('urlfollow', message, url)
        if not follows:
            if not auto:
                return IRCResponse(ResponseType.Say,
                                   '[no follows worked for {}]'.format(url),
                                   message.replyTo,
                                   metadata={'var': {'urlfollowURL': '[no follows worked for {}]'}})
            return
        text, url = follows

        return IRCResponse(ResponseType.Say, text, message.replyTo,
                           metadata={'var': {'urlfollowURL': url}})

    def dispatchToFollows(self, message: IRCMessage, url: str):
        if not re.search('\.(jpe?g|gif|png|bmp)$', url):
            return self.FollowStandard(message, url)

    def FollowStandard(self, message: IRCMessage, url: str):
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        if not response:
            return

        if response.url != url:
            return self.bot.moduleHandler.runActionUntilValue('urlfollow', message, response.url)

        short = self.bot.moduleHandler.runActionUntilValue('shorten-url', url)

        title = self.bot.moduleHandler.runActionUntilValue('get-html-title', response.content)
        if title is not None:
            domain = urlparse(response.url).netloc
            return ('{title} (at {domain}) {short}'
                    .format(title=title, domain=domain, short=short),
                    url)

        return


urlfollow = URLFollow()
