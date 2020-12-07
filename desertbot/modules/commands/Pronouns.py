"""
Created on May 26, 2018

@author: HubbeKing
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Pronouns(BotCommand):
    def triggers(self):
        return ["pronouns", "setpron", "rmpron"]

    def help(self, query):
        return ("Commands: pronouns <user>, setpron <pronouns>, rmpron |"
                " Query the user's pronouns, specify your own pronouns,"
                " or remove your pronouns from the database.")

    def execute(self, message: IRCMessage):
        if message.command == "setpron":
            if len(message.parameterList) < 1:
                return IRCResponse("Your pronouns are... blank?", message.replyTo)

            self.storage[message.user.nick.lower()] = message.parameters

            return IRCResponse("Your pronouns have been set as <{}>.".format(message.parameters), message.replyTo)

        elif message.command == "rmpron":
            if message.user.nick.lower() not in self.storage:
                return IRCResponse("I don't even know your pronouns!", message.replyTo)
            else:
                del self.storage[message.user.nick.lower()]

                return IRCResponse("Your pronouns have been deleted.", message.replyTo)
        elif message.command == "pronouns":
            if len(message.parameterList) < 1:
                lookup = message.user.nick
            else:
                lookup = message.parameterList[0]

            if lookup.lower() not in self.storage:
                return IRCResponse("User's pronouns have not been specified.", message.replyTo)
            else:
                return IRCResponse("{} uses <{}> pronouns."
                                   .format(lookup, self.storage[lookup.lower()]), message.replyTo)


pronouns = Pronouns()
