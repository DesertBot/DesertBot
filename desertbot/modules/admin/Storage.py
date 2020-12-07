from zope.interface import implementer
from twisted.plugin import IPlugin

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import admin, BotCommand
from desertbot.response import IRCResponse, ResponseType

import random


@implementer(IPlugin, IModule)
class Storage(BotCommand):
    def triggers(self):
        return ["storage"]

    def actions(self):
        return super(Storage, self).actions() + [("storage-load", 1, self.loadStorage),
                                                 ("storage-save", 1, self.saveStorage)]

    def help(self, query):
        helpDict = {
            "storage": f"{self.bot.commandChar}storage stopsync/startsync/load/save <modulename> - Manage bot storage files.",
            "stopsync": f"{self.bot.commandChar}storage stopsync <modulename> - Halts the periodic autosave for the specified modules storage file.",
            "startsync": f"{self.bot.commandChar}storage startsync <modulename> - Start periodic autosave for the specified modules storage file.",
            "load": f"{self.bot.commandChar}storage load <modulename> - Manually load the specified modules storage from file.",
            "save": f"{self.bot.commandChar}storage save <modulename> - Manually save the specified modules storage to file."
        }
        if len(query) > 1 and query[1].lower() in helpDict:
            return helpDict[query[1].lower()]
        else:
            return f"{self.bot.commandChar}storage stopsync/startsync/load/save <modulename> - Manage bot storage files."

    def execute(self, message: IRCMessage):
        if len(message.parameterList) < 2:
            return IRCResponse(self.help(["storage"]), message.replyTo)
        else:
            subcommand = message.parameterList[0].lower()
            if subcommand == "stopsync":
                return self.stopStorageSync(message)
            elif subcommand == "startsync":
                return self.startStorageSync(message)
            elif subcommand == "load":
                return self.loadStorage(message)
            elif subcommand == "save":
                return self.saveStorage(message)

    @admin("[Storage] Only my admins may stop my storage sync!")
    def stopStorageSync(self, message: IRCMessage):
        moduleNames = self._getValidModuleNames(message.parameterList[1:])
        for moduleName in moduleNames:
            self._stopDataSync(moduleName)
        return IRCResponse(
            f"Stopped storage sync for modules {', '.join(moduleNames)}. They will no longer periodically autosave to file!",
            message.replyTo)

    @admin("[Storage] Only my admins may start up my storage sync!")
    def startStorageSync(self, message: IRCMessage):
        moduleNames = self._getValidModuleNames(message.parameterList[1:])
        for moduleName in moduleNames:
            self._startDataSync(moduleName)
        return IRCResponse(
            f"Started storage sync for modules {', '.join(moduleNames)}. They will periodically autosave to file.",
            message.replyTo)

    @admin("[Storage] Only my admins can reload my storage file!")
    def loadStorage(self, message: IRCMessage):
        moduleNames = self._getValidModuleNames(message.parameterList[1:])
        for moduleName in moduleNames:
            self._loadModuleData(moduleName)
        return IRCResponse(f"Reloaded storage from file for modules {', '.join(moduleNames)}.", message.replyTo)

    @admin("[Storage] Only my admins can save my storage to file!")
    def saveStorage(self, message: IRCMessage):
        moduleNames = self._getValidModuleNames(message.parameterList[1:])
        for moduleName in moduleNames:
            self._saveModuleData(moduleName)
        return IRCResponse(f"Saved storage to file for modules {', '.join(moduleNames)}.", message.replyTo)

    def _getValidModuleNames(self, parameterList):
        """
        Given a list of module names, returns Properly Capitalized names for those modules, if they are loaded.
        """
        return [self.bot.moduleHandler.caseMap[name.lower()] for name in parameterList if name.lower() in self.bot.moduleHandler.caseMap]

    def _startDataSync(self, moduleName):
        """
        Given a valid, Proper Caps module name, enable storage sync for that module
        """
        # since each module has its own LoopingCall,
        # space them out over a second using random.random() to add 0-1 seconds to each module's storage save interval
        saveInterval = self.bot.config.getWithDefault("storage_save_interval", 60) + random.random()
        self.bot.moduleHandler.modules[moduleName].storageSync.start(saveInterval, now=True)

    def _stopDataSync(self, moduleName):
        """
        Given a valid, Proper Caps module name, disable storage sync for that module
        """
        self.bot.moduleHandler.modules[moduleName].storageSync.stop()

    def _saveModuleData(self, moduleName):
        """
        Given a valid, Proper Caps module name, immediately save that module's data to disk
        """
        self.bot.moduleHandler.modules[moduleName].storage.save()

    def _loadModuleData(self, moduleName):
        """
        Given a valid, Proper Caps module name, immediately load that module's data from disk
        """
        self.bot.moduleHandler.modules[moduleName].storage.load()


storage = Storage()
