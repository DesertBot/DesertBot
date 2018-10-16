# -*- coding: utf-8 -*-
"""
Created on Aug 16, 2018

@author: StarlitGhost
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

from desertbot.message import IRCMessage

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import dateutil.parser
import dateutil.tz


@implementer(IPlugin, IModule)
class Mastodon(BotModule):
    def actions(self):
        return super(Mastodon, self).actions() + [('urlfollow', 2, self.followURL)]

    def help(self, query):
        return ('Automatic module that fetches toots from Mastodon URLs. '
                'May have more functionality in future.')

    def followURL(self, _: IRCMessage, url: str) -> [str, None]:
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        if not response:
            return

        # we'd check Server: Mastodon here but it seems that not every server
        # sets that correctly
        if 'Set-Cookie' not in response.headers:
            return
        if not response.headers['Set-Cookie'].startswith('_mastodon_session'):
            return

        soup = BeautifulSoup(response.content, 'lxml')

        toot = soup.find(class_='entry-center')
        if not toot:
            # presumably not a toot, ignore
            return

        date = toot.find(class_='dt-published')['value']
        date = dateutil.parser.parse(date)
        date = date.astimezone(dateutil.tz.UTC)
        date = date.strftime('%Y/%m/%d %H:%M')

        # handy meta tags that already contain what we want
        user = soup.find(property='og:title')['content']
        # this entry obeys content warnings,
        # which is what we want for the auto-follow
        text = soup.find(property='og:description')['content']

        # strip empty lines, strip leading/ending whitespace,
        # and replace newlines with gray pipes
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        text = graySplitter.join(lines)

        formatString = str(colour(A.normal[A.fg.gray['[{date}]'], A.bold[' {user}:'], ' {text}']))

        return formatString.format(date=date, user=user, text=text), ''


mastodon = Mastodon()
