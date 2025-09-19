import datetime
import pytz
import time
from typing import List, Union, Dict

from desertbot.message import IRCMessage
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse
from desertbot.utils.regex import re


class BaseWeatherCommand(BotCommand):
    def __init__(self, name, subCommands):
        BotCommand.__init__(self)
        self.name = name
        self.subCommands = subCommands

    def help(self, query: Union[List[str], None]) -> str:
        if query and len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                doc = re.sub(r"\s+", " ", self.subCommands[subCommand].__doc__)
                return f"{self.bot.commandChar}{self.triggers()[0]} {doc}"
            else:
                return self._unrecognizedSubcommand(subCommand)
        else:
            return self._helpText

    def onLoad(self):
        self.apiKey = self.bot.moduleHandler.runActionUntilValue("get-api-key", self.name)

        command = self.triggers()[0]
        subCommands = "/".join(self.subCommands)
        self._helpText = f"{self.bot.commandChar}{command} {subCommands} (<latlon/user/place>) - Requests weather or " \
                         f"forecast data from the {self.name} API for a given set of coordinates, username or place. " \
                         f"Requests the users own weather or forecast when no parameters are given. Use " \
                         f"{self.bot.commandChar}{command} <subcommand> for subcommand help."

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            subCommand = message.parameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(self._unrecognizedSubcommand(subCommand), message.replyTo)

            if not self.apiKey:
                return IRCResponse("No API key found.", message.replyTo)

            params = message.parameterList.copy()

            # Remove the subcommand from the parameters should we could parse the rest without shifting
            params.pop(0)

            # Use the user"s nickname as a parameter if none were given
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
                    return IRCResponse("I can't determine locations at the moment. Try again later.", message.replyTo)
                if not location["success"]:
                    return IRCResponse("I don't think that's even a location in this multiverse...", message.replyTo)
                return self._handleCommandWithLocation(message.replyTo, subCommand, location)
            except (IndexError, ValueError):
                pass  # The user did not give a latlon, so continue using other methods

            # Try to determine the user"s location from a nickname
            userLoc = self.bot.moduleHandler.runActionUntilValue("userlocation", params[0])
            if selfSearch:
                if not userLoc:
                    return IRCResponse("I can't determine locations at the moment. Try again later.", message.replyTo)
                elif not userLoc["success"]:
                    return IRCResponse(userLoc["error"], message.replyTo)
            if userLoc and userLoc["success"]:
                if "lat" in userLoc:
                    location = self.bot.moduleHandler.runActionUntilValue("geolocation-latlon", userLoc["lat"],
                                                                          userLoc["lon"])
                else:
                    location = self.bot.moduleHandler.runActionUntilValue("geolocation-place", userLoc["location"])
                if not location:
                    return IRCResponse("I can't determine locations at the moment. Try again later.", message.replyTo)
                if not location["success"]:
                    return IRCResponse("I don't think that's even a location in this multiverse...", message.replyTo)
                return self._handleCommandWithLocation(message.replyTo, subCommand, location)

            # Try to determine the location by the name of the place
            place = " ".join(params)
            location = self.bot.moduleHandler.runActionUntilValue("geolocation-place", place)
            if not location:
                return IRCResponse("I can't determine locations at the moment. Try again later.", message.replyTo)
            if not location["success"]:
                return IRCResponse("I don't think that's even a location in this multiverse...", message.replyTo)
            return self._handleCommandWithLocation(message.replyTo, subCommand, location)
        else:
            return IRCResponse(self.help(None), message.replyTo)

    def _handleCommandWithLocation(self, replyTo, subCommand, location):
        return IRCResponse("Location: {} | {}".format(location["locality"],
                                                      self.subCommands[subCommand](location)), replyTo)

    def _unrecognizedSubcommand(self, subCommand):
        return (f"unrecognized subcommand f'{subCommand}', "
                f"available subcommands for {self.name} are: {', '.join(self.subCommands.keys())}")


def getFormattedWeatherData(weatherData: Dict):
    icon = _getWeatherIcon(weatherData["weatherCode"])
    description = weatherData["description"].title()
    humidity = int(weatherData["humidity"])
    tempC = round(weatherData["tempC"], 1)
    tempF = round(_celsiusToFahrenheit(weatherData["tempC"]), 1)
    windSpeedMs = round(weatherData["windSpeedMs"], 1)
    windSpeedMph = round(_msToMph(weatherData["windSpeedMs"]), 1)
    windSpeedBft = _msToBft(weatherData["windSpeedMs"])
    windDirStr = _getWindDirection(weatherData["windDir"]) if "windDir" in weatherData else "Unknown"

    if "gustSpeedMs" in weatherData:
        gustsMs = round(weatherData["gustSpeedMs"], 1)
        gustsMph = round(_msToMph(weatherData["gustSpeedMs"]), 1)
        gustsBft = _msToBft(weatherData["gustSpeedMs"])
        gustStr = f"Gust Speed: {gustsMs} m/s / {gustsMph} mph / {gustsBft} BFT | "
    else:
        gustStr = ""

    dataAge = int(round((time.time() - weatherData["timestamp"]) / 60))
    if dataAge <= 0:
        dataAgeStr = "now"
    else:
        dataAgeStr = f"{dataAge} min ago"

    if "stationID" in weatherData:
        stationIDStr = f"Station ID: {weatherData['stationID']} | "
    else:
        stationIDStr = ""

    if "timezone" in weatherData:
        zone = pytz.timezone(weatherData["timezone"])
        localTime = datetime.datetime.fromtimestamp(weatherData["timestamp"], tz=zone)
        localTimeStr = localTime.strftime(" @ %H:%M (%Z)")
    else:
        localTimeStr = ""

    return f"Temp: {tempC}°C / {tempF}°F | Weather: {icon}{description} | Humidity: {humidity}% | " \
           f"Wind Speed: {windSpeedMs} m/s / {windSpeedMph} mph / {windSpeedBft} BFT | {gustStr}Wind " \
           f"Direction: {windDirStr} | {stationIDStr}Latest Update: {dataAgeStr}{localTimeStr}"


def getFormattedForecastData(forecastData: List):
    formattedDays = []
    for day in forecastData:
        icon = _getWeatherIcon(day["weatherCode"])
        description = day["description"].title()
        minC = round(day["minC"], 1)
        minF = round(_celsiusToFahrenheit(day["minC"]), 1)
        maxC = round(day["maxC"], 1)
        maxF = round(_celsiusToFahrenheit(day["maxC"]), 1)
        date = day["date"]
        formattedDays.append("{}: {} - {}°C, {} - {}°F, {}{}".format(date, minC, maxC, minF, maxF, icon, description))
    return " | ".join(formattedDays)


def _celsiusToFahrenheit(celsius):
    return (celsius * 9 / 5) + 32


def _msToMph(windMs):
    return windMs * 2.237


def _msToBft(windMs):
    windSpeedTranslation = {
        0.5: 1,
        1.5: 2,
        3.3: 3,
        5.4: 4,
        7.9: 5,
        10.7: 6,
        13.8: 7,
        17.1: 8,
        20.7: 9,
        24.4: 10,
        28.4: 11,
        32.6: 12,
    }
    windSpeed = 0
    for maxSpeed in sorted(windSpeedTranslation.keys()):
        if windMs < maxSpeed:
            break
        else:
            windSpeed = windSpeedTranslation[maxSpeed]
    return windSpeed


def _getWindDirection(angle):
    windDirectionTranslation = {
        11.25: "N",
        33.75: "NNE",
        56.25: "NE",
        78.75: "ENE",
        101.25: "E",
        123.75: "ESE",
        146.25: "SE",
        168.75: "SSE",
        191.25: "S",
        213.75: "SSW",
        236.25: "SW",
        258.75: "WSW",
        281.25: "W",
        303.75: "WNW",
        326.25: "NW",
        348.75: "NNW",
        360.0: "N"
    }
    windDirection = "N"
    for maxDegrees in sorted(windDirectionTranslation.keys()):
        if angle < maxDegrees:
            break
        else:
            windDirection = windDirectionTranslation[maxDegrees]
    return windDirection


def _getWeatherIcon(conditionID):
    icon = ""
    if 200 <= conditionID < 300:
        icon = "\u26A1"
    elif 300 <= conditionID < 600:
        icon = "\U0001F4A7"
    elif 600 <= conditionID < 700:
        icon = "\u2744"
    elif 700 <= conditionID < 800:
        icon = "\U0001F32B"
    elif conditionID == 800:
        icon = "\u2600"
    elif conditionID > 800:
        icon = "\u2601"
    return icon
