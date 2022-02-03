import datetime
from fnmatch import fnmatch

from dateutil.parser import isoparse
from pytimeparse.timeparse import timeparse
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType
from desertbot.utils.string import b64ToStr, strftimeWithTimezone, strToB64, timeDeltaString
from desertbot.utils.timeutils import now

try:
    import re2
except ImportError:
    import re as re2


@implementer(IPlugin, IModule)
class Tell(BotCommand):
    def triggers(self):
        return ["tell", "tellafter", "stells", "rtell"]

    def actions(self):
        return super(Tell, self).actions() + [('action-channel', 5, self._processTells),
                                              ('action-user', 5, self._processTells),
                                              ('message-channel', 5, self._processTells),
                                              ('message-user', 5, self._processTells)]

    def onLoad(self):
        if "tells" not in self.storage:
            self.storage["tells"] = []

    def help(self, query):
        command = query[0].lower()
        if command == "tell":
            return "tell <user> <message> = Tell the given user(s) a message when they next speak."
        elif command == "tellafter":
            return "tellafter <user> <duration> <message> - Tell the given user(s) a message when they speak " \
                   "after the given duration or on the given date."
        elif command == "stells":
            return "stells - List all tells sent by you that have not yet been delivered."
        elif command == "rtell":
            return "rtell <string> - Remove an undelivered tell sent by you where the message content contains <string>."
    
    def execute(self, message: IRCMessage):
        params = message.parameterList
        responses = []
        if message.command == "tell" or message.command == "tellafter":
            if len(params) == 0:
                return IRCResponse("Tell who?", message.replyTo)
            elif len(params) == 1 and message.command == "tellafter":
                return IRCResponse("Tell it when?", message.replyTo)
            elif len(params) == 1 and message.command == "tell" or len(params) == 2 and message.command == "tellafter":
                return IRCResponse("Tell {} what?".format(params[0]), message.replyTo)
            sentTells = []
            if message.command == "tellafter":
                try:
                    try:  # first, try parsing as an ISO format string
                        date = isoparse(params[1])
                    except ValueError:
                        # if this fails, try parsing as a duration
                        date = now() + datetime.timedelta(seconds=timeparse(params[1]))
                except TypeError:
                    return IRCResponse("The given duration is invalid.", message.replyTo)
            else:
                date = now()
            url = self.mhRunActionUntilValue("urlfollow", message)
            if url:
                responses.append(IRCResponse(url, message.replyTo))
            for recep in params[0].split("&"):
                if recep.lower() == self.bot.nick.lower():
                    responses.append(
                        IRCResponse("Thanks for telling me that, {}.".format(message.user.nick), message.replyTo))
                    continue
                msg = {
                    "to": recep.lower(),
                    "body": strToB64(" ".join(params[1:]) if message.command == "tell" else " ".join(params[2:])),
                    "date": now().isoformat(),
                    "datetoreceive": date.isoformat(),
                    "from": message.user.nick,
                    "source": message.replyTo if message.replyTo[0] in self.bot.supportHelper.chanTypes else "PM"
                }
                self.storage["tells"].append(msg)
                sentTells.append(recep.replace("/", " or "))
            if len(sentTells) > 0:
                if message.command == "tellafter":
                    m = "Okay, I'll tell {} that when they speak after {}.".format(" and ".join(sentTells),
                                                                                   strftimeWithTimezone(date))
                else:
                    m = "Okay, I'll tell {} that next time they speak.".format(" and ".join(sentTells))
                responses.append(IRCResponse(m, message.replyTo))
        elif message.command == "stells":
            for tell in self.storage["tells"]:
                if tell["from"].lower() == message.user.nick.lower():
                    responses.append(IRCResponse(_parseSentTell(tell), message.user.nick, ResponseType.Notice))
            if len(responses) == 0:
                return IRCResponse("No undelivered messages sent by you were found.", message.user.nick,
                                   ResponseType.Notice)
        elif message.command == "rtell":
            if len(params) == 0:
                return IRCResponse("Remove what?", message.replyTo)
            tells = [x for x in self.storage["tells"] if x["from"].lower() == message.user.nick.lower()]
            for tell in tells:
                if re2.search(" ".join(params), b64ToStr(tell["body"]), re2.IGNORECASE):
                    self.storage["tells"].remove(tell)
                    m = "Message {!r} was removed from the message database.".format(_parseSentTell(tell))
                    return IRCResponse(m, message.user.nick, ResponseType.Notice)
            else:
                return IRCResponse("No tells matching {!r} were found.".format(" ".join(params)), message.user.nick,
                                   ResponseType.Notice)
        return responses

    def _processTells(self, message: IRCMessage):
        chanTells = []
        chanFollows = []
        pmTells = []
        pmFollows = []
        for tell in [i for i in self.storage["tells"]]: # Iterate over a copy so we don'rlt modify the list we're iterating over
            if not any(fnmatch(message.user.nick.lower(), r) for r in tell["to"].split("/")):
                continue
            if now().isoformat() < tell["datetoreceive"]:
                continue
            if tell["source"][0] in self.bot.supportHelper.chanTypes and len(chanTells) < 3:
                if tell["source"] == message.replyTo:
                    follows = self._tryFollowURLinTell(message, tell)
                    if follows:
                        chanFollows.append(follows)
                    chanTells.append(tell)
                    self.storage["tells"].remove(tell)
            elif tell["source"][0] not in self.bot.supportHelper.chanTypes:
                follows = self._tryFollowURLinTell(message, tell)
                if follows:
                    pmFollows.append(follows)
                pmTells.append(tell)
                self.storage["tells"].remove(tell)

        responses = []
        for tell in chanTells:
            responses.append(IRCResponse(_parseTell(message.user.nick, tell), message.replyTo))
        for tell in pmTells:
            responses.append(IRCResponse(_parseTell(message.user.nick, tell), message.user.nick))
        for follow in chanFollows:
            text, url = follow
            responses.append(IRCResponse(text, message.replyTo, metadata={'var': {'urlfollowURL': url}}))
        for follow in pmFollows:
            text, url = follow
            responses.append(IRCResponse(text, message.user.nick, metadata={'var': {'urlfollowURL': url}}))

        # TODO: what happens if responses contains more than 3 whose target is message.replyTo? flood protection trip??
        return responses

    def _tryFollowURLinTell(self, message: IRCMessage, tell):
        tellURL = _getURL(tell["body"])
        if tellURL:
            follows = self.bot.moduleHandler.runActionUntilValue('urlfollow', message, tellURL)
            if follows:
                return follows


def _parseTell(nick, tell):
    return "{}: {} < From {} ({} ago).".format(nick,
                                               b64ToStr(tell["body"]),
                                               tell["from"],
                                               timeDeltaString(now(), isoparse(tell["date"])))


def _parseSentTell(tell):
    return "{} < Sent to {} on {}, to be received on {} in {}.".format(b64ToStr(tell["body"]), tell["to"],
                                                                       strftimeWithTimezone(tell["date"]),
                                                                       strftimeWithTimezone(tell["datetoreceive"]),
                                                                       tell["source"])


def _getURL(tellBody):
    tellStr = b64ToStr(tellBody)
    match = re2.search(r'(?P<url>(https?://|www\.)[^\s]+)', tellStr, re2.IGNORECASE)
    if match:
        return match.group('url')


tellCommand = Tell()
