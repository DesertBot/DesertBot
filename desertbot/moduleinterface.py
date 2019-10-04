from twisted.internet.task import LoopingCall
from zope.interface import Interface
from functools import wraps
from fnmatch import fnmatch
import json
import os
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

        if os.path.exists(os.path.join(dataRootPath, 'desertbot.json')):
            self.storage = self.getLegacyData(dataRootPath, defaultRootPath)
        else:
            self.storage = DataStore(storagePath=os.path.join(dataRootPath, f'{self.__class__.__name__}.json'),
                                     defaultsPath=os.path.join(defaultRootPath, f'{self.__class__.__name__}.json'))

        # ensure storage is periodically synced to disk - DataStore.__set__() does call DataStore.save(), but you never know
        self.storageSync = LoopingCall(self.storage.save())
        self.storageSync.start(self.bot.config.getWithDefault('storage_save_interval', 60), now=False)

    def getLegacyData(self, dataRootPath, defaultRootPath) -> DataStore:
        """
        Hacky as heck, delete ASAP, remove from fabric of universe
        """
        legacyData = DataStore(storagePath=os.path.join(dataRootPath, 'desertbot.json'),
                               defaultsPath='')
        className = self.__class__.__name__

        # default values, if none of the below if/elif statements apply
        data = dict()
        dataPath = os.path.join(dataRootPath, f'{className}.json')

        if className == 'Lists':
            # Lists module wants per-server storage
            data = dict(legacyData.get("lists", {}))
            dataPath = os.path.join(dataRootPath, 'Lists.json')
        elif className == 'Pronouns':
            # Pronouns module wants per-server storage
            data = dict(legacyData.get("pronouns", {}))
            dataPath = os.path.join(dataRootPath, 'Pronouns.json')
        elif className == 'UserLocation':
            # UserLocation module wants per-server storage
            data = dict(legacyData.get("userlocations", {}))
            dataPath = os.path.join(dataRootPath, 'UserLocation.json')
        elif className == 'RSS':
            # RSS module wants per-server storage
            data = {
                'rss_feeds': dict(legacyData.get('rss_feeds', {})),
                'rss_channels': list(legacyData.get('rss_channels', []))
            }
            dataPath = os.path.join(dataRootPath, 'RSS.json')
        elif className == 'Tell':
            # Tell module wants per-server storage
            data = {
                'tells': list(legacyData.get('tells', []))
            }
            dataPath = os.path.join(dataRootPath, 'Tell.json')
        elif className == 'FFXIV':
            # FFXIV module wants per-server storage
            if 'ffxiv' in legacyData:
                data = {
                    "chars": dict(legacyData['ffxiv'].get('chars', {}))
                }
            dataPath = os.path.join(dataRootPath, 'FFXIV.json')
        elif className == 'Boops':
            # Boops module does not want per-server storage
            data = {
                'boops': list(legacyData.get('boops', []))
            }
            dataPath = os.path.join(defaultRootPath, 'Boops.json')
        elif className == 'Animals':
            # Animals module does not want per-server storage
            data = {
                'animals': dict(legacyData.get('animals', {})),
                'animalCustomReactions': dict(legacyData.get('animalCustomReactions', {}))
            }
            dataPath = os.path.join(defaultRootPath, 'Animals.json')
        elif className == 'Responses':
            # Responses does not want per-server storage
            data = dict(legacyData.get('responses', {}))
            dataPath = os.path.join(defaultRootPath, 'Responses.json')
        elif className == 'Trigger':
            # Trigger does want per-server storage
            data = dict(legacyData.get('triggers', {}))
            dataPath = os.path.join(dataRootPath, 'Trigger.json')

        # write data to dataPath if data is not empty
        if len(data) > 0:
            os.makedirs(os.path.dirname(dataPath), exist_ok=True)
            with open(dataPath, 'w') as storageFile:
                storageFile.write(json.dumps(data, indent=4))

        # proper data file SHOULD now exist at storagePath or defaultsPath for the various modules, in the positions they expect to be found.
        return DataStore(storagePath=os.path.join(dataRootPath, f'{self.__class__.__name__}.json'),
                         defaultsPath=os.path.join(defaultRootPath, f'{self.__class__.__name__}.json'))

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
