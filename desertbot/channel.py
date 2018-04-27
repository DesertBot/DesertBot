# -*- coding: utf-8 -*-
from desertbot import serverinfo
from typing import Any


class IRCChannel(object):
    def __init__(self, name: str):
        self.name = name
        self.topic = ''
        self.topicSetBy = ''
        self.users = {}
        self.ranks = {}
        self.modes = {}

    def __str__(self):
        return self.name

    def getHighestStatusOfUser(self, nickname: str) -> Any:
        if not self.ranks[nickname]:
            return None

        for mode in serverinfo.statusOrder:
            if mode in self.ranks[nickname]:
                return mode

        return None
