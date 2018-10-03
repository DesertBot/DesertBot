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
import time

from builtins import str
from six import iteritems

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from desertbot.utils.api_keys import load_key
from desertbot.utils import string

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
        self.twitchClientID = load_key(u'Twitch Client ID')

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
        twitterMatch = re.search(r'twitter\.com/(?P<tweeter>[^/]+)/status(es)?/(?P<tweetID>[0-9]+)', url)
        steamMatch   = re.search(r'store\.steampowered\.com/(?P<steamType>(app|sub))/(?P<steamID>[0-9]+)', url)
        twitchMatch  = re.search(r'twitch\.tv/(?P<twitchChannel>[^/]+)/?(\s|$)', url)

        if twitterMatch:
            return self.FollowTwitter(twitterMatch.group('tweeter'), twitterMatch.group('tweetID'))
        elif steamMatch:
            return self.FollowSteam(steamMatch.group('steamType'), steamMatch.group('steamID'))
        elif twitchMatch:
            return self.FollowTwitch(twitchMatch.group('twitchChannel'))
        elif not re.search('\.(jpe?g|gif|png|bmp)$', url):
            return self.FollowStandard(url)

    def FollowTwitter(self, tweeter, tweetID):
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
        text = re.sub('[\r\n]+', self.graySplitter, text)

        formatString = str(colour(A.normal[A.fg.gray['[{0}]'], A.bold[' {1}:'], ' {2}']))

        return formatString.format(tweetTimeText, user, text), url

    def FollowSteam(self, steamType, steamId):
        steamType = {'app': 'app', 'sub': 'package'}[steamType]
        params = '{0}details/?{0}ids={1}&cc=US&l=english&v=1'.format(steamType, steamId)
        url = 'http://store.steampowered.com/api/{}'.format(params)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        j = response.json()
        if not j[steamId]['success']:
            return  # failure

        appData = j[steamId]['data']

        data = []

        # name
        if 'developers' in appData:
            developers = u', '.join(appData['developers'])
            name = colour(A.normal[appData['name'], A.fg.gray[' by '], developers])
        else:
            name = appData['name']
        data.append(name)

        # package contents (might need to trim this...)
        if 'apps' in appData:
            appNames = [app['name'] for app in appData['apps']]
            apps = u'Package containing: {}'.format(u', '.join(appNames))
            data.append(apps)

        # genres
        if 'genres' in appData:
            genres = ', '.join([genre['description'] for genre in appData['genres']])
            data.append(u'Genres: ' + genres)

        # release date
        releaseDate = appData['release_date']
        if not releaseDate['coming_soon']:
            if releaseDate['date']:
                data.append(u'Released: ' + releaseDate['date'])
        else:
            upcomingDate = A.fg.cyan[A.bold[str(releaseDate['date'])]]
            data.append(colour(A.normal['To Be Released: ', upcomingDate]))

        # metacritic
        # http://www.metacritic.com/faq#item32
        # (Why is the breakdown of green, yellow, and red scores different for games?)
        if 'metacritic' in appData:
            metaScore = appData['metacritic']['score']
            if metaScore < 50:
                metacritic = colour(A.normal[A.fg.red[str(metaScore)]])
            elif metaScore < 75:
                metacritic = colour(A.normal[A.fg.orange[str(metaScore)]])
            else:
                metacritic = colour(A.normal[A.fg.green[str(metaScore)]])
            data.append(u'Metacritic: {0}'.format(metacritic))

        # prices
        priceField = {'app': 'price_overview', 'package': 'price'}[steamType]
        if priceField in appData:
            prices = {'USD': appData[priceField],
                      'GBP': self.getSteamPrice(steamType, steamId, 'GB'),
                      'EUR': self.getSteamPrice(steamType, steamId, 'FR'),
                      'AUD': self.getSteamPrice(steamType, steamId, 'AU')}

            currencies = {'USD': u'$',
                          'GBP': u'\u00A3',
                          'EUR': u'\u20AC',
                          'AUD': u'AU$'}

            # filter out AUD if same as USD (most are)
            if not prices['AUD'] or prices['AUD']['final'] == prices['USD']['final']:
                del prices['AUD']

            # filter out any missing prices
            prices = {key: val for key, val in iteritems(prices) if val}
            priceList = [currencies[val['currency']] + str(val['final'] / 100.0)
                         for val in prices.values()]
            priceString = u'/'.join(priceList)
            if prices['USD']['discount_percent'] > 0:
                discount = ' ({0}% sale!)'.format(prices['USD']['discount_percent'])
                priceString += colour(A.normal[A.fg.green[A.bold[discount]]])

            data.append(priceString)

        # platforms
        if 'platforms' in appData:
            platforms = appData['platforms']
            platformArray = []
            if platforms['windows']:
                platformArray.append(u'Win')
            else:
                platformArray.append(u'---')
            if platforms['mac']:
                platformArray.append(u'Mac')
            else:
                platformArray.append(u'---')
            if platforms['linux']:
                platformArray.append(u'Lin')
            else:
                platformArray.append(u'---')
            data.append(u'/'.join(platformArray))

        # description
        if 'about_the_game' in appData and appData['about_the_game'] is not None:
            limit = 100
            description = re.sub(r'(<[^>]+>|[\r\n\t])+', colour(A.normal[' ', A.fg.gray['>'], ' ']), appData['about_the_game'])
            if len(description) > limit:
                description = u'{0} ...'.format(description[:limit].rsplit(' ', 1)[0])
            data.append(description)

        url = 'http://store.steampowered.com/{}/{}'.format({'app': 'app', 'package': 'sub'}[steamType], steamId)
        return self.graySplitter.join(data), url

    def getSteamPrice(self, appType, appId, region):
        url = 'http://store.steampowered.com/api/{0}details/?{0}ids={1}&cc={2}&l=english&v=1'.format(appType, appId, region)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
        priceField = {'app': 'price_overview', 'package': 'price'}[appType]
        j = response.json()

        if 'data' not in j[appId]:
            return

        if region == 'AU':
            j[appId]['data'][priceField]['currency'] = 'AUD'
        return j[appId]['data'][priceField]

    def FollowTwitch(self, channel):
        # Heavily based on Didero's DideRobot code for the same
        # https://github.com/Didero/DideRobot/blob/06629fc3c8bddf8f729ce2d27742ff999dfdd1f6/commands/urlTitleFinder.py#L37
        # TODO: other stats?
        if self.twitchClientID is None:
            return '[Twitch Client ID not found]'

        chanData = {}
        channelOnline = False
        twitchHeaders = {'Accept': 'application/vnd.twitchtv.v3+json',
                         'Client-ID': self.twitchClientID}
        url = u'https://api.twitch.tv/kraken/streams/{}'.format(channel)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url,
                                                              extraHeaders=twitchHeaders)

        streamData = response.json()

        if 'stream' in streamData and streamData['stream'] is not None:
            chanData = streamData['stream']['channel']
            channelOnline = True
        elif 'error' not in streamData:
            url = u'https://api.twitch.tv/kraken/channels/{}'.format(channel)
            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url,
                                                                  extraHeaders=twitchHeaders)
            chanData = response.json()

        if len(chanData) == 0:
            return

        output = []
        if channelOnline:
            name = colour(A.normal[A.fg.green['{}'.format(chanData['display_name'])]])
        else:
            name = colour(A.normal[A.fg.red['{}'.format(chanData['display_name'])]])
        output.append(name)
        title = ' "{}"'.format(re.sub(r'[\r\n]+', self.graySplitter, chanData['status'].strip()))
        output.append(title)
        if chanData['game'] is not None:
            game = colour(A.normal[A.fg.gray[', playing '], '{}'.format(chanData['game'])])
            output.append(game)
        if chanData['mature']:
            mature = colour(A.normal[A.fg.lightRed[' [Mature]']])
            output.append(mature)
        if channelOnline:
            viewers = streamData['stream']['viewers']
            status = colour(A.normal[A.fg.green[' (Live with {0:,d} viewers)'.format(viewers)]])
        else:
            status = colour(A.normal[A.fg.red[' (Offline)']])
        output.append(status)

        return ''.join(output), 'https://twitch.tv/{}'.format(channel)

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
