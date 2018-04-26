# -*- coding: utf-8 -*-
from desertbot import serverinfo
from typing import Any


class IRCChannel(object):
    def __init__(self, name: str):
        self.Name = name
        self.Topic = ''
        self.TopicSetBy = ''
        self.Users = {}
        self.Ranks = {}
        self.Modes = {}

    def __str__(self):
        return self.Name

    def getHighestStatusOfUser(self, nickname: str) -> Any:
        if not self.Ranks[nickname]:
            return None

        for mode in serverinfo.StatusOrder:
            if mode in self.Ranks[nickname]:
                return mode

        return None
