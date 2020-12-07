"""
Created on Aug 14, 2013

@author: StarlitGhost
"""
import random

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class EightBall(BotCommand):
    def triggers(self):
        return ['8ball', 'eightball']

    def help(self, query):
        return '8ball (question) - swirls a magic 8-ball to give you the answer to your questions'

    def execute(self, message: IRCMessage):
        answers = ['It is certain',  # positive
                   'It is decidedly so',
                   'Without a doubt',
                   'Yes definitely',
                   'You may rely on it',
                   'As I see it yes',
                   'Most likely',
                   'Outlook good',
                   'Yes',
                   'Signs point to yes',

                   'Reply hazy try again',  # non-committal
                   'Ask again later',
                   'Better not tell you now',
                   'Cannot predict now',
                   'Concentrate and ask again',

                   "Don't count on it",  # negative
                   'My reply is no',
                   'My sources say no',
                   'Outlook not so good',
                   'Very doubtful']

        return IRCResponse('The Magic 8-ball says... {}'.format(random.choice(answers)), message.replyTo)


eightball = EightBall()
