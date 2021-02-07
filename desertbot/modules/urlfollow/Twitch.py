"""
Created on Apr 27, 2014

@author: StarlitGhost, HelleDaryd
"""
from datetime import datetime, timezone
import dateutil.parser as dparser

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.utils.string import deltaTimeToString

import jq
import re2 as re

TWITCH_GQL = "https://gql.twitch.tv/gql#origin=twilight"
TWITCH_URL_RE = re.compile(r'twitch\.tv/(?P<twitchChannel>[^/]+)/?(\s|$)')
TWITCH_PARSER = jq.compile("""
        [.[] | .data | (.user // .userByAttribute)] |
        (.[0].lastBroadcast | { title: .title, game: .game.displayName }) +
        { since: .[1].stream.createdAt } +
        { viewers: .[2].stream.viewersCount } +
        { name: .[3].displayName } +
        { mature: .[4].broadcastSettings.isMature }
    """)

@implementer(IPlugin, IModule)
class Twitch(BotCommand):
    def actions(self):
        return super(Twitch, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Twitch URLs'

    def onLoad(self):
        self.twitchClientID = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'Twitch Client ID')

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = TWITCH_URL_RE.search(url)
        if not match:
            return

        channel = match.group('twitchChannel')

        #if self.twitchClientID is None:
        #    return '[Twitch Client ID not found]'

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US",
            "Referer": "https://www.twitch.tv/",
            "Client-Id": "\x6b\x69\x6d\x6e\x65\x37\x38\x6b\x78\x33\x6e\x63\x78\x36\x62\x72\x67\x6f\x34\x6d\x76\x36\x77\x6b\x69\x35\x68\x31\x6b\x6f",
            # self.twitchClientID
            "Content-Type": "text/plain;charset=UTF-8",
            "Origin": "https://www.twitch.tv",
            "DNT": "1",
            "Connection": "keep-alive"
        }

        query = [
            {
                "operationName": "UseLiveBroadcast",
                "variables": {"channelLogin": f"{channel}"},
                "extensions":{
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "5ab2aee4bf1e768b9dc9020a9ae7ccf6f30f78b0a91d5dad504b29df4762c08a"
                    }
                }
            },
            {
                "operationName": "UseLive",
                "variables": {"channelLogin": f"{channel}"},
                "extensions":{
                    "persistedQuery":{
                        "version":1,
                        "sha256Hash":"639d5f11bfb8bf3053b424d9ef650d04c4ebb7d94711d644afb08fe9a0fad5d9"
                    }
                }
            },
            {
                "operationName": "UseViewCount",
                "variables": {"channelLogin": f"{channel}"},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "00b11c9c428f79ae228f30080a06ffd8226a1f068d6f52fbc057cbde66e994c2"
                    }
                }
            },
            {
                "operationName": "ChannelShell",
                "variables": {"login": f"{channel}"},
                "extensions": {
                    "persistedQuery": {
                        "version":1,
                        "sha256Hash":"2b29e2150fe65ee346e03bd417bbabbd0471a01a84edb7a74e3c6064b0283287"
                    }
                }
            }
        ]


        response = self.bot.moduleHandler.runActionUntilValue('post-url', TWITCH_GQL,
                                                              json=query, extraHeaders=headers)

        stream = TWITCH_PARSER.input(response.json()).first()

        if not stream["name"]:
            return

        return self._format_stream(stream), 'https://twitch.tv/{}'.format(channel)

    @staticmethod
    def _format_stream(stream):
        output = []
        if stream["since"]:
            name = colour(A.normal[A.fg.green['{}'.format(stream['name'])]])
        else:
            name = colour(A.normal[A.fg.red['{}'.format(stream['name'])]])
        output.append(name)
        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        title = ' "{}"'.format(re.sub(r'[\r\n]+', graySplitter, stream['title'].strip()))
        output.append(title)
        if stream['game'] is not None:
            if stream["since"]:
                game = colour(A.normal[A.fg.gray[', playing '], '{}'.format(stream['game'])])
            else:
                game = colour(A.normal[A.fg.gray[', was last playing '], '{}'.format(stream['game'])])
            output.append(game)
        if stream['mature']:
            mature = colour(A.normal[A.fg.lightRed[' [Mature]']])
            output.append(mature)
        if stream["viewers"] and stream["since"]:
            viewers = stream['viewers']
            timedelta = datetime.now(tz=timezone.utc) - dparser.isoparse(stream["since"])
            timedelta = deltaTimeToString(timedelta)
            status = colour(A.normal[A.fg.green[' (Live with {0:,d} viewers, for {1})'.format(viewers, timedelta)]])
        else:
            status = colour(A.normal[A.fg.red[' (Offline)']])
        output.append(status)

        return ''.join(output)


twitch = Twitch()
