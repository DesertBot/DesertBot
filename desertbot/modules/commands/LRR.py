"""
Created on Jan 29, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import dateutil.parser as dparser
from bs4 import BeautifulSoup


aYearAgo = datetime.datetime.utcnow() - datetime.timedelta(days=365)
tenMinsAgo = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

DataStore = {
    'LRR Video': {
        'url': 'https://feeds.feedburner.com/Loadingreadyrun',
        'lastUpdate': aYearAgo,
        'lastTitle': '',
        'lastLink': '',
        'lastCheck': tenMinsAgo,
        'aliases': ['vid', 'vids', 'video', 'videos', 'v'],
        'suppress': True
    },
    'LRRCast': {
        'url': 'https://loadingreadyrun.com/lrrcasts/feed/all',
        'lastUpdate': aYearAgo,
        'lastTitle': '',
        'lastLink': '',
        'lastCheck': tenMinsAgo,
        'aliases': ["podcast", "cast", "lrrc", "llrc", "lcast", "lc", 'chat'],
        'suppress': True
    },
    'LRR Blog': {
        'url': 'https://loadingreadyrun.com/blog/feed/',
        'lastUpdate': aYearAgo,
        'lastTitle': '',
        'lastLink': '',
        'lastCheck': tenMinsAgo,
        'aliases': ['blog'],
        'suppress': True
    }
}


@implementer(IPlugin, IModule)
class LRR(BotCommand):
    def triggers(self):
        return ['lrr', 'llr']

    def actions(self):
        return super(LRR, self).actions() + [('message-channel', 1, self.checkLRR)]

    def help(self, query):
        if query[0] in self.triggers():
            return "lrr (<series>) - returns a link to the latest LRR video, " \
                "or the latest of a series if you specify one; " \
                "series are: {0}".format(", ".join(DataStore.keys()))
        return "Automatic function, scans LRR video RSS feeds and reports new items in the channel."

    def checkLRR(self, _: IRCMessage):
        responses = []
        for feedName, feedDeets in DataStore.items():
            if feedDeets['lastCheck'] > datetime.datetime.utcnow() - datetime.timedelta(minutes=10):
                continue

            DataStore[feedName]['lastCheck'] = datetime.datetime.utcnow()

            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', feedDeets['url'])

            if not response:
                self.logger.warning('failed to fetch {!r}, either a server hiccup '
                                    'or the feed no longer exists'.format(feedDeets['url']))
                continue

            soup = BeautifulSoup(response.content, 'lxml')
            item = soup.find('item')

            if item is None:
                self.logger.warning("the feed at {!r} doesn't have any items, has it shut down?"
                                    .format(feedDeets['url']))
                continue

            itemDate = item.find('pubdate').text
            newestDate = dparser.parse(itemDate, fuzzy=True, ignoretz=True)

            if newestDate > feedDeets['lastUpdate']:
                DataStore[feedName]['lastUpdate'] = newestDate

                if feedDeets['suppress']:
                    DataStore[feedName]['suppress'] = False
                else:
                    title = item.find('title').text
                    link = item.find('link').text
                    link = self.bot.moduleHandler.runActionUntilValue('shorten-url', link)
                    DataStore[feedName]['lastTitle'] = title
                    DataStore[feedName]['lastLink'] = link
                    response = 'New {0}! Title: {1} | {2}'.format(feedName, title, link)
                    responses.append(IRCResponse(ResponseType.Say, response, '#desertbus'))

        return responses

    def execute(self, message: IRCMessage):
        if len(message.parameters.strip()) > 0:
            feed = self.handleAliases(message.parameters)
            lowerMap = {key.lower(): key for key in DataStore}
            if feed.lower() in lowerMap:
                feedName = lowerMap[feed.lower()]
                feedLatest = DataStore[feedName]['lastTitle']
                feedLink = DataStore[feedName]['lastLink']

                response = 'Latest {}: {} | {}'.format(feedName, feedLatest, feedLink)

                return IRCResponse(ResponseType.Say, response, message.replyTo)

            return IRCResponse(ResponseType.Say,
                               "{} is not one of the LRR series being monitored "
                               "(leave a tell for my owners if it's a new series or "
                               "should be an alias!)".format(message.parameters.strip()),
                               message.replyTo)
        else:
            latestDate = datetime.datetime.utcnow() - datetime.timedelta(days=365 * 10)
            latestFeed = None
            latestTitle = None
            latestLink = None
            for feedName, feedDeets in DataStore.items():
                if feedDeets['lastUpdate'] > latestDate:
                    latestDate = feedDeets['lastUpdate']
                    latestFeed = feedName
                    latestTitle = feedDeets['lastTitle']
                    latestLink = feedDeets['lastLink']

            response = 'Latest {}: {} | {}'.format(latestFeed, latestTitle, latestLink)
            return IRCResponse(ResponseType.Say, response, message.replyTo)

    @classmethod
    def handleAliases(cls, series):
        for feedName, feedDeets in DataStore.items():
            if series.lower() in feedDeets['aliases']:
                return feedName
        return series


lrr = LRR()
