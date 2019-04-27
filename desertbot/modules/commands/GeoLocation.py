from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer


@implementer(IPlugin, IModule)
class GeoLocation(BotCommand):
    def triggers(self):
        return ["geolocation"]

    def help(self, query):
        return ("geolocation <address> - Uses the OpenStreetMap geocoding API to lookup GPS coordinates "
                "for the given address")

    def actions(self):
        return super(GeoLocation, self).actions() + [ ("geolocation-latlon", 1, self.geolocationForLatLon),
                                                      ("geolocation-place", 1, self.geolocationForPlace) ]

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give an address to look up", message.replyTo)

        result = self.geolocationForPlace(message.parameters)
        if not result["success"]:
            return IRCResponse(ResponseType.Say,"I don't think that's even a location in this multiverse...",
                               message.replyTo)

        return IRCResponse(ResponseType.Say, "GPS coords for '{}' are: {},{}" .format(message.parameters,
                           result["latitude"], result["longitude"]), message.replyTo)

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
            "addressdetails": 1,
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

        locationInfo = []
        for addressPart, value in json["address"].items():
            if addressPart in ["city", "state", "country", "town", "continent", "aerodrome", "park", "attraction"]:
                locationInfo.append(addressPart)

        if len(locationInfo) == 0:
            locationInfo.append("Unknown")

        data["locality"] = ", ".join(locationInfo)
        return data


geoLocation = GeoLocation()
