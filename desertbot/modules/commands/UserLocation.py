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

    def execute(self, message: IRCMessage):
        if message.command == "addloc":
            if len(message.parameterList) < 1:
                return IRCResponse("No location was specified.", message.replyTo)
            self.storage[message.user.nick.lower()] = message.parameters
            self.bot.moduleHandler.runGenericAction('userlocation-updated', message.user.nick, message.parameters)
            return IRCResponse("Your location has been updated.", message.replyTo)
        elif message.command == "remloc":
            if message.user.nick.lower() not in self.storage:
                return IRCResponse("Your location is not registered!", message.replyTo)
            else:
                del self.storage[message.user.nick.lower()]
                self.bot.moduleHandler.runGenericAction('userlocation-removed', message.user.nick)
                return IRCResponse("Your location has been removed.", message.replyTo)

    def lookUpLocation(self, nick: str):
        if nick.lower() not in self.storage:
            return {
                "success": False,
                "error": "Your location is not registered. Register your location by using the \"addloc\" command "
                         "or provide a location"
            }
        else:
            return {
                "success": True,
                "location": self.storage[nick.lower()]
            }


userLocation = UserLocation()
