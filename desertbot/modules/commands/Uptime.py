"""
Created on Dec 18, 2011

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import datetime

import psutil


@implementer(IPlugin, IModule)
class Uptime(BotCommand):
    def triggers(self):
        return ['uptime']

    def help(self, query):
        return ("uptime - tells you the bot's uptime"
                " (actually that's a lie right now, it gives you the bot's server's uptime)")

    def execute(self, message: IRCMessage):
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.BOOT_TIME)

        return IRCResponse(ResponseType.Say,
                           'Uptime: %s' % str(uptime).split('.')[0],
                           message.replyTo)


uptime = Uptime()
