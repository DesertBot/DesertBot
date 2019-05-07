from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType
from typing import Union
from zope.interface import implementer


@implementer(IPlugin, IModule)
class Chatmap(BotCommand):
    chatmapBaseUrl = "https://chatmap.raptorpond.com/"

    def triggers(self):
        return ["chatmap", "addmap", "remmap"]

    def help(self, query: Union[str, None]) -> str:
        return "Commands: chatmap, addmap, remmap | View the Desert Bus Chatmap or add or remove your location to" \
               "or from it."

    def actions(self):
        return super(Chatmap, self).actions() + [ ("userlocation-updated", 1, self.setLocation),
                                                  ("userlocation-deleted", 1, self.deleteLocation) ]

    def onLoad(self) -> None:
        self.apiKey = self.bot.moduleHandler.runActionUntilValue("apikeys-getkey", "DBChatmap")

    def execute(self, message: IRCMessage):
        if message.command == "chatmap":
            return IRCResponse(ResponseType.Say, "Desert Bus Chatmap: {}".format(self.chatmapBaseUrl), message.replyTo)
        if not self.apiKey:
            return IRCResponse(ResponseType.Say, "No Desert Bus Chatmap API key found.", message.replyTo)
        if message.command == "addmap":
            loc = self.bot.moduleHandler.runActionUntilValue("userlocation", message.user.nick)
            if not loc or not loc["success"]:
                return

            return IRCResponse(ResponseType.Say,
                               self.setLocation(message.user.nick, loc["place"], False),
                               message.replyTo)
        elif message.command == "remmap":
            return IRCResponse(ResponseType.Say, self.deleteLocation(message.user.nick), message.replyTo)

    def setLocation(self, nick, location, checkExists = True):
        if not self.apiKey:
            return

        url = "{}api/chatizen/{}".format(self.chatmapBaseUrl, nick.lower())
        extraHeaders = { "Cookie": "password={}".format(self.apiKey) }
        if checkExists:
            result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, None, extraHeaders)
            if not result or result.status_code == 404:
                return

        userloc = self.bot.moduleHandler.runActionUntilValue("geolocation-place", location)
        data = "{{ \"lat\": {}, \"lon\": {} }}".format(userloc["latitude"], userloc["longitude"])
        setResult = self.bot.moduleHandler.runActionUntilValue("post-url", url, data, extraHeaders)
        if setResult and setResult.status_code == 204:
            return "Your location has been added to the chatmap."
        else:
            self.bot.log.warn(setResult)
            return "Something went wrong while adding your location to the chatmap."

    def deleteLocation(self, nick):
        if not self.apiKey:
            return

        url = "{}api/chatizen/{}".format(self.chatmapBaseUrl, nick.lower())
        extraHeaders = {"Cookie": "password={}".format(self.apiKey) }
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, None, extraHeaders)
        if not result or result.status_code == 404:
            return "Your location on the chatmap could not be determined."

        deleteResult = self.bot.moduleHandler.runActionUntilValue("delete-url", url, extraHeaders)
        if deleteResult.status_code == 204:
            return "Your location has been removed from the chatmap."
        else:
            self.bot.log.warn(deleteResult)
            return "Something went wrong while removing your location from the chatmap."


chatmapCommand = Chatmap()
