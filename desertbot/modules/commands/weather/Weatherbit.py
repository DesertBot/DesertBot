from collections import OrderedDict
from datetime import datetime

from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.moduleinterface import IModule
from desertbot.modules.commands.weather.BaseWeatherCommand import BaseWeatherCommand, getFormattedWeatherData, \
    getFormattedForecastData


@implementer(IPlugin, IModule)
class Weatherbit(BaseWeatherCommand):
    weatherBaseURL = "https://api.weatherbit.io/v2.0"

    def __init__(self):
        subCommands = OrderedDict([
            ('weather', self.getWeather),
            ('forecast', self.getForecast)]
        )
        BaseWeatherCommand.__init__(self, "Weatherbit", subCommands)

    def triggers(self):
        return ["weatherbit"]

    def getWeather(self, location) -> str:
        return self._handleCommand("weather", location)

    def getForecast(self, location) -> str:
        return self._handleCommand("forecast", location)

    def _handleCommand(self, subCommand, location) -> str:
        request = subCommand
        params = {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "units": "M",
            "key": self.apiKey
        }

        if subCommand == "weather":
            request = "current"
        if subCommand == "forecast":
            request = "forecast/daily"
            params["days"] = 4

        url = "{}/{}".format(self.weatherBaseURL, request)
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, params)
        output = None
        if not result:
            output = "No weather for this location could be found at this moment. Try again later."
        else:
            j = result.json()
            if "data" not in j or "count" in j and j["count"] == 0:
                output = "The Weatherbit API returned an unknown reply."
            else:
                if subCommand == "weather":
                    output = _parseWeather(j)
                elif subCommand == "forecast":
                    output = _parseForecast(j)
        return output


def _parseWeather(json):
    data = json["data"][0]

    weatherData = {
        "weatherCode": data["weather"]["code"],
        "description": data["weather"]["description"],
        "tempC": data["temp"],
        "humidity": data["rh"],
        "windSpeedMs": data["wind_spd"],
        "timestamp": data["ts"],
        "windDir": data["wind_dir"]
    }

    return getFormattedWeatherData(weatherData)


def _parseForecast(json):
    daysList = json["data"]
    forecastData = []
    for day in daysList:
        forecastData.append({
            "date": datetime.fromtimestamp(day['ts']).strftime("%A"),
            "minC": day["low_temp"],
            "maxC": day["max_temp"],
            "weatherCode": day["weather"]["code"],
            "description": day["weather"]["description"],
        })

    return getFormattedForecastData(forecastData)


weatherbitCommand = Weatherbit()
