"""
Created on Jan 29, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime
# TODO: replace this with BeautifulSoup
import xml.etree.ElementTree as ET

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import dateutil.parser as dparser


aYearAgo = datetime.datetime.utcnow() - datetime.timedelta(days=365)
tenMinsAgo = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)

DataStore = {
    'LRRCast': {
        'url': 'http://feeds.feedburner.com/lrrcast',
        'lastUpdate': aYearAgo,
        'lastTitle': '',
        'lastLink': '',
        'lastCheck': tenMinsAgo,
        'aliases': ["podcast", "cast", "lrrc", "llrc", "lcast", "lc", 'chat'],
        'suppress': True},
    'LRR Blog': {
        'url': 'http://loadingreadyrun.com/blog/feed/',
        'lastUpdate': aYearAgo,
        'lastTitle': '',
        'lastLink': '',
        'lastCheck': tenMinsAgo,
        'aliases': ['blog'],
        'suppress': True}
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
                # TODO: log an error here that the feed likely no longer exists!
                continue

            # TODO: replace this with BeautifulSoup
            root = ET.fromstring(response.content)
            item = root.find('channel/item')

            if item is None:
                # TODO: log an error here that the feed likely no longer exists!
                continue

            newestDate = dparser.parse(item.find('pubDate').text, fuzzy=True, ignoretz=True)

            if newestDate > feedDeets['lastUpdate']:
                DataStore[feedName]['lastUpdate'] = newestDate

                if feedDeets['suppress']:
                    DataStore[feedName]['suppress'] = False
                else:
                    title = item.find('title').text
                    DataStore[feedName]['lastTitle'] = title
                    link = self.bot.moduleHandler.runActionUntilValue('shorten-url',
                                                                      item.find('link').text)
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
