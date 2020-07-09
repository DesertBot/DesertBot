from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType
from desertbot.utils.string import b64ToStr, strftimeWithTimezone, strToB64, timeDeltaString
from desertbot.utils.timeutils import now
from zope.interface import implementer
import datetime
from dateutil.parser import isoparse
from fnmatch import fnmatch
from pytimeparse.timeparse import timeparse

try:
    import re2
except ImportError:
    import re as re2


@implementer(IPlugin, IModule)
class Tell(BotCommand):
    def triggers(self):
        return ["tell", "pmtell", "pmtellafter", "tellafter", "stells", "rtell", "givetells"]

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
        elif command == "pmtell":
            return "pmtell <user> <message> = Tell the given user(s) a message in a PM when they next speak."
        elif command == "pmtellafter":
            return "pmtellafter <user> <duration> <message> - Tell the given user(s) a message in a PM when they speak " \
                   "after the given duration or on the given date."
        elif command == "stells":
            return "stells - List all tells sent by you that have not yet been delivered."
        elif command == "rtell":
            return "rtell <string> - Remove an undelivered tell sent by you where the message content contains <string>."
        elif command == "givetells":
            return "givetells - Send all currently undelivered tells for the triggering user via PM."
    
    def execute(self, message: IRCMessage):
        params = message.parameterList
        responses = []
        if message.command in ["tell", "tellafter", "pmtell", "pmtellafter"]:
            if len(params) == 0:
                return IRCResponse(ResponseType.Say, "Tell who?", message.replyTo)
            elif len(params) == 1 and message.command in ["tellafter", "pmtellafter"]:
                return IRCResponse(ResponseType.Say, "Tell it when?", message.replyTo)
            elif len(params) == 1 and message.command in ["tell", "pmtell"] or len(params) == 2 and message.command in ["tellafter", "pmtellafter"]:
                return IRCResponse(ResponseType.Say, "Tell {} what?".format(params[0]), message.replyTo)
            sentTells = []
            if message.command in ["tellafter", "pmtellafter"]:
                try:
                    try:  # first, try parsing as an ISO format string
                        date = isoparse(params[1])
                    except ValueError:
                        # if this fails, try parsing as a duration
                        date = now() + datetime.timedelta(seconds=timeparse(params[1]))
                except TypeError:
                    return IRCResponse(ResponseType.Say, "The given duration is invalid.", message.replyTo)
            else:
                date = now()
            for recep in params[0].split("&"):
                if recep.lower() == self.bot.nick.lower():
                    responses.append(IRCResponse(ResponseType.Say,
                                                 "Thanks for telling me that, {}.".format(message.user.nick),
                                                 message.replyTo))
                    continue
                msg = {
                    "to": recep.lower(),
                    "body": strToB64(" ".join(params[1:]) if message.command == "tell" else " ".join(params[2:])),
                    "date": now().isoformat(),
                    "datetoreceive": date.isoformat(),
                    "from": message.user.nick,
                    "source": message.replyTo if message.replyTo[0] in self.bot.supportHelper.chanTypes else "PM"
                }
                # if this is a pmtell or a pmtellafter, send it as a PM
                if self.command[0:2] == "pm":
                    msg["source"] = "PM"

                self.storage["tells"].append(msg)
                sentTells.append(recep.replace("/", " or "))
            if len(sentTells) > 0:
                if message.command == "tellafter":
                    m = "Okay, I'll tell {} that when they speak after {}.".format(" and ".join(sentTells),
                                                                                   strftimeWithTimezone(date))
                else:
                    m = "Okay, I'll tell {} that next time they speak.".format(" and ".join(sentTells))
                responses.append(IRCResponse(ResponseType.Say, m, message.replyTo))
        elif message.command == "stells":
            for tell in self.storage["tells"]:
                if tell["from"].lower() == message.user.nick.lower():
                    responses.append(IRCResponse(ResponseType.Notice, _parseSentTell(tell), message.user.nick))
            if len(responses) == 0:
                return IRCResponse(ResponseType.Notice,
                                   "No undelivered messages sent by you were found.",
                                   message.user.nick)
        elif message.command == "rtell":
            if len(params) == 0:
                return IRCResponse(ResponseType.Say, "Remove what?", message.replyTo)
            tells = [x for x in self.storage["tells"] if x["from"].lower() == message.user.nick.lower()]
            for tell in tells:
                if re2.search(" ".join(params), b64ToStr(tell["body"]), re2.IGNORECASE):
                    self.storage["tells"].remove(tell)
                    m = "Message {!r} was removed from the message database.".format(_parseSentTell(tell))
                    return IRCResponse(ResponseType.Notice, m, message.user.nick)
            else:
                return IRCResponse(ResponseType.Notice,
                                   "No tells matching {!r} were found.".format(" ".join(params)),
                                   message.user.nick)
        return responses

    def _processTells(self, message: IRCMessage, alwaysPM=False):
        if message.command == "givetells":
            alwaysPM = True
        chanTells = []
        pmTells = []
        for tell in [i for i in self.storage["tells"]]: # Iterate over a copy so we don'rlt modify the list we're iterating over
            if not any(fnmatch(message.user.nick.lower(), r) for r in tell["to"].split("/")):
                continue
            if now().isoformat() < tell["datetoreceive"]:
                continue
            if not alwaysPM and tell["source"][0] in self.bot.supportHelper.chanTypes and len(chanTells) < 3:
                if tell["source"] == message.replyTo:
                    chanTells.append(tell)
                    self.storage["tells"].remove(tell)
            elif alwaysPM or tell["source"][0] not in self.bot.supportHelper.chanTypes:
                pmTells.append(tell)
                self.storage["tells"].remove(tell)

        responses = []
        for tell in chanTells:
            responses.append(IRCResponse(ResponseType.Say, _parseTell(message.user.nick, tell), message.replyTo))
        for tell in pmTells:
            responses.append(IRCResponse(ResponseType.Say, _parseTell(message.user.nick, tell), message.user.nick))
        return responses


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


tellCommand = Tell()
