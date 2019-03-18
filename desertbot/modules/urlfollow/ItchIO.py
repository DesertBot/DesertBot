"""
Created on Mar 14, 2019

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import json
import re


@implementer(IPlugin, IModule)
class ItchIO(BotCommand):
    def actions(self):
        return super(ItchIO, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows ItchIO URLs'

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'itch\.io/', url)
        if not match:
            return

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
        soup = BeautifulSoup(response.content, 'lxml')

        if not soup.find('body', {'data-page_name': 'view_game'}):
            return

        gameMetaInfo = soup.find(class_='game_info_panel_widget')
        if not gameMetaInfo:
            return

        # extract infobox information
        def extractInfo(namePattern: str):
            r = re.compile(namePattern)
            nameMatch = gameMetaInfo.find(text=r)
            if not nameMatch:
                return
            value = nameMatch.parent.parent.find_all('td')[-1]
            return value

        updated = extractInfo(r'^\s*Updated\s*$')
        updated = updated.abbr['title'] if updated else None

        published = extractInfo(r'^\s*Published\s*$')
        published = published.abbr['title'] if published else None

        status = extractInfo(r'^\s*Status\s*$')
        status = status.text.strip() if status else None

        platforms = extractInfo(r'^\s*Platforms\s*$')
        platforms = platforms.text.strip() if platforms else None

        rating = extractInfo(r'^\s*Rating\s*$')
        rating_stars = rating.find(class_='star_value')['content'] if rating else None
        rating_count = rating.find(class_='rating_count')['content'] if rating else None

        author = extractInfo(r'^\s*Author\s*$')
        author = author.text.strip() if author else None

        genre = extractInfo(r'^\s*Genre\s*$')
        genre = genre.text.strip() if genre else None

        # extract json information
        gameInfo = soup.find_all('script', {'type': 'application/ld+json'})[-1].text
        gameInfo = json.loads(gameInfo)

        title = gameInfo['name']
        description = gameInfo['description']

        if 'offers' in gameInfo:
            price = gameInfo['offers']['price']
            currency = gameInfo['offers']['priceCurrency']
            if gameInfo['offers']['priceValidUntil']:
                pass  # fetch sale info (original price, percentage discount, end time)

        # build the output
        output = []

        output.append(colour(A.normal[title, A.fg.gray[' by '], author]))

        if genre:
            output.append(colour(A.normal['Genre: ', genre]))

        outStatus = status
        # todo: publish date
        if updated:
            outStatus += ', last updated: ' + updated
        output.append(colour(A.normal[outStatus]))
        if rating:
            output.append(colour(A.normal['Rating: ', rating_stars, '/5',
                                          A.fg.gray[' (', rating_count, ' ratings)']]))
        if price:
            output.append(colour(A.normal[price, ' ', currency]))  # todo: sale stuff
        else:
            output.append('Free')

        if platforms:
            output.append(platforms)
        if description:
            output.append(description)

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        response = graySplitter.join(output)

        return response, url


itchio = ItchIO()
