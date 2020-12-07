"""
Created on Jan 25, 2014

@author: StarlitGhost
"""
import base64
import html
import json
import re
import time

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand


@implementer(IPlugin, IModule)
class Twitter(BotCommand):
    def actions(self):
        return super(Twitter, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Twitter URLs'

    def onLoad(self):
        self.token = None
        self.tokenType = None

    def getToken(self):
        token = self.mhRunActionUntilValue("get-api-key", "TwitterToken")
        tokenType = self.mhRunActionUntilValue("get-api-key", "TwitterTokenType")

        if token:
            self.token = token
            self.tokenType = tokenType
            return

        key = self.mhRunActionUntilValue("get-api-key", "TwitterKey")
        secret = self.mhRunActionUntilValue("get-api-key", "TwitterSecret")
        if not key or not secret:
            self.logger.error("no Twitter API key or secret defined")
            return

        creds = base64.b64encode(f'{key}:{secret}'.encode('utf-8'))
        headers = {
            'Authorization': f'Basic {creds}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        }
        data = 'grant_type=client_credentials'
        url = 'https://api.twitter.com/oauth2/token'

        response = self.mhRunActionUntilValue('post-url', url, data=data, extraHeaders=headers)
        if response is None:
            self.logger.error('no response from Twitter auth endpoint')
            return
        elif not response:
            error = response.json()['errors'][0]
            self.logger.error(f'error {error["code"]} from Twitter auth: {error["message"]}')
            return

        j = response.json()
        if 'access_token' not in j:
            self.logger.warning(f'failed to retrieve Twitter token, {json.dumps(j)}')
            self.token = None
            self.tokenType = None
        else:
            self.token = j['access_token']
            self.tokenType = j['token_type']

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        match = re.search(r'twitter\.com/(?P<tweeter>[^/]+)/status(es)?/(?P<tweetID>[0-9]+)', url)
        if not match:
            return

        if not self.token:
            self.getToken()

            if not self.token:
                return

        # tweeter = match.group('tweeter')
        tweetID = match.group('tweetID')

        url = 'https://api.twitter.com/1.1/statuses/show.json'
        headers = {'Authorization': f'{self.tokenType} {self.token}'}
        params = {'id': tweetID, 'tweet_mode': 'extended'}
        response = self.mhRunActionUntilValue('fetch-url', url, params=params, extraHeaders=headers)
        j = response.json()

        # replace retweets with the original tweet
        if 'retweeted_status' in j:
            j = j['retweeted_status']

        displayName = j['user']['name']
        user = j['user']['screen_name']

        if j['in_reply_to_screen_name'] and j['in_reply_to_screen_name'] != user:
            reply = f"replying to @{j['in_reply_to_screen_name']}"
        else:
            reply = None

        tweetText = j['full_text']

        # replace twitter shortened links with real urls
        for url in j['entities']['urls']:
            tweetText = tweetText.replace(url['url'], url['expanded_url'])

        # replace twitter shortened embedded media links with real urls
        if 'media' in j['entities']:
            mediaDict = {}
            for media in j['extended_entities']['media']:
                if media['url'] not in mediaDict:
                    mediaDict[media['url']] = [media['media_url_https']]
                else:
                    mediaDict[media['url']].append(media['media_url_https'])
            for media, mediaURLs in mediaDict.items():
                splitter = ' · '
                mediaString = splitter.join(mediaURLs)
                tweetText = tweetText.replace(media, mediaString)

        # unescape html entities to their unicode equivalents
        tweetText = html.unescape(tweetText)

        # Thu Jan 30 16:44:15 +0000 2020
        tweetTimeText = j['created_at']
        tweetTimeText = time.strptime(tweetTimeText, '%a %b %d %H:%M:%S %z %Y')
        tweetTimeText = time.strftime('%Y/%m/%d %H:%M UTC', tweetTimeText)

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])
        text = re.sub('[\r\n]+', graySplitter, tweetText)

        formatString = str(colour(A.normal[A.fg.gray['[{time}]'],
                                           A.bold[' {name} (@{user})',
                                                  A.normal[A.fg.gray[' {reply}']] if reply else '',
                                                  ':'],
                                           ' {text}']))

        return formatString.format(time=tweetTimeText,
                                   name=displayName,
                                   user=user,
                                   reply=reply,
                                   text=text), url


twitter = Twitter()
