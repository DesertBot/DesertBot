"""
Created on Aug 31, 2015

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from html import unescape
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from bs4 import BeautifulSoup


@implementer(IPlugin, IModule)
class Slurp(BotCommand):
    def triggers(self):
        return ['slurp']

    def help(self, query):
        return ("slurp <attribute> <url> <css selector>"
                " - scrapes the given attribute from the tag selected "
                "at the given url")

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 3:
            return IRCResponse(ResponseType.Say,
                               "Not enough parameters, usage: {}".format(self.help(None)),
                               message.replyTo)

        prop, url, selector = (message.parameterList[0],
                               message.parameterList[1],
                               " ".join(message.parameterList[2:]))

        if not re.match(r'^\w+://', url):
            url = "http://{}".format(url)

        if 'slurp' in message.metadata and url in message.metadata['slurp']:
            soup = message.metadata['slurp'][url]
        else:
            response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
            if not response:
                return IRCResponse(ResponseType.Say,
                                   "Problem fetching {}".format(url),
                                   message.replyTo)
            soup = BeautifulSoup(response.content, 'lxml')

        tag = soup.select_one(selector)

        if tag is None:
            return IRCResponse(ResponseType.Say,
                               "'{}' does not select a tag at {}".format(selector, url),
                               message.replyTo)

        specials = {
            'tagname': tag.name,
            'text': tag.text
        }

        if prop in specials:
            value = specials[prop]
        elif prop in tag.attrs:
            value = tag[prop]
        else:
            attrMissing = ("The tag selected by '{}' ({}) does not have attribute '{}'"
                           .format(selector, tag.name, prop))
            return IRCResponse(ResponseType.Say, attrMissing, message.replyTo)

        if not isinstance(value, str):
            value = " ".join(value)

        # sanitize the value
        value = value.strip()
        value = re.sub(r'[\r\n]+', ' ', value)
        value = re.sub(r'\s+', ' ', value)
        value = unescape(value)

        return IRCResponse(ResponseType.Say, value, message.replyTo,
                           extraVars={'slurpURL': url},
                           metadata={'slurp': {url: soup}})


slurp = Slurp()
