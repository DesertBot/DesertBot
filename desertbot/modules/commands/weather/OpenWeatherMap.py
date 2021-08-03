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
        """weather (<latlon/user/place>) - Requests weather data from the API for a given set of coordinates, username
        or place. Requests the users own weather when no parameters are given."""
        return self._handleCommand("weather", self._getApiParams(location), _parseWeather)

    def getForecast(self, location) -> str:
        """forecast (<latlon/user/place>) - Requests forecast data from the API for a given set of coordinates, username
        or place. Requests the users own forecast when no parameters are given."""
        params = self._getApiParams(location)
        params["cnt"] = 4
        return self._handleCommand("forecast/daily", params, _parseForecast)
    
    def _getApiParams(self, location):
        return {
            "lat": location["latitude"],
            "lon": location["longitude"],
            "units": "metric",
            "appid": self.apiKey
        }

    def _handleCommand(self, endpoint, params, parserFunc) -> str:
        url = f"{self.weatherBaseURL}/{endpoint}"
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, params)
        if not result:
            return "No weather for this location could be found at this moment. Try again later."
        else:
            j = result.json()
            if "cod" not in j:
                return "The OpenWeatherMap API returned an unknown reply."
            elif int(j["cod"]) != 200 and "message" in j:
                return "The OpenWeatherMap API returned an error:{}".format(j["message"])
            elif int(j["cod"]) == 200:
                return parserFunc(j)


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
