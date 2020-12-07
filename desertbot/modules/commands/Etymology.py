# -*- coding: utf-8 -*-
"""
Created on Oct 11, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import re

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A


@implementer(IPlugin, IModule)
class Etymology(BotCommand):
    def triggers(self):
        return ['etymology', 'etym']

    def help(self, query):
        return ("etym <search term> (index) - returns the etymology of the "
                "given search term from EtymOnline.com")

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse("You didn't give a word! Usage: {}".format(self.help(None)), message.replyTo)

        mh = self.bot.moduleHandler

        searchURL = 'https://www.etymonline.com/search'
        query = message.parameterList[0]
        if len(message.parameterList) > 1:
            try:
                index = int(message.parameterList[1]) - 1
                if index < 0:
                    index = 0
            except ValueError:
                return IRCResponse('Index {!r} is not an integer! Usage: {}'
                                   .format(message.parameterList[1], self.help(None)), message.replyTo)
        else:
            index = 0

        results = mh.runActionUntilValue('fetch-url', searchURL,
                                         params={'q': query})

        soup = BeautifulSoup(results.content, 'lxml')
        words = soup.find_all(class_='word--C9UPa')
        if not words:
            return IRCResponse('No results found for {!r}'.format(query), message.replyTo)

        totalResults = soup.find(class_='searchList__pageCount--2jQdB').text
        totalResults = int(re.sub(r'[^\d]', '', totalResults))

        if index >= totalResults:
            index = totalResults - 1
        displayIndex = '{}/{}'.format(index + 1, totalResults)
        if index >= len(words):
            results = mh.runActionUntilValue('fetch-url', searchURL,
                                             params={'q': query, 'page': index // len(words) + 1})
            index %= len(words)
            soup = BeautifulSoup(results.content, 'lxml')
            words = soup.find_all(class_='word--C9UPa')
            if index >= len(words):
                index = len(words) - 1

        word = words[index].find(class_='word__name--TTbAA')
        word = word.text

        defn = words[index].find(class_='word__defination--2q7ZH')
        defn = ' '.join(defn.text.splitlines())
        limit = 500
        if len(defn) > limit:
            defn = '{} ...'.format(defn[:limit].rsplit(' ', 1)[0])

        wordURL = 'https://www.etymonline.com{}'.format(words[index]['href'])
        url = mh.runActionUntilValue('shorten-url', wordURL)

        response = colour(A.normal[A.bold['{}: '.format(word)],
                                   defn,
                                   A.fg.gray[' | {} | '.format(displayIndex)],
                                   url])

        return IRCResponse(response, message.replyTo)


etymology = Etymology()
