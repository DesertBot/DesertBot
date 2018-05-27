from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class UserLocation(BotCommand):
    def triggers(self):
        return ["addloc", "remloc"]

    def actions(self):
        return super(UserLocation, self).actions() + [("userlocation", 1, self.lookUpLocation)]

    def help(self, query):
        return "Commands: addloc <location>, remloc <location> | Add or remove your location from the database."

    def onLoad(self):
        if "userlocations" not in self.bot.storage or not type(self.bot.storage["userlocations"] == dict):
            self.bot.storage["userlocations"] = {}
        self.locationStorage = self.bot.storage["userlocations"]

    def execute(self, message: IRCMessage):
        if message.command == "addloc":
            if len(message.parameterList) < 1:
                return IRCResponse(ResponseType.Say, "No location was specified.", message.replyTo)
            self.locationStorage[message.user.nick.lower()] = message.parameters
            self.bot.storage["userlocations"] = self.locationStorage
            self.bot.moduleHandler.runGenericAction('userlocation-updated', message.user)
            return IRCResponse(ResponseType.Say, "Your location has been updated.".format(message.parameters),
                               message.replyTo)
        elif message.command == "remloc":
            if message.user.nick.lower() not in self.locationStorage:
                return IRCResponse(ResponseType.Say, "Your location is not registered!", message.replyTo)
            else:
                del self.locationStorage[message.user.nick.lower()]
                self.bot.storage["userlocations"] = self.locationStorage
                self.bot.moduleHandler.runGenericAction('userlocation-removed', message.user)
                return IRCResponse(ResponseType.Say, "Your location has been removed.", message.replyTo)

    def lookUpLocation(self, nick: str):
        if nick.lower() not in self.locationStorage:
            return {
                "success": False,
                "error": "Your location is not registered. Register your location by using the \"addloc\" command "
                         "or provide a location"
            }
        else:
            return {
                "success": True,
                "location": self.locationStorage[nick.lower()]
            }


userLocation = UserLocation()
