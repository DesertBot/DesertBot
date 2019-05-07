from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from zope.interface import implementer
from datetime import datetime
import time


@implementer(IPlugin, IModule)
class OpenWeatherMap(BotCommand):
    weatherBaseURL = "https://api.openweathermap.org/data/2.5"

    def triggers(self):
        return ["forecast", "weather"]

    def help(self, arg):
        return "Commands: weather/forecast (<latlon/user/place>) - Uses the OpenWeatherMap API to request the weather " \
               "for a given set of coordinates, username or place. Requests the users own weather or forecast when no " \
               "paramters are given."

    def onLoad(self):
        self.apiKey = self.bot.moduleHandler.runActionUntilValue("apikeys-getkey", "OpenWeatherMap")

    def execute(self, message: IRCMessage):
        if not self.apiKey:
            return IRCResponse(ResponseType.Say, "No API key found.", message.replyTo)

        params = message.parameterList.copy()
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
                return IRCResponse(ResponseType.Say, "I can't determine locations at the moment. Try again later.",
                                   message.replyTo)
            if not location["success"]:
                return IRCResponse(ResponseType.Say, "I don't think that's even a location in this multiverse...",
                                   message.replyTo)
            return self._handleCommandWithLocation(message, location)
        except (IndexError, ValueError):
            pass  # The user did not give a latlon, so continue using other methods
        
        # Try to determine the user"s location from a nickname
        userLoc = self.bot.moduleHandler.runActionUntilValue("userlocation", params[0])
        if selfSearch:
            if not userLoc:
                return IRCResponse(ResponseType.Say, "I can't determine locations at the moment. Try again later.",
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
        request = message.command
        params = {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "units": "metric",
            "appid": self.apiKey
        }

        if request == "forecast":
            request = "forecast/daily"
            params["cnt"] = 4

        url = "{}/{}".format(self.weatherBaseURL, request)
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, params)
        output = None
        if not result:
            output = "No weather for this location could be found at this moment. Try again later."
        else:
            j = result.json()
            if "cod" not in j:
                output = "The OpenWeatherMap API returned an unknown reply."
            elif int(j["cod"]) != 200 and "message" in j:
                output = "The OpenWeatherMap API returned an error:{}".format(j["message"])
            elif int(j["cod"]) == 200:
                if message.command == "weather":
                    output = _parseWeather(j)
                elif message.command == "forecast":
                    output = _parseForecast(j)
        return IRCResponse(ResponseType.Say, "Location: {} | {}".format(location["locality"], output), message.replyTo)


def _parseWeather(json):
    description = json["weather"][0]["main"]
    icon = _getWeatherIcon(json["weather"][0]["id"])
    main = json["main"]
    tempC = round(main["temp"], 1)
    tempF = round(_celsiusToFahrenheit(main["temp"]), 1)
    humidity = main["humidity"]

    wind = json["wind"]
    winddir = "Unknown"
    if "deg" in wind:
        winddir = _getWindDirection(wind["deg"])
    windspeedMs = round(wind["speed"], 1)
    windspeedMph = round(_msToMph(wind["speed"]), 1)
    windspeedBft = _msToBft(wind["speed"])

    if "gust" in wind:
        gustsMs = round(wind["gust"], 1)
        gustsMph = round(_msToMph(wind["gust"]), 1)
        gustsBft = _msToBft(wind["gust"])
        gustStr = "Gust Speed: {} m/s / {} mph / {} BFT | ".format(gustsMs, gustsMph, gustsBft)
    else:
        gustStr = ""

    dataAge = int(round((time.time() - json["dt"]) / 60))
    if dataAge <= 0:
        dataAgeStr = "just now"
    else:
        dataAgeStr = "{} minute{} ago".format(dataAge, "s" if dataAge > 1 else "")

    return "Temp: {}°C / {}°F | Weather: {}{} | Humidity: {}% | Wind Speed: {} m/s / {} mph / {} BFT | {}Wind " \
           "Direction: {} | Latest Update: {}.".format(tempC, tempF, icon, description, humidity, windspeedMs,
                                                       windspeedMph, windspeedBft, gustStr, winddir, dataAgeStr)


def _parseForecast(json):
    daysList = json["list"]
    formattedDays = []
    for x in range(0, len(daysList)):
        day = daysList[x]
        date = datetime.utcfromtimestamp(day['dt']).strftime("%A")
        minC = round(day["temp"]["min"], 1)
        minF = round(_celsiusToFahrenheit(day["temp"]["min"]), 1)
        maxC = round(day["temp"]["max"], 1)
        maxF = round(_celsiusToFahrenheit(day["temp"]["max"]), 1)
        description = day["weather"][0]["main"]
        icon = _getWeatherIcon(day["weather"][0]["id"])
        formattedDays.append("{}: {} - {}°C, {} - {}°F, {}{}".format(date, minC, maxC, minF, maxF, icon, description))
    return " | ".join(formattedDays)


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


def _getWeatherIcon(conditionID):
    icon = ""
    if conditionID >= 200 and conditionID < 300:
        icon = "\u26A1"
    elif conditionID >= 300 and conditionID < 600:
        icon = "\U0001F4A7"
    elif conditionID >= 600 and conditionID < 700:
        icon = "\u2744"
    elif conditionID >= 700 and conditionID < 800:
        icon = "\U0001F32B"
    elif conditionID == 800:
        icon = "\u2600"
    elif conditionID > 800:
        icon = "\u2601"
    return icon


openWeatherMapCommand = OpenWeatherMap()
