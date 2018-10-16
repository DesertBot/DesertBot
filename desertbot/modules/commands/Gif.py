"""
Created on Dec 05, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import random

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Gif(BotCommand):
    def triggers(self):
        return ['gif']

    def help(self, query):
        return 'gif [<year>] - fetches a random gif posted during Desert Bus'

    def execute(self, message: IRCMessage):
        baseURL = "http://greywool.com/desertbus/{}/gifs/random.php"
        years = range(7, 11)

        if len(message.parameterList) > 0:
            invalid = ("'{}' is not a valid year, valid years are {} to {}"
                       .format(message.parameterList[0], years[0], years[-1]))
            try:
                if len(message.parameterList[0]) < 4:
                    year = int(message.parameterList[0])
                else:
                    raise ValueError
            except ValueError:
                return IRCResponse(ResponseType.Say, invalid, message.replyTo)

            if year not in years:
                return IRCResponse(ResponseType.Say, invalid, message.replyTo)
        else:
            year = random.choice(years)

        url = baseURL.format(year)

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        link = response.content

        return IRCResponse(ResponseType.Say,
                           "Random DB{} gif: {}".format(year, link),
                           message.replyTo)


gif = Gif()
