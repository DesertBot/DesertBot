# -*- coding: utf-8 -*-
"""
Created on May 20, 2014

@author: Tyranic-Moron
"""
import re

from CommandInterface import CommandInterface
from IRCMessage import IRCMessage
from IRCResponse import IRCResponse, ResponseType

from Utils import StringUtils, WebUtils


class Find(CommandInterface):
    triggers = ['find', 'google', 'g']
    help = 'find/google/g <searchterm> - returns the first google result for the given search term'
    runInThread = True

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        try:
            results = WebUtils.googleSearch(message.Parameters)

            firstResult = results[u'items'][0]

            title = firstResult[u'title']
            title = re.sub(r'\s+', ' ', title)
            content = firstResult[u'snippet']
            content = re.sub(r'\s+', ' ', content)  # replace multiple spaces with single ones (includes newlines?)
            content = StringUtils.unescapeXHTML(content)
            url = firstResult[u'link']
            replyText = u'{1}{0}{2}{0}{3}'.format(StringUtils.graySplitter, title, content, url)

            return IRCResponse(ResponseType.Say, replyText, message.ReplyTo)
        except Exception as x:
            print(str(x))
            return IRCResponse(ResponseType.Say, x.args, message.ReplyTo)
