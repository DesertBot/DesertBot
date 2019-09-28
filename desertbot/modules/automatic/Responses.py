from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, ignore
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime
import re
from typing import Union

from desertbot.message import IRCMessage
from desertbot.response import ResponseType, IRCResponse


@implementer(IPlugin, IModule)
class Responses(BotCommand):
    def actions(self):
        return super(Responses, self).actions() + [('message-channel', 1, self.respond),
                                                   ('message-user', 1, self.respond),
                                                   ('action-channel', 1, self.respond),
                                                   ('action-user', 1, self.respond)]

    def help(self, query):
        return ('Talkwords from the mouth place'
                ' - response <name> to enable/disable a particular response')

    def onLoad(self):
        try:
            self.responses = ResponseDict()

            for responseName, responseData in self.bot.storage['responses'].items():
                self.responses.add(ResponseObject(responseName,
                                                  responseData['messages'],
                                                  responseData['regexes'],
                                                  responseData['responseType'],
                                                  responseData['enabledByDefault'],
                                                  int(responseData['cooldown']),
                                                  responseData['allRegexesMustMatch']))

        except Exception:
            self.logger.exception("Exception during responses load.")

    @ignore
    def respond(self, message: IRCMessage):
        if message.command:
            return

        triggers = []
        for response in self.responses.dict:
            trig = self.responses.dict[response].trigger(message)
            if isinstance(trig, str):
                trig = [trig]
            try:
                triggers.extend(trig)
            except Exception:
                triggers = triggers
        return triggers

    @ignore
    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            enableds = []
            for param in message.parameterList:
                enableds.append(self.responses.toggle(param, message))
            return enableds
        else:
            enabled = []
            disabled = []
            for name, response in self.responses.dict.items():
                if response.enabled:
                    enabled.append(name)
                else:
                    disabled.append(name)

            enabled = sorted(enabled)
            disabled = sorted(disabled)

            return [IRCResponse(ResponseType.Say,
                                'Enabled responses: {}'.format(', '.join(enabled)),
                                message.replyTo),
                    IRCResponse(ResponseType.Say,
                                'Disabled responses: {}'.format(', '.join(disabled)),
                                message.replyTo)]


class ResponseObject(object):
    lastTriggered = datetime.datetime.min

    def __init__(self, name: str, responseMessages: list, regexes: list, responseType="Say",
                 enabled=True, cooldown=300, regexMustAllMatch=True):
        self.name = name
        self.responseMessages = responseMessages
        self.regexes = regexes
        self.enabled = enabled
        self.cooldown = cooldown
        self.mustAllMatch = regexMustAllMatch
        if responseType.lower() == "say":
            self.responseType = ResponseType.Say
        elif responseType.lower() == "do":
            self.responseType = ResponseType.Do
        elif responseType.lower() == "notice":
            self.responseType = ResponseType.Notice
        elif responseType.lower() == "raw":
            self.responseType = ResponseType.Raw
        else:
            self.responseType = ResponseType.Say

    # check the regexes for this ResponseObject and see if the messageString matches
    def match(self, messageString: str) -> bool:
        for regex in self.regexes:
            # check every regex
            if re.search(regex, messageString, re.IGNORECASE | re.UNICODE):
                # if not all regexes must match, this messageString matches this ResponseObject
                if not self.mustAllMatch:
                    return True
                # otherwise, continue and check remaining regexes
                else:
                    continue
            # if a regexes doesn't match, and all regexes in this ResponseObject must match, return false
            elif self.mustAllMatch:
                return False
        # if we get here, all regexes have matched. Return the value of mustAllMatch.
        return self.mustAllMatch

    # true if this ResponseObject should be triggered by the given messageString
    def shouldTrigger(self, messageString: str) -> bool:
        return (self.enabled and
                (datetime.datetime.utcnow() - self.lastTriggered).seconds >= self.cooldown and
                self.match(messageString))

    # trigger this ResponseObject, if it should be triggered
    def trigger(self, message: IRCMessage) -> Union[list, None]:
        if self.shouldTrigger(message.messageString):
            self.lastTriggered = datetime.datetime.utcnow()
            return self.talkwords(message)

    # toggle this ResponseObject on/off
    def toggle(self, message: IRCMessage) -> IRCResponse:
        self.enabled = not self.enabled
        return IRCResponse(ResponseType.Say, f"Response {self.name!r} {'enabled' if self.enabled else 'disabled'}", message.replyTo)

    # construct and return IRCResponse objects for the responseMessages this ResponseObject has
    def talkwords(self, message: IRCMessage) -> list:
        return [IRCResponse(self.responseType, response, message.replyTo) for response in self.responseMessages]


class ResponseDict(object):
    dict = {}

    def add(self, mbr):
        self.dict[mbr.name] = mbr

    def toggle(self, name: str, chatMessage: IRCMessage):
        if name.lower() in self.dict:
            return self.dict[name.lower()].toggle(chatMessage)
        return


responses = Responses()
