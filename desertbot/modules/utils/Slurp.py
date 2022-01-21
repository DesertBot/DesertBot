"""
Created on Aug 31, 2015

@author: StarlitGhost
"""
import re
from html import unescape

from bs4 import BeautifulSoup
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


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
            return IRCResponse("Not enough parameters, usage: {}".format(self.help(None)), message.replyTo)

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
                return IRCResponse("Problem fetching {}".format(url), message.replyTo)
            soup = BeautifulSoup(response.content, 'lxml')

        if prop.endswith("list"):
            tags = soup.select(selector)
            prop = prop[:-4]
        else:
            tags = [soup.select_one(selector)]

        if not tags:
            return IRCResponse("'{}' does not select a tag at {}".format(selector, url), message.replyTo)

        if prop == 'tagname':
            value = ", ".join(tag.name for tag in tags)
        elif prop == 'text':
            value = ", ".join(tag.text for tag in tags)
        elif prop in tags[0].attrs:
            value = tags[0][prop]
        else:
            attrMissing = ("The tag selected by '{}' ({}) does not have attribute '{}'"
                           .format(selector, tags[0].name, prop))
            return IRCResponse(attrMissing, message.replyTo)

        if not isinstance(value, str):
            value = " ".join(value)

        # sanitize the value
        value = value.strip()
        value = re.sub(r'[\r\n]+', ' ', value)
        value = re.sub(r'\s+', ' ', value)
        value = unescape(value)

        return IRCResponse(value, message.replyTo, metadata={'slurp': {url: soup}, 'var': {'slurpURL': url}})


slurp = Slurp()
