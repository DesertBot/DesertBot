"""
Created on Jan 24, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from urllib.parse import quote

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A


@implementer(IPlugin, IModule)
class Urban(BotCommand):
    def triggers(self):
        return ['urban', 'ud']

    def help(self, query):
        return ("urban <search term>"
                " - returns the definition of the given search term from UrbanDictionary.com")

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say,
                               "You didn't give a word! Usage: {0}".format(self.help),
                               message.replyTo)

        search = quote(message.parameters)

        url = 'http://api.urbandictionary.com/v0/define?term={0}'.format(search)

        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        j = response.json()

        if len(j['list']) == 0:
            return IRCResponse(ResponseType.Say,
                               "No entry found for '{0}'".format(message.parameters),
                               message.replyTo)

        graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])

        defn = j['list'][0]

        word = defn['word']

        definition = defn['definition']
        definition = graySplitter.join([s.strip() for s in definition.strip().splitlines() if s])

        example = defn['example']
        example = graySplitter.join([s.strip() for s in example.strip().splitlines() if s])

        author = defn['author']

        up = defn['thumbs_up']
        down = defn['thumbs_down']

        more = 'http://{}.urbanup.com/'.format(word.replace(' ', '-'))

        if word.lower() != message.parameters.lower():
            word = "{0} (Contains '{1}')".format(word, message.parameters)

        defFormatString = str(colour(A.normal[A.bold["{0}:"], " {1}"]))
        exampleFormatString = str(colour(A.normal[A.bold["Example(s):"], " {0}"]))
        byFormatString = str(colour(A.normal["{0}",
                                             graySplitter,
                                             A.fg.lightGreen["+{1}"],
                                             A.fg.gray["/"],
                                             A.fg.lightRed["-{2}"],
                                             graySplitter,
                                             "More defs: {3}"]))
        responses = [IRCResponse(ResponseType.Say,
                                 defFormatString.format(word, definition),
                                 message.replyTo),
                     IRCResponse(ResponseType.Say,
                                 exampleFormatString.format(example),
                                 message.replyTo),
                     IRCResponse(ResponseType.Say,
                                 byFormatString.format(author, up, down, more),
                                 message.replyTo)]

        return responses


urban = Urban()
