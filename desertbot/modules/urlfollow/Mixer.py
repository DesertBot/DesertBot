"""
Created on May 5, 2019

@author: MasterGunner
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage

from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import re


@implementer(IPlugin, IModule)
class Mixer(BotCommand):
    def actions(self):
        return super(Mixer, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Mixer URLs'

    def onLoad(self):
        self.mixerClientID = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'Mixer Client ID')

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        # Heavily based on Didero's DideRobot code for the same
        # https://github.com/Didero/DideRobot/blob/06629fc3c8bddf8f729ce2d27742ff999dfdd1f6/commands/urlTitleFinder.py#L37
        match = re.search(r'mixer\.com/(?P<mixerChannel>[^/]+)/?(\s|$)', url)
        if not match:
            return
        channel = match.group('mixerChannel')

        if self.mixerClientID is None:
            return '[Mixer Client ID not found]'

        chanData = {}
        channelOnline = False
        mixerHeaders = {'Accept': 'application/json',
                        'Client-ID': self.mixerClientID}
        url = 'https://mixer.com/api/v1/channels/{}'.format(channel)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url,
                                                              extraHeaders=mixerHeaders)

        streamData = response.json()

        if len(streamData) > 0 and 'online' in streamData:
            chanData = streamData
            channelOnline = streamData['online']
        else:
            return

        output = []
        if channelOnline:
            name = colour(A.normal[A.fg.green['{}'.format(chanData['user']['username'])]])
        else:
            name = colour(A.normal[A.fg.red['{}'.format(chanData['user']['username'])]])
        output.append(name)
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        title = ' "{}"'.format(re.sub(r'[\r\n]+', graySplitter, chanData['name'].strip()))
        output.append(title)
        game = colour(A.normal[A.fg.gray[', playing '], '{}'.format(chanData['type']['name'])])
        output.append(game)
        if chanData['audience'] == "18+":
            mature = colour(A.normal[A.fg.lightRed[' [Mature]']])
            output.append(mature)
        if channelOnline:
            viewers = streamData['viewersCurrent']
            status = colour(A.normal[A.fg.green[' (Live with {0:,d} viewers)'.format(viewers)]])
        else:
            status = colour(A.normal[A.fg.red[' (Offline)']])
        output.append(status)

        return ''.join(output), 'https://mixer.com/{}'.format(channel)


mixer = Mixer()
