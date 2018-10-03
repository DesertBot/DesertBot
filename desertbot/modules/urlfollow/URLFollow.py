# -*- coding: utf-8 -*-
"""
Created on Jan 27, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from html.parser import HTMLParser
from urllib.parse import urlparse
import re

from builtins import str

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A


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

    htmlParser = HTMLParser()

    graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])

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

    def handleURL(self, message, auto=True):
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
                                   u'[no url recognized]',
                                   message.replyTo,
                                   {'urlfollowURL': u'[no url recognized]'})
            return

        url = match.group('url')
        follows = self.bot.moduleHandler.runActionUntilValue('urlfollow', message, url)
        if not follows:
            if not auto:
                return IRCResponse(ResponseType.Say,
                                   u'[no follows worked for {}]'.format(url),
                                   message.replyTo,
                                   {'urlfollowURL': u'[no follows worked for {}]'})
            return
        text, url = follows

        return IRCResponse(ResponseType.Say, text, message.replyTo, {'urlfollowURL': url})

    def dispatchToFollows(self, _: IRCMessage, url: str):
        if not re.search('\.(jpe?g|gif|png|bmp)$', url):
            return self.FollowStandard(url)

    def FollowStandard(self, url):
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        if not response:
            return

        if response.url != url:
            return self.dispatchToFollows(None, response.url)

        title = self.GetTitle(response.content)
        if title is not None:
            domain = urlparse(response.url).netloc
            return u'{} (at {})'.format(title, domain), url

        return

    def GetTitle(self, webpage):
        soup = BeautifulSoup(webpage, 'lxml')
        title = soup.title
        if title:
            title = title.text
            title = re.sub(u'[\r\n]+', u'', title)  # strip any newlines
            title = title.strip()  # strip all whitespace either side
            title = u' '.join(title.split())  # replace multiple whitespace with single space
            title = self.htmlParser.unescape(title)  # unescape html entities

            # Split on the first space before 300 characters, and replace the rest with '...'
            if len(title) > 300:
                title = title[:300].rsplit(u' ', 1)[0] + u" ..."

            return title

        return None


urlfollow = URLFollow()
