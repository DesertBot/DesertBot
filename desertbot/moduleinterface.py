from twisted.internet.task import LoopingCall
from zope.interface import Interface
from functools import wraps
from fnmatch import fnmatch
import json
import os
import random
from typing import Any, Callable, List, Tuple, Union, TYPE_CHECKING
import logging

from desertbot.message import IRCMessage
from desertbot.datastore import DataStore

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

    def loadDataStore() -> None:
        """
        Called when the module is loaded to create its DataStore object and load data from disk (if it exists)
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
        self.bot = None
        self.storage = None
        self.storageSync = None

        self.loadingPriority = 1
        """
        Increase this number in the module's class if the module should be loaded before other modules.
        """

    def actions(self) -> List[Tuple[str, int, Callable]]:
        return [('help', 1, self.displayHelp)]

    def onLoad(self) -> None:
        pass

    def hookBot(self, bot: 'DesertBot') -> None:
        self.bot = bot

    def loadDataStore(self):
        dataRootPath = os.path.join(self.bot.rootDir, 'data', self.bot.server)
        defaultRootPath = os.path.join(self.bot.rootDir, 'data', 'defaults')

        self.storage = DataStore(storagePath=os.path.join(dataRootPath, f'{self.__class__.__name__}.json'),
                                 defaultsPath=os.path.join(defaultRootPath, f'{self.__class__.__name__}.json'))

        # ensure storage is periodically synced to disk - DataStore.__set__() does call DataStore.save(), but you never know
        self.storageSync = LoopingCall(self.storage.save())
        # since each module has its own LoopingCall,
        # space them out over a second using random.random() to add 0-1 seconds to each module's storage save interval
        self.storageSync.start(self.bot.config.getWithDefault('storage_save_interval', 60) + random.random(), now=False)

    def displayHelp(self, query: Union[List[str], None]) -> str:
        if query is not None and query[0].lower() == self.__class__.__name__.lower():
            return self.help(query)

    def help(self, query: Union[List[str], None]) -> str:
        return 'This module has no help text'

    def onUnload(self) -> None:
        self.storage.save()

    def checkIgnoreList(self, message: IRCMessage) -> bool:
        for ignore in self.bot.config.getWithDefault('ignored', []):
            if fnmatch(message.user.fullUserPrefix(), ignore):
                return True
        return False
