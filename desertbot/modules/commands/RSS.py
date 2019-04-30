from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import admin, BotCommand
from zope.interface import implementer

import datetime

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import dateutil.parser as dparser
from bs4 import BeautifulSoup


@implementer(IPlugin, IModule)
class RSS(BotCommand):
    def triggers(self):
        return ["rss"]

    def actions(self):
        return super(RSS, self).actions() + [("message-channel", 1, self.checkFeeds)]

    def onLoad(self) -> None:
        if "rss_feeds" not in self.bot.storage:
            self.bot.storage["rss_feeds"] = {}
        self.feeds = self.bot.storage["rss_feeds"]

    def help(self, query):
        """
        RSS command syntax:
        .rss <feed_name> - fetch latest for feed name
        .rss follow <url> <feed_name> - start following <url> as <feed_name>
        .rss unfollow <feed_name> - stop following <feed_name>
        .rss toggle <feed_name> - toggle automatic posting of new RSS posts to channels
        .rss list - list followed feeds
        """
        helpDict = {
            "follow": "{}rss follow <url> <feed_name> - Start following the RSS feed at <url> as <feed_name>",
            "unfollow": "{}rss unfollow <feed_name> - Stop following the RSS feed at <url>",
            "toggle": "{}rss toggle <feed_name> - Toggle displaying of new posts of the given RSS feed as chat messages",
            "list": "{}rss list - List currently followed RSS feeds",
            "": "{}rss <feed_name> - Display the latest post in the given RSS feed."
        }
        if len(query) == 1:
            return ("{0}rss <feed_name>/follow/unfollow/toggle/list - Manages RSS feeds and automatic updates of them"
                    " Use {0}help rss <subcommand> for more help.".format(self.bot.commandChar))
        else:
            if query[1].lower() in helpDict:
                return helpDict[query[1].lower()].format(self.bot.commandChar)
            else:
                return ("{!r} is not a valid subcommand, use {}help rss for a list of subcommands"
                        .format(query[1], self.bot.commandChar))

    def execute(self, message: IRCMessage):
        if message.parameterList[0].lower() == "follow":
            return self._followFeed(message)
        elif message.parameterList[0].lower() == "unfollow":
            return self._unfollowFeed(message)
        elif message.parameterList[0].lower() == "toggle":
            return self._toggleFeedSuppress(message)
        elif message.parameterList[0].lower() == "list":
            return self._listFeeds(message)
        elif len(message.parameters.strip()) > 0:
            feed = message.parameters.strip()
            latest = self._getLatest(feed)
            if latest is not None:
                response = 'Latest {}: {} | {}'.format(feed["name"], feed["title"], feed["link"])
                return IRCResponse(ResponseType.Say, response, message.replyTo)
            else:
                return IRCResponse(ResponseType.Say,
                                   "{} is not an RSS feed I monitor, leave a tell if you'd like it added!".format(message.parameters.strip()),
                                   message.replyTo)
        else:
            return self.help(None)

    def _getLatest(self, feedName):
        lowerMap = {name.lower(): name for name in self.feeds}
        if feedName.lower() in lowerMap:
            name = lowerMap[feedName.lower()]
            title = self.feeds[name]["latestTitle"]
            link = self.feeds[name]["latestLink"]
            return {
                "name": name,
                "title": title,
                "link": link
            }
        else:
            return None

    def checkFeeds(self, message: IRCMessage):
        if message.command in self.triggers():
            return self.execute(message)
        responses = []
        for feedName, feedDeets in self.feeds.items():
            if feedDeets["lastCheck"] > datetime.datetime.utcnow() - datetime.timedelta(minutes=10):
                continue

            self.feeds[feedName]["lastCheck"] = datetime.datetime.utcnow()

            response = self.bot.moduleHandler.runActionUntilValue("fetch-url", feedDeets["url"])

            if not response:
                self.logger.warning("failed to fetch {!r}, either a server hiccup "
                                    "or the feed no longer exists".format(feedDeets["url"]))
                continue

            soup = BeautifulSoup(response.content, "lxml")
            item = soup.find("item")

            if item is None:
                self.logger.warning("the feed at {!r} doesn't have any items, has it shut down?"
                                    .format(feedDeets["url"]))
                continue

            itemDate = item.find("pubdate").text
            newestDate = dparser.parse(itemDate, fuzzy=True, ignoretz=True)

            if newestDate > feedDeets["lastUpdate"]:
                self.feeds[feedName]["lastUpdate"] = newestDate
                title = item.find("title").text
                link = item.find("link").text
                link = self.bot.moduleHandler.runActionUntilValue("shorten-url", link)
                self.feeds[feedName]["lastTitle"] = title
                self.feeds[feedName]["lastLink"] = link
                if not feedDeets["suppress"]:
                    response = "New {}! Title: {} | {}".format(feedName, title, link)
                    responses.append(IRCResponse(ResponseType.Say, response, message.replyTo))
                self.bot.storage["rss_feeds"] = self.feeds

        return responses

    @admin("[RSS] Only my admins may follow new RSS feeds!")
    def _followFeed(self, message: IRCMessage):
        try:
            url = message.parameterList[1]
            name = " ".join(message.parameterList[2:])
            feed_object = {
                "url": url,
                "lastUpdate": datetime.datetime.utcnow() - datetime.timedelta(days=365),
                "lastTitle": "",
                "lastLink": "",
                "lastCheck": datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
                "suppress": False
            }
            self.feeds[name] = feed_object
            self.bot.storage["rss_feeds"] = self.feeds
            return IRCResponse(ResponseType.Say,
                               "Successfully followed {} at URL {}".format(name, url),
                               message.replyTo)
        except Exception:
            self.logger.exception("Failed to follow RSS feed - {}".format(message.messageString))
            return IRCResponse(ResponseType.Say,
                               "I couldn't quite parse that RSS follow, are you sure you did it right?",
                               message.replyTo)

    @admin("[RSS] Only my admins may unfollow RSS feeds!")
    def _unfollowFeed(self, message: IRCMessage):
        name = " ".join(message.parameterList[1:])
        if name in self.feeds:
            del self.feeds[name]
            self.bot.storage["rss_feeds"] = self.feeds
            return IRCResponse(ResponseType.Say,
                               "Sucessfully unfollowed {}".format(name),
                               message.replyTo)
        else:
            return IRCResponse(ResponseType.Say,
                               "I am not following any feed named {}".format(name),
                               message.replyTo)

    @admin("[RSS] Only my admins may turn RSS feeds on and off!")
    def _toggleFeedSuppress(self, message: IRCMessage):
        name = " ".join(message.parameterList[1:])
        if name in self.feeds:
            self.feeds[name]["suppress"] = not self.feeds[name]["suppress"]
            self.bot.storage["rss_feeds"] = self.feeds
            return IRCResponse(ResponseType.Say,
                               "Successfully {}ed {}".format("suppress" if self.feeds[name]["suppress"] else "unsupress", name),
                               message.replyTo)
        else:
            return IRCResponse(ResponseType.Say,
                               "I am not following any feed named {}".format(name),
                               message.replyTo)

    def _listFeeds(self, message: IRCMessage):
        return IRCResponse(ResponseType.Say,
                           "Currently followed feeds are: {}".format(", ".join(self.feeds.keys())),
                           message.replyTo)


rss = RSS()
