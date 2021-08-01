from collections import OrderedDict
from datetime import datetime

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.moduleinterface import IModule
from desertbot.modules.commands.weather.BaseWeatherCommand import BaseWeatherCommand, getFormattedWeatherData, \
    getFormattedForecastData


@implementer(IPlugin, IModule)
class OpenWeatherMap(BaseWeatherCommand):
    weatherBaseURL = "https://api.openweathermap.org/data/2.5"

    def __init__(self):
        subCommands = OrderedDict([
            ('weather', self.getWeather),
            ('forecast', self.getForecast)]
        )
        BaseWeatherCommand.__init__(self, "OpenWeatherMap", subCommands)

    def triggers(self):
        return ["openweathermap"]

    def getWeather(self, location) -> str:
        return self._handleCommand("weather", location)

    def getForecast(self, location) -> str:
        return self._handleCommand("forecast", location)

    def _handleCommand(self, subCommand, location) -> str:
        request = subCommand
        params = {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "units": "metric",
            "appid": self.apiKey
        }

        if subCommand == "forecast":
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
                if subCommand == "weather":
                    output = _parseWeather(j)
                elif subCommand == "forecast":
                    output = _parseForecast(j)
        return output


def _parseWeather(json):
    main = json["main"]
    wind = json["wind"]

    weatherData = {
        "weatherCode": json["weather"][0]["id"],
        "description": json["weather"][0]["main"],
        "tempC": main["temp"],
        "humidity": main["humidity"],
        "windSpeedMs": wind["speed"],
        "timestamp": json["dt"]
    }

    if "deg" in wind:
        weatherData["windDir"] = wind["deg"]

    if "gust" in wind:
        weatherData["gustSpeedMs"] = wind["gust"]

    return getFormattedWeatherData(weatherData)


def _parseForecast(json):
    daysList = json["list"]
    forecastData = []
    for day in daysList:
        forecastData.append({
            "weatherCode": day["weather"][0]["id"],
            "description": day["weather"][0]["main"],
            "date": datetime.utcfromtimestamp(day['dt']).strftime("%A"),
            "minC": day["temp"]["min"],
            "maxC": day["temp"]["max"]
        })

    return getFormattedForecastData(forecastData)


openWeatherMapCommand = OpenWeatherMap()
