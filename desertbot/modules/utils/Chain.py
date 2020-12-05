"""
Created on May 03, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

from desertbot.utils import string, dictutils


@implementer(IPlugin, IModule)
class Chain(BotCommand):
    def triggers(self):
        return ['chain']

    def help(self, query):
        return ['chain <command 1> | <command 2> [| <command n>] -'
                ' chains multiple commands together,'
                ' feeding the output of each command into the next',
                'syntax: command1 params | command2 $output | command3 $var',
                '$output is the output text of the previous command in the chain',
                '$var is any extra var that may have been added'
                ' to the message by commands earlier in the chain']

    def execute(self, message: IRCMessage):
        # split on unescaped |
        chain = re.split(r'(?<!\\)\|', message.parameters)

        response = None
        metadata = {}

        for link in chain:
            link = link.strip()
            link = re.sub(r'\\\|', r'|', link)
            if response is not None:
                if hasattr(response, '__iter__'):
                    return IRCResponse(ResponseType.Say,
                                       "Chain Error: segment before '{}' returned a list"
                                       .format(link),
                                       message.replyTo)
                # replace $output with output of previous command
                link = link.replace('$output', response.response)
                # merge response metadata back into our chain-global dict
                metadata = dictutils.recursiveMerge(metadata, response.Metadata)
                # replace any vars in the command
                if 'var' in metadata:
                    for var, value in metadata['var'].items():
                        link = re.sub(r'\$\b{}\b'.format(re.escape(var)), '{}'.format(value), link)
            else:
                # replace $output with empty string if previous command had no output
                # (or this is the first command in the chain,
                #  but for some reason has $output as a param)
                link = link.replace('$output', '')

            link = link.replace('$sender', message.user.nick)
            if message.channel is not None:
                link = link.replace('$channel', message.channel.name)
            else:
                link = link.replace('$channel', message.user.nick)

            # build a new message out of this 'link' in the chain
            inputMessage = IRCMessage(message.type, message.user, message.channel,
                                      self.bot.commandChar + link.lstrip(),
                                      self.bot, metadata=metadata)
            # might be used at some point to tell commands they're being called from Chain
            inputMessage.chained = True

            if inputMessage.command.lower() in self.bot.moduleHandler.mappedTriggers:
                command = self.bot.moduleHandler.mappedTriggers[inputMessage.command.lower()]
                response = command.execute(inputMessage)
            else:
                return IRCResponse(ResponseType.Say,
                                   "{!r} is not a recognized command trigger"
                                   .format(inputMessage.command),
                                   message.replyTo)

        if response.response is not None:
            # limit response length (chains can get pretty large)
            response.response = list(string.splitUTF8(response.response.encode('utf-8'), 700))[0]
            response.response = str(response.response, 'utf-8')
        return response


chain = Chain()
