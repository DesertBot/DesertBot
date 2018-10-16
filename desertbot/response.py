from enum import Enum
from typing import Dict


class ResponseType(Enum):
    Say = 1
    Do = 2
    Notice = 3
    Raw = 4


class IRCResponse(object):
    type = ResponseType.Say
    response = ''
    target = ''

    def __init__(self, messageType: ResponseType, response: str, target: str,
                 extraVars: Dict=None, metadata: Dict=None):
        if extraVars is None:
            extraVars = {}
        if metadata is None:
            metadata = {}
        self.type = messageType
        try:
            self.response = str(response, 'utf-8')
        except TypeError:  # Already utf-8?
            self.response = response
        try:
            self.target = str(target, 'utf-8')
        except TypeError:  # Already utf-8?
            self.target = target

        # remove CTCP chars
        if not self.type == ResponseType.Raw:
            self.response = self.response.replace('\x01', '')

        self.ExtraVars = extraVars
        self.Metadata = metadata
