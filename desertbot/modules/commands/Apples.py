# -*- coding: utf-8 -*-
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Apples(BotCommand):
    def actions(self):
        return super(Apples, self).actions() + [('message-channel', 1, self.handleApples)]

    def triggers(self):
        return ['playapples', 'stopapples']

    def help(self, query):
        return 'playapples, stopapples - For when you need a 4th for Apples to Apples (will always pick 0)'

    playApples = 0

    def handleApples(self, message):
        if self.playApples == 1 and message.user.name.lower() == "robobo":
            msgArr = message.messageList
            name = msgArr.pop(0).strip()
            cmd = " ".join(msgArr).strip()
            if cmd == "to Apples! You have 60 seconds to join.":
                return IRCResponse(ResponseType.Say, "!join", message.replyTo)
            elif name.lower() == self.bot.nickname and cmd == "is judging.":
                return IRCResponse(ResponseType.Say, "!pick 0", message.replyTo)
            elif name.lower() != self.bot.nickname and (cmd == "is judging next." or cmd == "is judging first."):
                return IRCResponse(ResponseType.Say, "!play 0", message.replyTo)
            elif cmd == "wins the game!" or name == "Sorry,":
                self.playApples = 0

    def execute(self, message: IRCMessage):
        if message.command.lower() == "playapples":
            self.playApples = 1
            return IRCResponse(ResponseType.Say, "!join", message.replyTo)
        elif message.command.lower() == "stopapples":
            self.playApples = 0
            return IRCResponse(ResponseType.Say, "!leave", message.replyTo)


apples = Apples()
