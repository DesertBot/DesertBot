"""
Created on Jan 27, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.utils.api_keys import load_key
from desertbot.utils import string

from isodate import parse_duration
import dateutil.parser
import dateutil.tz
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

import datetime
import re


@implementer(IPlugin, IModule)
class YouTube(BotCommand):
    def actions(self):
        return super(YouTube, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows YouTube URLs'

    def onLoad(self):
        self.youtubeKey = load_key('YouTube')

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'(youtube\.com/watch.+v=|youtu\.be/)(?P<videoID>[^&#\?]{11})', url)
        if not match:
            return
        videoID = match.group('videoID')

        if self.youtubeKey is None:
            return '[YouTube API key not found]', None

        url = 'https://www.googleapis.com/youtube/v3/videos'
        fields = ('items('
                    'id,'
                    'snippet('
                      'title,'
                      'description,'
                      'channelTitle,'
                      'liveBroadcastContent'
                    '),'
                    'contentDetails(duration),'
                    'statistics(viewCount),'
                    'liveStreamingDetails(scheduledStartTime)'
                  ')')
        parts = 'snippet,contentDetails,statistics,liveStreamingDetails'
        params = {
            'id': videoID,
            'fields': fields,
            'part': parts,
            'key': self.youtubeKey,
        }

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url',
                                                              url,
                                                              params=params)
        j = response.json()

        if 'items' not in j:
            return None

        data = []

        vid = j['items'][0]

        title = vid['snippet']['title']
        data.append(title)
        channel = vid['snippet']['channelTitle']
        data.append(channel)
        if vid['snippet']['liveBroadcastContent'] == 'none':
            length = parse_duration(vid['contentDetails']['duration']).total_seconds()
            m, s = divmod(int(length), 60)
            h, m = divmod(m, 60)
            if h > 0:
                length = '{0:02d}:{1:02d}:{2:02d}'.format(h, m, s)
            else:
                length = '{0:02d}:{1:02d}'.format(m, s)

            data.append(length)
        elif vid['snippet']['liveBroadcastContent'] == 'upcoming':
            startTime = vid['liveStreamingDetails']['scheduledStartTime']
            startDateTime = dateutil.parser.parse(startTime)
            now = datetime.datetime.now(dateutil.tz.tzutc())
            delta = startDateTime - now
            timespan = string.deltaTimeToString(delta, 'm')
            timeString = colour(A.normal['Live in ', A.fg.cyan[A.bold[timespan]]])
            data.append(timeString)
            pass  # time till stream starts, indicate it's upcoming
        elif vid['snippet']['liveBroadcastContent'] == 'live':
            status = str(colour(A.normal[A.fg.red[A.bold['{} Live']]]))
            status = status.format('●')
            data.append(status)
        else:
            pass  # if we're here, wat

        views = int(vid['statistics']['viewCount'])
        data.append('{:,}'.format(views))

        description = vid['snippet']['description']
        if not description:
            description = '<no description available>'
        description = re.sub('(\n|\s)+', ' ', description)
        limit = 150
        if len(description) > limit:
            description = '{} ...'.format(description[:limit].rsplit(' ', 1)[0])
        data.append(description)

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        return graySplitter.join(data), 'http://youtu.be/{}'.format(videoID)


youtube = YouTube()
