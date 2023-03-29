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
        """weather (<latlon/user/place>) - Requests weather data from the API for a given set of coordinates, username
        or place. Requests the users own weather when no parameters are given."""
        return self._handleCommand("current", self._getApiParams(location), _parseWeather)

    def getForecast(self, location) -> str:
        """forecast (<latlon/user/place>) - Requests forecast data from the API for a given set of coordinates, username
        or place. Requests the users own forecast when no parameters are given."""
        params = self._getApiParams(location)
        params["days"] = 4
        return self._handleCommand("forecast/daily", params, _parseForecast)
    
    def _getApiParams(self, location):
        return {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "units": "M",
            "key": self.apiKey
        }

    def _handleCommand(self, endpoint, params, parserFunc) -> str:
        url = f"{self.weatherBaseURL}/{endpoint}"
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, params)
        if not result:
            return "No weather for this location could be found at this moment. Try again later."
        else:
            j = result.json()
            if "data" not in j or "count" in j and j["count"] == 0:
                return "The Weatherbit API returned an unknown reply."
            self.logger.debug(j) 
            return parserFunc(j)


def _parseWeather(json):
    data = json["data"][0]

    weatherData = {
        "weatherCode": data["weather"]["code"],
        "description": data["weather"]["description"],
        "tempC": data["temp"],
        "humidity": data["rh"],
        "windSpeedMs": data["wind_spd"],
        "timestamp": data["ts"],
        "windDir": data["wind_dir"],
        "stationID": data["station"],
        "timezone": data["timezone"]
    }

    return getFormattedWeatherData(weatherData)


def _parseForecast(json):
    daysList = json["data"]
    forecastData = []
    for day in daysList:
        forecastData.append({
            "date": datetime.strptime(day["datetime"], "%Y-%m-%d").strftime("%A"),
            "minC": day["low_temp"],
            "maxC": day["max_temp"],
            "weatherCode": day["weather"]["code"],
            "description": day["weather"]["description"],
        })

    return getFormattedForecastData(forecastData)


weatherbitCommand = Weatherbit()
