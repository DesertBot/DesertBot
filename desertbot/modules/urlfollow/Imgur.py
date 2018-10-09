# -*- coding: utf-8 -*-
"""
Created on Jun 13, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.utils.api_keys import load_key

from twisted.words.protocols.irc import assembleFormattedText, attributes as A

import re


@implementer(IPlugin, IModule)
class Imgur(BotCommand):
    def actions(self):
        return super(Imgur, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Imgur URLs'

    def onLoad(self):
        self.imgurClientID = load_key(u'imgur Client ID')

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'(i\.)?imgur\.com/(?P<imgurID>[^\.]+)', url)
        if not match:
            return
        imgurID = match.group('imgurID')

        if self.imgurClientID is None:
            return '[imgur Client ID not found]', None

        if imgurID.startswith('gallery/'):
            imgurID = imgurID.replace('gallery/', '')

        albumLink = False
        if imgurID.startswith('a/'):
            imgurID = imgurID.replace('a/', '')
            url = 'https://api.imgur.com/3/album/{0}'.format(imgurID)
            albumLink = True
        else:
            url = 'https://api.imgur.com/3/image/{0}'.format(imgurID)

        headers = {'Authorization': 'Client-ID {0}'.format(self.imgurClientID)}

        mh = self.bot.moduleHandler
        response = mh.runActionUntilValue('fetch-url', url, extraHeaders=headers)

        if not response:
            url = 'https://api.imgur.com/3/gallery/{0}'.format(imgurID)
            response = mh.runActionUntilValue('fetch-url', url, extraHeaders=headers)

        if not response:
            return

        j = response.json()

        imageData = j['data']

        if imageData['title'] is None:
            url = 'https://api.imgur.com/3/gallery/{0}'.format(imgurID)
            response = mh.runActionUntilValue('fetch-url', url, extraHeaders=headers)
            if response:
                j = response.json()
                if j['success']:
                    imageData = j['data']

            if imageData['title'] is None:
                url = 'http://imgur.com/{0}'.format(imgurID)
                response = mh.runActionUntilValue('fetch-url', url)
                title = mh.runActionUntilValue('get-html-title', response.content)
                imageData['title'] = title.replace(' - Imgur', '')
                if imageData['title'] in ['imgur: the simple image sharer',
                                          'Imgur: The magic of the Internet']:
                    imageData['title'] = None

        data = []
        if imageData['title'] is not None:
            data.append(imageData['title'])
        else:
            data.append(u'<No Title>')
        if imageData['nsfw']:
            data.append(u'\x034\x02NSFW!\x0F')
        if albumLink:
            data.append(u'Album: {0} Images'.format(imageData['images_count']))
        else:
            if 'is_album' in imageData and imageData['is_album']:
                data.append(u'Album: {0:,d} Images'.format(len(imageData['images'])))
            else:
                if imageData[u'animated']:
                    data.append(u'\x032\x02Animated!\x0F')
                data.append(u'{0:,d}x{1:,d}'.format(imageData['width'], imageData['height']))
                data.append(u'Size: {0:,d}kb'.format(int(imageData['size']/1024)))
        data.append(u'Views: {0:,d}'.format(imageData['views']))

        graySplitter = assembleFormattedText(A.normal[' ',
                                                      A.fg.gray['|'],
                                                      ' '])
        return graySplitter.join(data), '[no imgur url]'


imgur = Imgur()
