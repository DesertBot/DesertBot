"""
Created on Feb 05, 2022

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse

from PyDictionary import PyDictionary


@implementer(IPlugin, IModule)
class Define(BotCommand):
    def triggers(self):
        return ['define']

    def help(self, query):
        return ('define <word> - fetches the meaning of the given word using WordNet'
                ', via PyDictionary')

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse(self.help(None), message.replyTo)

        lookup = message.parameterList[0]
        meaning = PyDictionary().meaning(lookup.lower())
        if not meaning:
            return IRCResponse(f"No meaning found for '{lookup}'", message.replyTo)

        results = [f"{lookup}, {wordtype}: {'; '.join(meaning[wordtype])}"
                   for wordtype in ['Noun', 'Verb', 'Adjective', 'Adverb'] if wordtype in meaning]

        responses = [IRCResponse(result, message.replyTo) for result in results]
        return responses


define = Define()
