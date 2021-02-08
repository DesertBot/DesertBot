"""
Created on Dec 20, 2011

@author: StarlitGhost
"""
import inspect
import os

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


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

            customSource = mh.runActionUntilValue('fetch-command-source', command)
            if customSource:
                return IRCResponse(customSource, message.replyTo)

            if command in mh.mappedTriggers:
                module = mh.mappedTriggers[command].__class__
            elif command in mh.caseMap:
                module = mh.modules[mh.caseMap[command]].__class__
            else:
                return IRCResponse(f'"{command}" not recognized as a command or module name', message.replyTo)
            fullModulePath = inspect.getsourcefile(module)
            relModulePath = os.path.relpath(fullModulePath)

            fullModuleURL = f"{rootSourceURL}blob/master/{relModulePath}"
            name = module.__name__

            return IRCResponse(f"Source of {name}: {fullModuleURL}", message.replyTo)

        return IRCResponse(rootSourceURL, message.replyTo)


source = Source()
