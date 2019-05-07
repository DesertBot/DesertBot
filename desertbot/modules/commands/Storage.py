from zope.interface import implementer
from twisted.plugin import IPlugin

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import admin, BotCommand
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Storage(BotCommand):
    def triggers(self):
        return ["storage"]

    def actions(self):
        return super(Storage, self).actions() + [("storage-load", 1, self.loadStorage),
                                                 ("storage-save", 1, self.saveStorage)]

    def help(self, query):
        helpDict = {
            "storage": f"{self.bot.commandChar}storage stopsync/startsync/load/save - Manage bot storage file.",
            "stopsync": f"{self.bot.commandChar}storage stopsync - Halts the periodic autosave for the bot's storage file.",
            "startsync": f"{self.bot.commandChar}storage startsync - Start periodic autosave for the bot's storage file.",
            "load": f"{self.bot.commandChar}storage load - Manually load the bot's storage from file.",
            "save": f"{self.bot.commandChar}storage save - Manually save the bot's storage to file."
        }
        if len(query) > 1 and query[1].lower() in helpDict:
            return helpDict[query[1].lower()]
        else:
            return f"{self.bot.commandChar}storage stopsync/startsync/load/save - Manage bot storage file."

    def execute(self, message: IRCMessage):
        if len(message.parameterList) != 1:
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
        self.bot.storageSync.stop()
        return IRCResponse(ResponseType.Say,
                           "Stopped storage sync. Storage will no longer periodically autosave to file!",
                           message.replyTo)

    @admin("[Storage] Only my admins may start up my storage sync!")
    def startStorageSync(self, message: IRCMessage):
        self.bot.storageSync.start(self.bot.config.getWithDefault("storage_save_interval", 60), now=False)
        return IRCResponse(ResponseType.Say,
                           "Started storage sync. Storage will periodically autosave to file.",
                           message.replyTo)

    @admin("[Storage] Only my admins can reload my storage file!")
    def loadStorage(self, message: IRCMessage):
        self.bot.storage.load()
        return IRCResponse(ResponseType.Say, "Reloaded bot storage from file.", message.replyTo)

    @admin("[Storage] Only my admins can save my storage to file!")
    def saveStorage(self, message: IRCMessage):
        self.bot.storage.save()
        return IRCResponse(ResponseType.Say, "Saved bot storage to file.", message.replyTo)


storage = Storage()
