from twisted.plugin import IPlugin
from desertbot.moduleinterface import BotModule, IModule
from zope.interface import implementer


@implementer(IPlugin, IModule)
class GeoLocation(BotModule):
    def actions(self):
        return [ ("geolocation-latlon", 1, self.geolocationForLatLon),
                 ("geolocation-place", 1, self.geolocationForPlace) ]

    def geolocationForLatLon(self, lat, lon):
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "zoom": 10,
            "format": "jsonv2"
        }
        return self._sendLocationRequest(url, params)

    def geolocationForPlace(self, place):
        url = "https://nominatim.openstreetmap.org/search/{}".format(place.replace(" ", "%20"))
        params = {
            "format": "json",
            "limit": 1
        }
        return self._sendLocationRequest(url, params)

    def _sendLocationRequest(self, url, params):
        extraHeaders = {
            "Accept-Language": "en"
        }
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", url ,params=params, extraHeaders=extraHeaders)
        if not result:
            return None

        return self._geolocationFromJSON(result.json())

    def _geolocationFromJSON(self, json):
        success = True
        if isinstance(json, list):
            if len(json) == 0:
                success = False
            else:
                json = json[0]

        if "error" in json:
            success = False
        
        data = {
            "success": success
        }
        if not success:
            return data

        data["latitude"] = float(json["lat"])
        data["longitude"] = float(json["lon"])
        data["locality"] = json["display_name"] if "display_name" in json else "Unknown"
        return data


geoLocation = GeoLocation()
