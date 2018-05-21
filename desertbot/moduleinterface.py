# -*- coding: utf-8 -*-

from zope.interface import Interface
from functools import wraps
from fnmatch import fnmatch
from typing import Any, Callable, List, Tuple, TYPE_CHECKING
import logging

from desertbot.message import IRCMessage

if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot


class IModule(Interface):
    def actions() -> List[Tuple[str, int, Callable]]:
        """
        Returns the list of actions this module hooks into.
        Actions are defined as a tuple with the following values:
        (action_name, priority, function)
        action_name (string): The name of the action.
        priority (int):       Actions are handled in order of priority.
                              Leave it at 1 unless you want to override another handler.
        function (reference): A reference to the function in the module that handles this action.
        """

    def onLoad() -> None:
        """
        Called when the module is loaded. Typically loading data, API keys, etc.
        """

    def hookBot(bot: 'DesertBot') -> None:
        """
        Called when the bot is loaded to pass a reference to the bot for later use.
        """

    def displayHelp(query: str, params: Any) -> str:
        """
        Catches help actions, checks if they are for this module, then calls help(query, params)
        """

    def help(query: str, params: Any) -> str:
        """
        Returns help text describing what the module does.
        Takes params as input so you can override with more complex help lookup.
        """

    def onUnload() -> None:
        """
        Called when the module is unloaded. Cleanup, if any.
        """


def ignore(func):
    @wraps(func)
    def wrapped(inst, message):
        if inst.checkIgnoreList(message):
            return
        return func(inst, message)

    return wrapped


class BotModule(object):
    def __init__(self):
        self.logger = logging.getLogger('desertbot.{}'.format(self.__class__.__name__))

    def actions(self) -> List[Tuple[str, int, Callable]]:
        return [('help', 1, self.displayHelp)]

    def onLoad(self) -> None:
        pass

    def hookBot(self, bot: 'DesertBot') -> None:
        self.bot = bot

    def displayHelp(self, query: str) -> str:
        if query[0].lower() == self.__class__.__name__.lower():
            return self.help(query)

    def help(self, query: str) -> str:
        return "This module has no help text"

    def onUnload(self) -> None:
        pass

    def checkIgnoreList(self, message: IRCMessage) -> bool:
        for ignore in self.bot.config.getWithDefault('ignored', []):
            if fnmatch(message.user.fullUserPrefix(), ignore):
                return True
        return False
