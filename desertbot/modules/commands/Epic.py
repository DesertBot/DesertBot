"""
@date: 2021-02-05
@author: HelleDaryd
"""

from datetime import datetime, timezone

import dateutil.parser as dparser

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse
from desertbot.utils.string import timeDeltaString

import jq
# I should be scheduled slightly past 16:00 each day

@implementer(IPlugin, IModule)
class Epic(BotCommand):
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    query = jq.compile("""
        def e(f): if f == "[]" then null else f end;
        [ .data.Catalog.searchStore.elements[] |
            ({
                id: .id,
                title: .title,
                url: (if e(.productSlug) then ("https://www.epicgames.com/store/en-US/product/" + .productSlug) else null end),
            }) +
            (.customAttributes | from_entries |
            {
                publisher: e(.publisherName // .developerName),
                developer: e(.developerName // .publisherName)
            }) +
            try (.promotions |
            # Decorate future items (spammy)
            .upcomingPromotionalOffers |= ((..|objects) |= . + { future: true }) |
            (.promotionalOffers, .upcomingPromotionalOffers)[] | .promotionalOffers[] |
            select(.discountSetting.discountPercentage == 0) |
            {
                startDate: .startDate,
                endDate: .endDate,
                future: (.future // false)
            })
        ] | reduce .[] as $item ({}; . + {($item.id): $item})
        """)

    def triggers(self):
        return ["epic"]

    def onLoad(self) -> None:
        pass

    def help(self, query):
        """
        Epic command syntax:
        .epic - current free games
        .epic current - current free games
        .epic next - upcoming free games
        .epic check - check for new free games
        """
        helpDict = {
            "current": "{}epic - Display the current free games on the Epic Games Store.",
            "next": "{}epic next - Display the upcoming free games on the Epic Games Store",
            "check": "{}epic check - Force a check on the Epic Games Store feed"
        }
        if len(query) == 1:
            return ("{0}epic current/next/check - Get information about the free games on the Epic Games Store"
                    " Use {0}help epic <subcommand> for more help.".format(self.bot.commandChar))
        else:
            if query[1].lower() in helpDict:
                return helpDict[query[1].lower()].format(self.bot.commandChar)
            else:
                return ("{!r} is not a valid subcommand, use {}help epic for a list of subcommands"
                        .format(query[1], self.bot.commandChar))

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return self.tell_games(message)
        if message.parameterList[0].lower() == "next":
            return self.tell_games(message, False)
        elif message.parameterList[0].lower() == "check":
            return self.check_games(message)
        return self.tell_games(message)


    def check_games(self, message: IRCMessage):
        response = self.bot.moduleHandler.runActionUntilValue("fetch-url", self.url)
        if not response:
            self.logger.warning("Couldn't fetch the Epic games feed, maybe a temporary failure")
            return False

        result = self.query.input(text=response.content.decode("utf8")).first()

        fresh = []
        for (pid, game) in result.items():
            game["active"] = self._active(game)

            if pid in self.storage:
                if game["url"]:
                    if "shortUrl" in self.storage[pid]:
                        game["shortUrl"] = self.storage[pid]["shortUrl"]
                    else:
                        game["shortUrl"] = self.bot.moduleHandler.runActionUntilValue("shorten-url", game["url"])
                if "active" not in self.storage[pid] and game["active"]:
                    fresh.append(game)
            else:
                if game["url"]:
                    game["shortUrl"] = self.bot.moduleHandler.runActionUntilValue("shorten-url", game["url"])
                if game["active"]:
                    fresh.append(game)

            self.storage[pid] = game

        # Clean up our storage
        for pid in self.storage.keys():
            if pid not in result:
                self.storage.pop(pid)

        return [IRCResponse(self._format(g, True), message.replyTo) for g in fresh]

    def tell_games(self, message: IRCMessage, active=True):
        return [IRCResponse(self._format(g), message.replyTo) for g in self.storage.values() if self._active(g) == active]


    @staticmethod
    def _active(game):
        now = datetime.now(tz=timezone.utc)
        if dparser.isoparse(game["startDate"]) <= now <= dparser.isoparse(game["endDate"]):
            return True
        return False

    @staticmethod
    def _format(game, fresh=False):
        now = datetime.now(tz=timezone.utc)
        active = Epic._active(game)
        future = timeDeltaString(dparser.isoparse(game["startDate"]), now)
        left = timeDeltaString(dparser.isoparse(game["endDate"]), now)

        builder = ""
        if active:
            builder += colour(A.bold[A.fg.gray["Free on Epic: "]])
        else:
            builder += colour(A.normal[A.fg.gray["Free on Epic in "], f"{future}", A.fg.gray[": "]])
        builder += colour(A.bold[f"{game['title']}"])
        if "developer" in game:
            builder += colour(A.normal[" by ", A.bold[f"{game['developer']}"]])
        if active and not fresh:
            builder += colour(A.normal[" for another ", A.bold[f"{left}"]])
        if "shortUrl" in game:
            builder += colour(A.normal[f" - {game['shortUrl']}"])

        return builder

epic = Epic()
