# -*- coding: utf-8 -*-
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Googl(BotCommand):
    def triggers(self):
        return ['googl', 'shorten', 'goo.gl']

    def help(self, query):
        return "googl/shorten <url> - Gives you a shortened version of a url, via Goo.gl"
    
    def execute(self, message: IRCMessage):
        if len(message.ParameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give a URL to shorten!", message.ReplyTo)
        
        url = self.bot.moduleHandler.runActionUntilValue('shorten-url', message.Parameters)
        
        return IRCResponse(ResponseType.Say, url, message.ReplyTo)


googl = Googl()
