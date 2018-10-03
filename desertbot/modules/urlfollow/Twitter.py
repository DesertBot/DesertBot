# -*- coding: utf-8 -*-
"""
Created on Jan 25, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.utils import string

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import re
import time


@implementer(IPlugin, IModule)
class Twitter(BotCommand):
    def actions(self):
        return super(Twitter, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Twitch URLs'

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'twitter\.com/(?P<tweeter>[^/]+)/status(es)?/(?P<tweetID>[0-9]+)', url)
        if not match:
            return

        tweeter = match.group('tweeter')
        tweetID = match.group('tweetID')
        url = 'https://twitter.com/{}/status/{}'.format(tweeter, tweetID)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        soup = BeautifulSoup(response.content, 'lxml')

        tweet = soup.find(class_='permalink-tweet')

        user = tweet.find(class_='username').text

        tweetText = tweet.find(class_='tweet-text')

        tweetTimeText = tweet.find(class_='client-and-actions').text.strip()
        try:
            tweetTimeText = time.strptime(tweetTimeText, '%I:%M %p - %d %b %Y')
            tweetTimeText = time.strftime('%Y/%m/%d %H:%M', tweetTimeText)
        except ValueError:
            pass
        tweetTimeText = re.sub(r'[\r\n\s]+', u' ', tweetTimeText)

        links = tweetText.find_all('a', {'data-expanded-url': True})
        for link in links:
            link.string = ' ' + link['data-expanded-url']

        embeddedLinks = tweetText.find_all('a', {'data-pre-embedded': 'true'})
        for link in embeddedLinks:
            link.string = ' ' + link['href']

        text = string.unescapeXHTML(tweetText.text)
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        text = re.sub('[\r\n]+', graySplitter, text)

        formatString = str(colour(A.normal[A.fg.gray['[{0}]'], A.bold[' {1}:'], ' {2}']))

        return formatString.format(tweetTimeText, user, text), url


twitter = Twitter()
