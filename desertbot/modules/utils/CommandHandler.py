"""
Created on Feb 28, 2018

@author: StarlitGhost
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer


@implementer(IPlugin, IModule)
class CommandHandler(BotModule):
    def actions(self):
        return super(CommandHandler, self).actions() + [('message-channel', 1, self.handleCommand),
                                                        ('message-user', 1, self.handleCommand)]

    def handleCommand(self, message):
        if message.command:
            return self.bot.moduleHandler.runGatheringAction('botmessage', message)


commandhandler = CommandHandler()
