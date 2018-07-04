import logging

from desertbot.ircbase import ModeType
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot
    from desertbot.user import IRCUser


class IRCChannel(object):
    def __init__(self, name: str, bot: 'DesertBot'):
        self.logger = logging.getLogger('desertbot.core.{}'.format(name))
        self.name = name
        self.bot = bot
        self.modes = {}
        self.users = {}
        self.ranks = {}
        self.topic = None
        self.topicSetter = None
        self.topicTimestamp = 0
        self.creationTime = 0
        self.userlistComplete = True

    def setModes(self, modes: str, params: List) -> Optional[Dict]:
        adding = True
        supportedChanModes = self.bot.supportHelper.chanModes
        supportedStatuses = self.bot.supportHelper.statusModes
        modesAdded = []
        paramsAdded = []
        modesRemoved = []
        paramsRemoved = []
        for mode in modes:
            if mode == "+":
                adding = True
            elif mode == "-":
                adding = False
            elif mode not in supportedChanModes and mode not in supportedStatuses:
                self.logger.warning('Received unknown MODE char {} in MODE string {}'.format(mode, modes))
                # We received a mode char that's unknown to use, so we abort parsing to prevent desync.
                return None
            elif mode in supportedStatuses:
                if len(params) < 1:
                    self.logger.warning('Received a broken MODE string for channel {}!'.format(self.name))
                    return {}
                user = params.pop(0)
                if user not in self.users:
                    self.logger.warning("Received status MODE for unknown user {} in channel {}.".format(user, self.name))
                else:
                    if adding:
                        self.ranks[user] += mode
                        modesAdded.append(mode)
                        paramsAdded.append(user)
                    elif not adding and mode in self.ranks[user]:
                        self.ranks[user] = self.ranks[user].replace(mode, "")
                        modesRemoved.append(mode)
                        paramsRemoved.append(user)
            elif supportedChanModes[mode] == ModeType.LIST:
                if len(params) < 1:
                    self.logger.warning('Received a broken MODE string for channel {}!'.format(self.name))
                    return {}
                param = params.pop(0)
                if mode not in self.modes:
                    self.modes[mode] = set()
                if adding:
                    self.modes[mode].add(param)
                    modesAdded.append(mode)
                    paramsAdded.append(param)
                elif not adding and param in self.modes[mode]:
                    self.modes[mode].remove(param)
                    modesRemoved.append(mode)
                    paramsRemoved.append(param)
            elif supportedChanModes[mode] == ModeType.PARAM_SET:
                if adding:
                    if len(params) < 1:
                        self.logger.warning('Received a broken MODE string for channel {}!'.format(self.name))
                        return {}
                    param = params.pop(0)
                    self.modes[mode] = param
                    modesAdded.append(mode)
                    paramsAdded.append(param)
                elif not adding and mode in self.modes:
                    del self.modes[mode]
                    modesRemoved.append(mode)
                    paramsRemoved.append(None)
            elif supportedChanModes[mode] == ModeType.PARAM_SET_UNSET:
                if len(params) < 1:
                    self.logger.warning('Received a broken MODE string for channel {}!'.format(self.name))
                    return {}
                param = params.pop(0)
                if adding:
                    self.modes[mode] = param
                    modesAdded.append(mode)
                    paramsAdded.append(param)
                elif not adding and mode in self.modes:
                    del self.modes[mode]
                    modesRemoved.append(mode)
                    paramsRemoved.append(param)
            elif supportedChanModes[mode] == ModeType.NO_PARAM:
                if adding:
                    self.modes[mode] = None
                    modesAdded.append(mode)
                    paramsAdded.append(None)
                elif not adding and mode in self.modes:
                    del self.modes[mode]
                    modesRemoved.append(mode)
                    paramsRemoved.append(None)
        return {
            "added": modesAdded,
            "removed": modesRemoved,
            "addedParams": paramsAdded,
            "removedParams": paramsRemoved
        }

    def getHighestStatusOfUser(self, user: 'IRCUser') -> str:
        if user.nick not in self.ranks:
            return ""

        for status in self.bot.supportHelper.statusOrder:
            if status in self.ranks[user.nick]:
                return self.bot.supportHelper.statusModes[status]
        return ""

    def userIsChanOp(self, user: 'IRCUser') -> bool:
        if user.nick not in self.ranks:
            return False

        for status in self.bot.supportHelper.statusModes:
            if status in self.ranks[user.nick]:
                return True
            if status == "o":  # We consider anyone with +o or higher to be an op
                break

        return False

    def __str__(self):
        return self.name
