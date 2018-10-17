from enum import Enum
import importlib
import inspect
import logging
import os

from twisted.plugin import getPlugins
from twisted.python.rebuild import rebuild
from twisted.internet import threads
from twisted.internet import reactor

from desertbot.moduleinterface import IModule
import desertbot.modules
from desertbot.message import IRCMessage, TargetTypes
from desertbot.response import ResponseType

from typing import Any, List, TYPE_CHECKING
if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot


class ModuleHandler(object):
    def __init__(self, bot: 'DesertBot'):
        self.bot = bot
        self.logger = logging.getLogger('desertbot.modulehandler')

        self.modules = {}
        self.caseMap = {}
        self.fileMap = {}
        self.actions = {}
        self.mappedTriggers = {}

    def loadModule(self, name: str, rebuild_: bool=True) -> str:
        for module in getPlugins(IModule, desertbot.modules):
            if module.__class__.__name__ and module.__class__.__name__.lower() == name.lower():
                if rebuild_:
                    rebuild(importlib.import_module(module.__module__))
                self._loadModuleData(module)

                self.logger.info('Module {} loaded'.format(module.__class__.__name__))

                return module.__class__.__name__

    def _loadModuleData(self, module: Any) -> None:
        if not IModule.providedBy(module):
            raise ModuleLoaderError(module.__class__.__name__,
                                    "Module doesn't implement the module interface.",
                                    ModuleLoadType.LOAD)
        if module.__class__.__name__ in self.modules:
            raise ModuleLoaderError(module.__class__.__name__,
                                    "Module is already loaded.",
                                    ModuleLoadType.LOAD)

        module.hookBot(self.bot)

        # do this before loading actions or triggers, in case the
        # module wants to do anything to them
        module.onLoad()

        actions = {}
        for action in module.actions():
            if action[0] not in actions:
                actions[action[0]] = [(action[2], action[1])]
            else:
                actions[action[0]].append((action[2], action[1]))

        for action, actionList in actions.items():
            if action not in self.actions:
                self.actions[action] = []
            for actionData in actionList:
                for index, handlerData in enumerate(self.actions[action]):
                    if actionData[1] > handlerData[1]:
                        self.actions[action].insert(index, actionData)
                        break
                else:
                    self.actions[action].append(actionData)

        # map triggers to modules so we can call them via dict lookup
        if hasattr(module, 'triggers'):
            for trigger in module.triggers():
                self.mappedTriggers[trigger] = module

        className = module.__class__.__name__
        fileName = inspect.getsourcefile(module.__class__).split(os.path.sep)[-1]
        self.modules.update({className: module})
        self.fileMap.update({fileName: className})
        self.caseMap.update({className.lower(): className})

    def unloadModule(self, name: str) -> str:
        if name.lower() not in self.caseMap:
            raise ModuleLoaderError(name, "The module is not loaded.", ModuleLoadType.UNLOAD)

        name = self.caseMap[name.lower()]

        for action in self.modules[name].actions():
            self.actions[action[0]].remove((action[2], action[1]))

        # unmap module triggers
        if hasattr(self.modules[name], 'triggers'):
            for trigger in self.modules[name].triggers():
                del self.mappedTriggers[trigger]

        # do this after removing actions and triggers,
        # so the module can't leave some dangling
        self.modules[name].onUnload()

        del self.modules[name]
        for k, v in list(self.fileMap.items()):
            if v.lower() == name.lower():
                del self.fileMap[k]
        del self.caseMap[name.lower()]

        self.logger.info('Module {} unloaded'.format(name))

        return name

    def reloadModule(self, name: str) -> str:
        self.unloadModule(name)
        return self.loadModule(name)

    def sendPRIVMSG(self, message: str, destination: str) -> None:
        self.bot.output.cmdPRIVMSG(destination, message)

    def handleMessage(self, message: IRCMessage) -> None:
        isChannel = message.targetType == TargetTypes.CHANNEL
        typeActionMap = {
            "PRIVMSG": lambda: "message-channel" if isChannel else "message-user",
            "ACTION": lambda: "action-channel" if isChannel else "action-user",
            "NOTICE": lambda: "notice-channel" if isChannel else "notice-user",
            "JOIN": lambda: "channeljoin",
            "INVITE": lambda: "channelinvite",
            "PART": lambda: "channelpart",
            "KICK": lambda: "channelkick",
            "QUIT": lambda: "userquit",
            "NICK": lambda: "usernick",
            "MODE": lambda: "modeschanged-channel" if isChannel else "modeschanged-user",
            "TOPIC": lambda: "channeltopic",
            "CTCP": lambda: "ctcp-channel" if isChannel else "ctcp-user",
            "001": lambda: "welcome",
            "324": lambda: "modes-channel"
        }
        action = typeActionMap[message.type]()
        # fire off a thread for every incoming message
        d = threads.deferToThread(self.runGatheringAction, action, message)
        d.addCallback(self.sendResponses)
        d.addErrback(self._deferredError)

    def sendResponses(self, responses: List) -> None:
        typeActionMap = {
            ResponseType.Say: "response-message",
            ResponseType.Do: "response-action",
            ResponseType.Notice: "response-notice",
            ResponseType.Raw: "response-",
        }
        for response in responses:
            if not response or not response.response:
                continue

            action = typeActionMap[response.type]
            if response.type == ResponseType.Raw:
                action += response.response.split()[0].lower()
            self.runProcessingAction(action, response)

            try:
                if response.type == ResponseType.Say:
                    self.bot.output.cmdPRIVMSG(response.target, response.response)
                elif response.type == ResponseType.Do:
                    self.bot.output.ctcpACTION(response.target, response.response)
                elif response.type == ResponseType.Notice:
                    self.bot.output.cmdNOTICE(response.target, response.response)
                elif response.type == ResponseType.Raw:
                    self.bot.sendMessage(response.response)
            except Exception as e:
                # ^ dirty, but we don't want any modules to kill the bot
                self.logger.exception("Python Execution Error sending responses {!r}"
                                      .format(responses))
                # if we're in debug mode, let the exception kill the bot
                if self.bot.logLevel == logging.DEBUG:
                    raise e

    def _deferredError(self, error):
        self.logger.exception("Python Execution Error in deferred call {!r}".format(error))
        self.logger.exception(error)
        # if we're in debug mode, let the exception kill the bot
        if self.bot.logLevel == logging.DEBUG:
            # we can't just re-raise because twisted will eat the deferred error
            self.bot.factory.exitStatus = 1
            reactor.stop()

    def loadAll(self) -> None:
        configModulesToLoad = self.bot.config.getWithDefault('modules', ['all'])
        modulesToLoad = set()
        if 'all' in configModulesToLoad:
            modulesToLoad.update(set(
                [module.__class__.__name__ for module in getPlugins(IModule, desertbot.modules)]
                ))

        for module in configModulesToLoad:
            if module == 'all':
                continue
            elif module.startswith('-'):
                modulesToLoad.remove(module[1:])
            else:
                modulesToLoad.add(module)

        for module in modulesToLoad:
            try:
                self.loadModule(module, rebuild_=False)
            except Exception as e:
                # ^ dirty, but we don't want any modules to kill the bot
                self.logger.exception("Exception when loading module {!r}".format(module))
                # if we're in debug mode, let the exception kill the bot
                if self.bot.logLevel == logging.DEBUG:
                    raise e

    def runGenericAction(self, actionName: str, *params: Any, **kw: Any) -> None:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        for action in actionList:
            action[0](*params, **kw)

    def runProcessingAction(self, actionName: str, data: Any, *params: Any, **kw: Any) -> None:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        for action in actionList:
            action[0](data, *params, **kw)
            if not data:
                return

    def runGatheringAction(self, actionName: str, *params: Any, **kw: Any) -> List:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        responses = []
        for action in actionList:
            response = action[0](*params, **kw)
            if not response:
                continue
            if isinstance(response, list):
                responses.extend(response)
            else:
                responses.append(response)

        return responses

    def runActionUntilTrue(self, actionName: str, *params: Any, **kw: Any) -> bool:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        for action in actionList:
            if action[0](*params, **kw):
                return True
        return False

    def runActionUntilFalse(self, actionName: str, *params: Any, **kw: Any) -> bool:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        for action in actionList:
            if not action[0](*params, **kw):
                return True
        return False

    def runActionUntilValue(self, actionName: str, *params: Any, **kw: Any) -> Any:
        actionList = []
        if actionName in self.actions:
            actionList = self.actions[actionName]
        for action in actionList:
            value = action[0](*params, **kw)
            if value:
                return value
        return None


class ModuleLoadType(Enum):
    LOAD = 0
    UNLOAD = 1


class ModuleLoaderError(Exception):
    def __init__(self, module, message, loadType):
        self.module = module
        self.message = message
        self.loadType = loadType

    def __str__(self):
        if self.loadType == ModuleLoadType.LOAD:
            return "Module {} could not be loaded: {}".format(self.module, self.message)
        elif self.loadType == ModuleLoadType.UNLOAD:
            return "Module {} could not be unloaded: {}".format(self.module, self.message)
        elif self.loadType == ModuleLoadType.ENABLE:
            return "Module {} could not be enabled: {}".format(self.module, self.message)
        elif self.loadType == ModuleLoadType.DISABLE:
            return "Module {} could not be disabled: {}".format(self.module, self.message)
        return "Error: {}".format(self.message)
