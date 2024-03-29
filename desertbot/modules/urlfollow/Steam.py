"""
Created on Jan 26, 2014

@author: StarlitGhost
"""
import html
import re

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand


@implementer(IPlugin, IModule)
class Steam(BotCommand):
    def actions(self):
        return super(Steam, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Steam URLs'

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'store\.steampowered\.com/(?P<steamType>(app|sub))/(?P<steamID>[0-9]+)',
                          url)
        if not match:
            return

        steamType = match.group('steamType')
        steamId = match.group('steamID')

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
            developers = ', '.join(appData['developers'])
            name = colour(A.normal[appData['name'], A.fg.gray[' by '], developers])
        else:
            name = appData['name']
        data.append(name)

        # package contents (might need to trim this...)
        if 'apps' in appData:
            appNames = [app['name'] for app in appData['apps']]
            apps = 'Package containing: {}'.format(', '.join(appNames))
            data.append(apps)

        # genres
        if 'genres' in appData:
            genres = ', '.join([genre['description'] for genre in appData['genres']])
            data.append('Genres: ' + genres)

        # release date
        releaseDate = appData['release_date']
        if not releaseDate['coming_soon']:
            if releaseDate['date']:
                data.append('Released: ' + releaseDate['date'])
        else:
            upcomingDate = A.fg.cyan[A.bold[str(releaseDate['date'])]]
            data.append(colour(A.normal['To Be Released: ', upcomingDate]))

        # metacritic
        # http://www.metacritic.com/faq#item32
        # (Why is the breakdown of green, yellow, and red scores different for games?)
        if 'metacritic' in appData:
            metaScore = appData['metacritic']['score']
            if metaScore < 50:
                metacritic = colour(A.fg.red[str(metaScore)])
            elif metaScore < 75:
                metacritic = colour(A.fg.orange[str(metaScore)])
            else:
                metacritic = colour(A.fg.green[str(metaScore)])
            data.append('Metacritic: {}'.format(metacritic))

        # dlc count
        if 'dlc' in appData:
            dlc = 'DLC: {}'.format(len(appData['dlc']))
            data.append(dlc)

        # prices
        if 'is_free' in appData:
            if appData['is_free']:
                free = colour(A.fg.cyan['Free'])
                data.append(free)

        priceField = {'app': 'price_overview', 'package': 'price'}[steamType]
        if priceField in appData:
            prices = {'USD': appData[priceField],
                      'GBP': self.getSteamPrice(steamType, steamId, 'GB'),
                      'EUR': self.getSteamPrice(steamType, steamId, 'FR'),
                      'AUD': self.getSteamPrice(steamType, steamId, 'AU')}

            currencies = {'USD': '$',
                          'GBP': '\u00A3',
                          'EUR': '\u20AC',
                          'AUD': 'AU$'}

            # filter out AUD if same as USD (most are)
            if not prices['AUD'] or prices['AUD']['final'] == prices['USD']['final']:
                del prices['AUD']

            # filter out any missing prices
            prices = {key: val for key, val in prices.items() if val}
            priceList = ['{}{:,.2f}'.format(currencies[val['currency']], val['final'] / 100.0)
                         for val in prices.values()]
            priceString = '/'.join(priceList)
            if prices['USD']['discount_percent'] > 0:
                discount = ' ({}% sale!)'.format(prices['USD']['discount_percent'])
                priceString += colour(A.fg.green[A.bold[discount]])

            data.append(priceString)

        # platforms
        if 'platforms' in appData:
            platforms = appData['platforms']
            platformArray = []
            if platforms['windows']:
                platformArray.append('Win')
            else:
                platformArray.append('---')
            if platforms['mac']:
                platformArray.append('Mac')
            else:
                platformArray.append('---')
            if platforms['linux']:
                platformArray.append('Lin')
            else:
                platformArray.append('---')
            data.append('/'.join(platformArray))

        # description
        if 'short_description' in appData and appData['short_description'] is not None:
            limit = 100
            description = appData['short_description']
            description = html.unescape(description)
            if len(description) > limit:
                description = '{} ...'.format(description[:limit].rsplit(' ', 1)[0])
            data.append(description)

        url = ('http://store.steampowered.com/{}/{}'
               .format({'app': 'app', 'package': 'sub'}[steamType],
                       steamId))
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        return graySplitter.join(data), url

    def getSteamPrice(self, appType, appId, region):
        url = ('http://store.steampowered.com/api/{0}details/?{0}ids={1}&cc={2}&l=english&v=1'
               .format(appType, appId, region))
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
        priceField = {'app': 'price_overview', 'package': 'price'}[appType]
        j = response.json()

        if 'data' not in j[appId]:
            return

        data = j[appId]['data']

        if priceField not in data:
            return

        if region == 'AU':
            data[priceField]['currency'] = 'AUD'
        return data[priceField]


steam = Steam()
