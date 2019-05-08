"""
Created on Apr 27, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage

from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import re


@implementer(IPlugin, IModule)
class Twitch(BotCommand):
    def actions(self):
        return super(Twitch, self).actions() + [('urlfollow', 2, self.follow),
                                                ("apikeys-available", 1, self.onLoad)]

    def help(self, query):
        return 'Automatic module that follows Twitch URLs'

    def onLoad(self):
        self.twitchClientID = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'Twitch Client ID')

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        # Heavily based on Didero's DideRobot code for the same
        # https://github.com/Didero/DideRobot/blob/06629fc3c8bddf8f729ce2d27742ff999dfdd1f6/commands/urlTitleFinder.py#L37
        match = re.search(r'twitch\.tv/(?P<twitchChannel>[^/]+)/?(\s|$)', url)
        if not match:
            return
        channel = match.group('twitchChannel')

        if self.twitchClientID is None:
            return '[Twitch Client ID not found]'

        chanData = {}
        channelOnline = False
        twitchHeaders = {'Accept': 'application/vnd.twitchtv.v3+json',
                         'Client-ID': self.twitchClientID}
        url = 'https://api.twitch.tv/kraken/streams/{}'.format(channel)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url,
                                                              extraHeaders=twitchHeaders)

        streamData = response.json()

        if 'stream' in streamData and streamData['stream'] is not None:
            chanData = streamData['stream']['channel']
            channelOnline = True
        elif 'error' not in streamData:
            url = 'https://api.twitch.tv/kraken/channels/{}'.format(channel)
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
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        title = ' "{}"'.format(re.sub(r'[\r\n]+', graySplitter, chanData['status'].strip()))
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


twitch = Twitch()
