from typing import List, Union

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class Chatmap(BotCommand):
    chatmapBaseUrl = "https://chatmap.dbco.link/"

    def triggers(self):
        return ["chatmap", "addmap", "remmap"]

    def help(self, query: Union[List[str], None]) -> str:
        helpDict = {
            "chatmap": f"{self.bot.commandChar}chatmap/addmap/remmap - View the Desert Bus Chatmap, or manage your location marker on it.",
            "addmap": f"{self.bot.commandChar}addmap - Add or update your location marker to the Desert Bus Chatmap",
            "remmap": f"{self.bot.commandChar}remmap - Remove your location marker from the Desert Bus Chatmap"
        }
        if query is None or query[0].lower() not in helpDict:
            # should never happen??
            return helpDict["chatmap"]
        else:
            return helpDict[query[0].lower()]

    def actions(self):
        return super(Chatmap, self).actions() + [("userlocation-updated", 1, self.setLocation),
                                                 ("userlocation-deleted", 1, self.deleteLocation)]

    def onLoad(self) -> None:
        self.apiKey = self.bot.moduleHandler.runActionUntilValue("get-api-key", "DBChatmap")

    def execute(self, message: IRCMessage):
        if message.command == "chatmap":
            return IRCResponse("Desert Bus Chatmap: {}".format(self.chatmapBaseUrl), message.replyTo)
        if not self.apiKey:
            return IRCResponse("No Desert Bus Chatmap API key found.", message.replyTo)
        if message.command == "addmap":
            loc = self.bot.moduleHandler.runActionUntilValue("userlocation", message.user.nick)
            if not loc or not loc["success"]:
                return IRCResponse(f"You do not have a location stored in {self.bot.nick}!", message.replyTo)

            return IRCResponse(self.setLocation(message.user.nick, loc["location"], False), message.replyTo)
        elif message.command == "remmap":
            return IRCResponse(self.deleteLocation(message.user.nick), message.replyTo)

    def setLocation(self, nick, location, checkExists=True):
        if not self.apiKey:
            return

        url = "{}api/chatizen/{}".format(self.chatmapBaseUrl, nick)
        extraHeaders = {"Cookie": "password={}".format(self.apiKey), "Content-Type": "application/json"}
        if checkExists:
            result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, None, extraHeaders)
            if not result or result.status_code == 404:
                return

        userloc = self.bot.moduleHandler.runActionUntilValue("geolocation-place", location)
        data = {"lat": userloc["latitude"], "lon": userloc["longitude"]}
        setResult = self.bot.moduleHandler.runActionUntilValue("post-url", url, json=data, extraHeaders=extraHeaders)
        if setResult and setResult.status_code == 204:
            return "Your location has been added to the chatmap."
        else:
            self.logger.warning(f"Failed to add marker to chatmap - API returned status {setResult}")
            return "Something went wrong while adding your location to the chatmap."

    def deleteLocation(self, nick):
        if not self.apiKey:
            return

        url = "{}api/chatizen/{}".format(self.chatmapBaseUrl, nick)
        extraHeaders = {"Cookie": "password={}".format(self.apiKey)}
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, None, extraHeaders)
        if not result or result.status_code == 404:
            return "Your location on the chatmap could not be determined."

        deleteResult = self.bot.moduleHandler.runActionUntilValue("delete-url", url, extraHeaders)
        if deleteResult and deleteResult.status_code == 204:
            return "Your location has been removed from the chatmap."
        else:
            self.logger.warning(f"Failed to delete marker from chatmap - API returned {deleteResult}")
            return "Something went wrong while removing your location from the chatmap."


chatmapCommand = Chatmap()
