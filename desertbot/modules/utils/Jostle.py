"""
Created on Oct 08, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from json import JSONDecodeError
import jsonpath_ng
import re
import collections

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Jostle(BotCommand):
    def triggers(self):
        return ['jostle']

    def help(self, query):
        return ('jostle <url> <jsonpath> - extracts values from json at the given url. '
                'jsonpath syntax: https://github.com/h2non/jsonpath-ng#jsonpath-syntax '
                '(no extensions are currently supported)')

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 2:
            return IRCResponse('Not enough parameters, usage: {}'.format(self.help(None)), message.replyTo)

        path = ' '.join(message.parameterList[1:])

        try:
            parser = jsonpath_ng.parse(path)
        except (jsonpath_ng.lexer.JsonPathLexerError, Exception) as e:
            # yep, jsonpath_ng uses generic exceptions, so this is the best we can do
            return IRCResponse('[Jostle Error: {}]'.format(e), message.replyTo)

        url = message.parameterList[0]
        if not re.match(r'^\w+://', url):
            url = 'http://{}'.format(url)

        if 'jostle' in message.metadata and url in message.metadata['jostle']:
            # use cached data if it exists
            j = message.metadata['jostle'][url]
        else:
            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
            if not response:
                return IRCResponse('[Jostle Error: problem fetching {}]'.format(url), message.replyTo)
            try:
                j = response.json()
            except JSONDecodeError:
                return IRCResponse('[Jostle Error: data at {} is not valid JSON]'.format(url), message.replyTo)

        m = parser.find(j)
        if not m:
            reply = '[Jostle Error: the jsonpath {!r} does not resolve a value from {!r}]'
            reply = reply.format(path, url)
            return IRCResponse(reply, message.replyTo)

        value = m[0].value

        if not isinstance(value, str):
            if isinstance(value, collections.Iterable):
                value = ' '.join(value)
            else:
                value = f'{value}'

        # sanitize the value
        value = value.strip()
        value = re.sub(r'[\r\n]+', ' ', value)
        value = re.sub(r'\s+', ' ', value)

        return IRCResponse(value, message.replyTo, metadata={'jostle': {url: j}, 'var': {'jostleURL': url}})


jostle = Jostle()
