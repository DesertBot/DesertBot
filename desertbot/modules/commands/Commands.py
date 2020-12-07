from typing import Union

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class Commands(BotCommand):
    def triggers(self):
        return ["commands"]

    def help(self, query: Union[str, None]) -> str:
        return "Commands: commands - Lists all bot commands from all loaded modules."

    def execute(self, message: IRCMessage):
        commandsList = []
        for moduleName, module in self.bot.moduleHandler.modules.items():
            if isinstance(module, BotCommand):
                commandsList += module.triggers()
        return IRCResponse("Available commands: {}".format(", ".join(sorted(commandsList))), message.replyTo)


commandsCommand = Commands()