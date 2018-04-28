# -*- coding: utf-8 -*-
"""
Created on May 03, 2014

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import re
from builtins import str
from six import iteritems

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from desertbot.utils import string


@implementer(IPlugin, IModule)
class Chain(BotCommand):
    def triggers(self):
        return ['chain']

    def help(self, query):
        return 'chain <command 1> | <command 2> [| <command n>] - chains multiple commands together, feeding the output of each command into the next\n' \
           'syntax: command1 params | command2 $output | command3 $var\n' \
           '$output is the output text of the previous command in the chain\n' \
           '$var is any extra var that may have been added to the message by commands earlier in the chain'

    def execute(self, message: IRCMessage):
        # split on unescaped |
        chain = re.split(r'(?<!\\)\|', message.parameters)

        response = None
        extraVars = {}

        for link in chain:
            link = link.strip()
            link = re.sub(r'\\\|', r'|', link)
            if response is not None:
                if hasattr(response, '__iter__'):
                    return IRCResponse(ResponseType.Say,
                                       u"Chain Error: segment before '{}' returned a list".format(link),
                                       message.replyTo)
                link = link.replace('$output', response.response)  # replace $output with output of previous command
                extraVars.update(response.ExtraVars)
                for var, value in iteritems(extraVars):
                    link = re.sub(r'\$\b{}\b'.format(re.escape(var)), '{}'.format(value), link)
            else:
                # replace $output with empty string if previous command had no output
                # (or this is the first command in the chain, but for some reason has $output as a param)
                link = link.replace('$output', '')
            
            link = link.replace('$sender', message.user.name)
            if message.channel is not None:
                link = link.replace('$channel', message.channel.name)
            else:
                link = link.replace('$channel', message.user.name)

            # build a new message out of this 'link' in the chain
            inputMessage = IRCMessage(message.type, message.user.string, message.channel,
                                      self.bot.commandChar + link.lstrip(),
                                      self.bot)
            inputMessage.chained = True  # might be used at some point to tell commands they're being called from Chain

            if inputMessage.command.lower() in self.bot.moduleHandler.mappedTriggers:
                response = self.bot.moduleHandler.mappedTriggers[inputMessage.command.lower()].execute(inputMessage)
            else:
                return IRCResponse(ResponseType.Say,
                                   "'{0}' is not a recognized command trigger".format(inputMessage.command),
                                   message.replyTo)

        if response.response is not None:
            # limit response length (chains can get pretty large)
            response.response = list(string.splitUTF8(response.response.encode('utf-8'), 700))[0]
            response.response = str(response.response, 'utf-8')
        return response


chain = Chain()
