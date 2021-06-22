"""
Created on Feb 28, 2015

@author: StarlitGhost
"""
import re

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse
from desertbot.utils import dictutils


class UnbalancedBracesException(Exception):
    def __init__(self, message, column):
        # Call the base exception constructor with the params it needs
        super(UnbalancedBracesException, self).__init__(message)
        # Store the message
        self.message = message
        # Store the column position of the unbalanced brace
        self.column = column


class DictMergeError(Exception):
    pass


@implementer(IPlugin, IModule)
class Sub(BotCommand):
    def triggers(self):
        return ['sub']

    def help(self, query):
        return [
            "sub <text> - "
            "executes nested commands in <text> and replaces the commands with their output",
            "syntax: text {command params} more text {command {command params} {command params}}",
            "example: .sub Some {rainbow magical} {flip topsy-turvy} text"]

    def execute(self, message: IRCMessage):
        subString = self._mangleEscapes(message.parameters)

        try:
            segments = list(self._parseSubcommandTree(subString))
        except UnbalancedBracesException as e:
            red = colour(A.bold[A.fg.lightRed['']])
            normal = colour(A.normal[''])
            error = (subString[:e.column]
                     + red + subString[e.column]
                     + normal + subString[e.column+1:])
            error = self._unmangleEscapes(error, False)
            return [
                IRCResponse("Sub Error: {} (column {})".format(e.message, e.column), message.replyTo),
                IRCResponse(error, message.replyTo)]

        prevLevel = -1
        responseStack = []
        metadata = message.metadata

        if 'tracking' in metadata:
            metadata['tracking'].append('Sub')
        else:
            metadata['tracking'] = ['Sub']

        for segment in segments:
            (level, command, start, end) = segment

            # grab the text replace var dict from the metadata, if present
            if 'var' in metadata:
                replaceVars = metadata['var']
            else:
                replaceVars = {}

            # We've finished executing subcommands at the previous depth,
            # so replace subcommands with their output at the current depth
            if level < prevLevel:
                command = self._substituteResponses(command, responseStack, level, replaceVars, start)

            # Replace any replaceVars in the command
            for var, value in replaceVars.items():
                command = re.sub(r'\$\b{}\b'.format(re.escape(var)), '{}'.format(value), command)

            # Build a new message out of this segment
            inputMessage = IRCMessage(message.type, message.user, message.channel,
                                      self.bot.commandChar + command.lstrip(),
                                      self.bot,
                                      metadata=metadata)

            # Execute the constructed message
            if inputMessage.command.lower() in self.bot.moduleHandler.mappedTriggers:
                module = self.bot.moduleHandler.mappedTriggers[inputMessage.command.lower()]
                response = module.execute(inputMessage)
                """@type : IRCResponse"""
            else:
                return IRCResponse("'{}' is not a recognized command trigger"
                                   .format(inputMessage.command), message.replyTo)

            # Push the response onto the stack
            responseStack.append((level, response.response, start, end))
            # merge response metadata back into our sub-global dict
            metadata = dictutils.recursiveMerge(metadata, response.Metadata)
            # update the replaceVars in case this is the outermost segment
            # (and therefore we won't be looping again to pick them up)
            if 'var' in metadata:
                replaceVars = metadata['var']

            prevLevel = level

        responseString = self._substituteResponses(subString, responseStack, -1, replaceVars, -1)
        responseString = self._unmangleEscapes(responseString)
        return IRCResponse(responseString, message.replyTo, metadata=metadata)

    @staticmethod
    def _parseSubcommandTree(string):
        """Parse braced segments in string as tuples (level, contents, start index, end index)."""
        stack = []
        for i, c in enumerate(string):
            if c == '{':
                stack.append(i)
            elif c == '}':
                if stack:
                    start = stack.pop()
                    yield len(stack), string[start + 1: i], start, i
                else:
                    raise UnbalancedBracesException("unbalanced closing brace", i)
        if stack:
            start = stack.pop()
            raise UnbalancedBracesException("unbalanced opening brace", start)

    @staticmethod
    def _substituteResponses(command, responseStack, commandLevel, replaceVars, start):
        # Pop responses off the stack and replace the subcommand that generated them
        while len(responseStack) > 0:
            level, responseString, rStart, rEnd = responseStack.pop()
            if level <= commandLevel:
                responseStack.append((level, responseString, rStart, rEnd))
                break
            cStart = rStart - start - 1
            cEnd = rEnd - start
            # Replace the subcommand with its output
            command = command[:cStart] + responseString + command[cEnd:]

        # Replace any replaceVars generated by functions
        for var, value in replaceVars.items():
            command = re.sub(r'\$\b{}\b'.format(re.escape(var)), '{}'.format(value), command)

        return command

    @staticmethod
    def _mangleEscapes(string):
        # Replace escaped left and right braces with something
        #  that should never show up in messages/responses
        string = re.sub(r'(?<!\\)\\\{', '@LB@', string)
        string = re.sub(r'(?<!\\)\\\}', '@RB@', string)
        return string

    @staticmethod
    def _unmangleEscapes(string, unescape=True):
        if unescape:
            # Replace the mangled escaped braces with unescaped braces
            string = string.replace('@LB@', '{')
            string = string.replace('@RB@', '}')
        else:
            # Just unmangle them, ie, keep the escapes
            string = string.replace('@LB@', '\\{')
            string = string.replace('@RB@', '\\}')
        return string


sub = Sub()
