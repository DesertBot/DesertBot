"""
Created on Dec 20, 2011

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import inspect
import os


@implementer(IPlugin, IModule)
class Source(BotCommand):
    def triggers(self):
        return ['source']

    def help(self, query):
        return (f"source (<command>) - returns a link to {self.bot.nick}'s source, "
                f"or a specific command/module if given")

    def execute(self, message: IRCMessage):
        rootSourceURL = self.bot.config.getWithDefault('source',
                                                       'https://github.com/DesertBot/DesertBot/')

        if message.parameterList:
            command = message.parameterList[0].lower()
            mh = self.bot.moduleHandler
            if command in mh.mappedTriggers:
                module = mh.mappedTriggers[command].__class__
            elif command in mh.caseMap:
                module = mh.modules[mh.caseMap[command]].__class__
            else:
                return IRCResponse(ResponseType.Say,
                                   f'"{command}" not recognized as a command or module name',
                                   message.replyTo)
            fullModulePath = inspect.getsourcefile(module)
            relModulePath = os.path.relpath(fullModulePath)

            fullModuleURL = f"{rootSourceURL}blob/master/{relModulePath}"
            name = module.__name__

            return IRCResponse(ResponseType.Say,
                               f"Source of {name}: {fullModuleURL}",
                               message.replyTo)

        return IRCResponse(ResponseType.Say,
                           rootSourceURL,
                           message.replyTo)


source = Source()
