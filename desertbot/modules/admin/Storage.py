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
        if len(message.parameterList) <= 2:
            return IRCResponse(ResponseType.Say, self.help(["storage"]), message.replyTo)
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
        mh = self.bot.moduleHandler
        moduleNames = [mh.caseMap[name.lower()] for name in message.parameterList[1:] if name.lower() in mh.caseMap]
        for moduleName in moduleNames:
            mh.modules[moduleName].storageSync.stop()

        return IRCResponse(ResponseType.Say,
                           f"Stopped storage sync for modules {', '.join(moduleNames)}. They will no longer periodically autosave to file!",
                           message.replyTo)

    @admin("[Storage] Only my admins may start up my storage sync!")
    def startStorageSync(self, message: IRCMessage):
        mh = self.bot.moduleHandler
        moduleNames = [mh.caseMap[name.lower()] for name in message.parameterList[1:] if name.lower() in mh.caseMap]
        for moduleName in moduleNames:
            # since each module has its own LoopingCall,
            # space them out over a second using random.random() to add 0-1 seconds to each module's storage save interval
            mh.modules[moduleName].storageSync.start(self.bot.config.getWithDefault("storage_save_interval", 60) + random.random(), now=True)
        return IRCResponse(ResponseType.Say,
                           f"Started storage sync for modules {', '.join(moduleNames)}. They will periodically autosave to file.",
                           message.replyTo)

    @admin("[Storage] Only my admins can reload my storage file!")
    def loadStorage(self, message: IRCMessage):
        mh = self.bot.moduleHandler
        moduleNames = [mh.caseMap[name.lower()] for name in message.parameterList[1:] if name.lower() in mh.caseMap]
        for moduleName in moduleNames:
            mh.modules[moduleName].storage.load()
        return IRCResponse(ResponseType.Say,
                           f"Reloaded storage from file for modules {', '.join(moduleNames)}.",
                           message.replyTo)

    @admin("[Storage] Only my admins can save my storage to file!")
    def saveStorage(self, message: IRCMessage):
        mh = self.bot.moduleHandler
        moduleNames = [mh.caseMap[name.lower()] for name in message.parameterList[1:] if name.lower() in mh.caseMap]
        for moduleName in moduleNames:
            mh.modules[moduleName].storage.save()
        return IRCResponse(ResponseType.Say,
                           f"Saved storage to file for modules {', '.join(moduleNames)}.",
                           message.replyTo)


storage = Storage()
