"""
Created on Jun 13, 2013

@author: StarlitGhost
"""
import re

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand


@implementer(IPlugin, IModule)
class Imgur(BotCommand):
    def actions(self):
        return super(Imgur, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Imgur URLs'

    def onLoad(self):
        self.imgurClientID = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'imgur Client ID')

    def follow(self, _: IRCMessage, origUrl: str) -> [str, None]:
        match = re.search(r'(i\.)?imgur\.com/(?P<imgurID>[^\.]+)', origUrl)
        if not match:
            return
        origImgurID = match.group('imgurID')

        if self.imgurClientID is None:
            return '[imgur Client ID not found]', None

        albumLink = False
        if origImgurID.startswith('a/'):
            imgurID = origImgurID.replace('a/', '')
            url = 'https://api.imgur.com/3/album/{}'.format(imgurID)
            albumLink = True
        elif origImgurID.startswith('gallery/'):
            imgurID = origImgurID.replace('gallery/', '')
            url = 'https://api.imgur.com/3/gallery/{}'.format(imgurID)
        else:
            imgurID = origImgurID
            url = 'https://api.imgur.com/3/image/{}'.format(origImgurID)

        headers = {'Authorization': 'Client-ID {}'.format(self.imgurClientID)}

        mh = self.bot.moduleHandler
        response = mh.runActionUntilValue('fetch-url', url, extraHeaders=headers)

        if not response:
            return

        j = response.json()

        imageData = j['data']

        if not imageData['title']:
            if imageData['section']:
                # subreddit galleries have a different endpoint with better data.
                #  we don't know if it's a subreddit gallery image until we fetch it,
                #  so we're stuck with this double-lookup. oh well.
                url = ('https://api.imgur.com/3/gallery/r/{}/{}'
                       .format(imageData['section'], imgurID))
                response = mh.runActionUntilValue('fetch-url', url, extraHeaders=headers)
                if not response:
                    return
                j = response.json()
                imageData = j['data']

        data = []
        if imageData['title']:
            data.append(imageData['title'])
        else:
            data.append('<No Title>')
        if imageData['nsfw']:
            data.append('\x034\x02NSFW!\x0F')
        if albumLink:
            data.append('Album: {} Images'.format(imageData['images_count']))
        else:
            if 'is_album' in imageData and imageData['is_album']:
                data.append('Album: {:,d} Images'.format(len(imageData['images'])))
            else:
                if imageData['animated']:
                    data.append('\x032\x02Animated!\x0F')
                if imageData['has_sound']:
                    data.append('\x032\x02Sound!\x0F')
                data.append('{:,d}x{:,d}'.format(imageData['width'], imageData['height']))
                data.append('Size: {:,d}kb'.format(int(imageData['size']/1024)))
        data.append('Views: {:,d}'.format(imageData['views']))

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        return graySplitter.join(data), '[no imgur url]'


imgur = Imgur()
