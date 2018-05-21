# -*- coding: utf-8 -*-
from enum import Enum
from typing import Dict, Optional, TYPE_CHECKING
import re

from desertbot.user import IRCUser
from desertbot.channel import IRCChannel

if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot


class TargetTypes(Enum):
    CHANNEL = 1
    USER = 2
            

class IRCMessage(object):
    def __init__(self, msgType: str, user: IRCUser, channel: Optional[IRCChannel], message: str, bot: DesertBot, metadata: Dict=None):
        if metadata is None:
            metadata = {}
        self.metadata = metadata

        if isinstance(message, bytes):
            unicodeMessage = message.decode('utf-8', 'ignore')
        else:  # Already utf-8?
            unicodeMessage = message
        self.type = msgType
        self.messageList = unicodeMessage.strip().split(' ')
        self.messageString = unicodeMessage
        self.user = user

        self.channel = None
        if channel is None:
            self.replyTo = self.user.nick
            self.targetType = TargetTypes.USER
        else:
            self.channel = channel
            # I would like to set this to the channel object but I would probably break functionality if I did :I
            self.replyTo = channel.name
            self.targetType = TargetTypes.CHANNEL

        self.command = ''
        self.parameters = ''
        self.parameterList = []

        if self.messageList[0].startswith(bot.commandChar):
            self.command = self.messageList[0][len(bot.commandChar):]
            if self.command == '':
                self.command = self.messageList[1]
                self.parameters = u' '.join(self.messageList[2:])
            else:
                self.parameters = u' '.join(self.messageList[1:])
        elif re.match('{}[:,]?'.format(re.escape(bot.nick)), self.messageList[0], re.IGNORECASE):
            if len(self.messageList) > 1:
                self.command = self.messageList[1]
                self.parameters = u' '.join(self.messageList[2:])

        if self.parameters.strip():
            self.parameterList = self.parameters.split(' ')

            self.parameterList = [param for param in self.parameterList if param != '']

            if len(self.parameterList) == 1 and not self.parameterList[0]:
                self.parameterList = []
