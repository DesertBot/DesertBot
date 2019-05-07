from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from desertbot.utils.timeutils import now, timestamp
from zope.interface import implementer
from datetime import datetime
from typing import Union


@implementer(IPlugin, IModule)
class Time(BotCommand):
    timeBaseURL = "http://api.timezonedb.com/v2.1/get-time-zone"

    def triggers(self):
        return ["time"]

    def help(self, query: Union[str, None]) -> str:
        return "Commands: time <lat> <lon>, time <place>, time <nickname> | Get the current local time for " \
               "the given latlon, place or user."

    def onLoad(self) -> None:
        self.apiKey = self.bot.moduleHandler.runActionUntilValue("apikeys-getkey", "TimeZoneDB")

    def execute(self, message: IRCMessage):
        if not self.apiKey:
            return IRCResponse(ResponseType.Say, "No API key found.", message.replyTo)

        params = message.parameterList

        # Use the user's nickname as a parameter if none were given
        if len(params) == 0:
            params.append(message.user.nick)
            selfSearch = True
        else:
            selfSearch = False

        # Try using latlon to get the location
        try:
            lat = float(params[0])
            lon = float(params[1])
            location = self.bot.moduleHandler.runActionUntilValue("geolocation-latlon", lat, lon)
            if not location:
                return IRCResponse(ResponseType.Say,
                                   "I can't determine locations at the moment. Try again later.",
                                   message.replyTo)
            if not location["success"]:
                return IRCResponse(ResponseType.Say,
                                   "I don't think that's even a location in this multiverse...",
                                   message.replyTo)
            return self._handleCommandWithLocation(message, location)
        except (IndexError, ValueError):
            pass  # The user did not give a latlon, so continue using other methods

        # Try to determine the user's location from a nickname
        userLoc = self.bot.moduleHandler.runActionUntilValue("userlocation", params[0])
        if selfSearch:
            if not userLoc:
                return IRCResponse(ResponseType.Say,
                                   "I can't determine locations at the moment. Try again later.",
                                   message.replyTo)
            elif not userLoc["success"]:
                return IRCResponse(ResponseType.Say, userLoc["error"], message.replyTo)
        if userLoc and userLoc["success"]:
            if "lat" in userLoc:
                location = self.bot.moduleHandler.runActionUntilValue("geolocation-latlon", userLoc["lat"],
                                                                      userLoc["lon"])
            else:
                location = self.bot.moduleHandler.runActionUntilValue("geolocation-place", userLoc["location"])
            if not location:
                return IRCResponse(ResponseType.Say, "I can't determine locations at the moment. Try again later.",
                                   message.replyTo)
            if not location["success"]:
                return IRCResponse(ResponseType.Say, "I don't think that's even a location in this multiverse...",
                                   message.replyTo)
            return self._handleCommandWithLocation(message, location)

        # Try to determine the location by the name of the place
        place = " ".join(params)
        location = self.bot.moduleHandler.runActionUntilValue("geolocation-place", place)
        if not location:
            return IRCResponse(ResponseType.Say, "I can't determine locations at the moment. Try again later.",
                               message.replyTo)
        if not location["success"]:
            return IRCResponse(ResponseType.Say, "I don't think that's even a location in this multiverse...",
                               message.replyTo)
        return self._handleCommandWithLocation(message, location)

    def _handleCommandWithLocation(self, message, location):
        formattedTime = self._getTime(location["latitude"], location["longitude"])
        return IRCResponse(ResponseType.Say,
                           "Location: {} | {}".format(location["locality"], formattedTime),
                           message.replyTo)

    def _getTime(self, lat, lon):
        currentTime = timestamp(now())
        params = {
            "format": "json",
            "by": "position",
            "key": self.apiKey,
            "lat": lat,
            "lng": lon
        }
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", self.timeBaseURL, params)
        if not result:
            return "No time for this location could be found at this moment. Try again later."
        timeJSON = result.json()
        if timeJSON["status"] != "OK":
            if "message" in timeJSON:
                return timeJSON["message"]
            else:
                return "An unknown error occurred while requesting the time."
        resultDate = datetime.fromtimestamp(currentTime + int(timeJSON["gmtOffset"]))
        properDay = self._getProperDay(resultDate.day)
        formattedTime = resultDate.strftime("%H:%M (%I:%M %p) on %A, " + properDay + " of %B, %Y")
        return "Timezone: {} ({}) | Local time is {} | Daylight Savings Time: {}".format(
            timeJSON["zoneName"], timeJSON["abbreviation"], formattedTime, "Yes" if timeJSON["dst"] == "1" else "No")

    def _getProperDay(self, day):
        if day in [1, 21, 31]:
            return "{}st".format(day)
        elif day in [2, 22]:
            return "{}nd".format(day)
        elif day in [3, 23]:
            return "{}rd".format(day)
        else:
            return "{}th".format(day)


timeZoneCommand = Time()
