from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, ignore
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime
import re
from typing import List, Union

from desertbot.message import IRCMessage
from desertbot.response import ResponseType, IRCResponse


@implementer(IPlugin, IModule)
class Responses(BotCommand):
    def triggers(self):
        return ["responses"]

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
            self.responses = dict()

            for responseName, responseData in self.storage.items():
                self.responses[responseName] = ResponseObject(responseName,
                                                              responseData['messages'],
                                                              responseData['regexes'],
                                                              responseData['responseType'],
                                                              responseData['enabledByDefault'],
                                                              int(responseData['cooldown']),
                                                              responseData['allRegexesMustMatch'])

        except Exception:
            self.logger.exception("Exception during responses load.")

    @ignore
    def respond(self, message: IRCMessage):
        if message.command:
            return

        triggeredResponses = []
        # each message should only trigger one response really, but there might be future cases where we want multiple
        for responseObject in self.responses.values():
            responseTrigger = responseObject.trigger(message)
            # responseTrigger will be None if the current message didn't trigger the response in question
            if responseTrigger is not None:
                # .trigger() should always return a list of IRCResponse objects, but if there are typos in the datastore it might be a str or IRCResponse object instead
                # wrap the return in a list if so
                if not isinstance(responseTrigger, list):
                    responseTrigger = [responseTrigger]
                try:
                    triggeredResponses.extend(responseTrigger)
                except Exception:
                    self.logger.exception(f"Exception occurred when trying to trigger response {responseObject.name}")
                    triggeredResponses = triggeredResponses
        return triggeredResponses

    @ignore
    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            # on a !responses command followed by some parameters, assume the parameters are ResponseObject names
            # try toggling each and return the resulting IRCResponse objects showing the new status of the matching ResponseObjects
            # .toggle() doesn't return anything if the param given to it is not a valid name for a loaded ResponseObject
            enableds = []
            for param in message.parameterList:
                for responseName, responseObject in self.responses.items():
                    if param.lower() == responseName.lower():
                        enableds.append(responseObject.toggle(message))
            return enableds
        else:
            # on a !responses command, return sorted lists of currently enabled and disabled responses
            enabled = []
            disabled = []
            for name, response in self.responses.items():
                if response.enabled:
                    enabled.append(name)
                else:
                    disabled.append(name)

            enabled = sorted(enabled)
            disabled = sorted(disabled)

            return [IRCResponse('Enabled responses: {}'.format(', '.join(enabled)), message.replyTo),
                    IRCResponse('Disabled responses: {}'.format(', '.join(disabled)), message.replyTo)]


class ResponseObject(object):
    lastTriggered = datetime.datetime.min

    def __init__(self, name: str, responseMessages: List[str], regexes: List[str], responseType="Say",
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
    def trigger(self, message: IRCMessage) -> Union[List[IRCResponse], None]:
        if self.shouldTrigger(message.messageString):
            self.lastTriggered = datetime.datetime.utcnow()
            return self.talkwords(message)

    # toggle this ResponseObject on/off in response to an IRCMessage
    def toggle(self, message: IRCMessage) -> IRCResponse:
        self.enabled = not self.enabled
        return IRCResponse(f"Response {self.name!r} {'enabled' if self.enabled else 'disabled'}", message.replyTo)

    # construct and return IRCResponse objects for the responseMessages this ResponseObject has
    def talkwords(self, message: IRCMessage) -> List[IRCResponse]:
        return [IRCResponse(response, message.replyTo, self.responseType) for response in self.responseMessages]


responses = Responses()
