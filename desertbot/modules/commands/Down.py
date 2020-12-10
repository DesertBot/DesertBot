from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse

import requests


@implementer(IPlugin, IModule)
class Down(BotCommand):
    def triggers(self):
        return ['down']

    def help(self, query):
        return 'down <url> - Check if the specified website URL is up'

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse("You didn't give me a URL to check!", message.replyTo)

        res = requests.get(message.parameterList[0])

        if res.ok:
            return IRCResponse(f"{message.parameterList[0]} looks up to me! It returned {res.status_code}.", message.replyTo)
        else:
            return IRCResponse(f"{message.parameterList[0]} looks to be down! It returned {res.status_code}.", message.replyTo)


down = Down()
