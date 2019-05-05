from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType
from desertbot.utils.string import b64ToStr, strftimeWithTimezone, strToB64, timeDeltaString
from desertbot.utils.timeutils import now
from zope.interface import implementer
from datetime import timedelta
from dateutil.parser import parse
from fnmatch import fnmatch
from pytimeparse.timeparse import timeparse

try:
    import re2
except ImportError:
    import re as re2


@implementer(IPlugin, IModule)
class Tell(BotCommand):
    def triggers(self):
        return ["tell", "tellafter", "stells", "rtell"]

    def actions(self):
        return super(Tell, self).actions() + [('action-channel', 1, self._processTells),
                                              ('action-user', 1, self._processTells),
                                              ('message-channel', 1, self._processTells),
                                              ('message-user', 1, self._processTells)]

    def onLoad(self):
        if "tells" not in self.bot.storage:
            self.bot.storage["tells"] = []
        self.tells = self.bot.storage["tells"]

    def help(self, query):
        command = query[0].lower()
        if command == "tell":
            return "tell <user> <message> = Tell the given user(s) a message when they next speak."
        elif command == "tellafter":
            return "tellafter <user> <duration> <message> - Tell the given user(s) a message when they speak " \
                   "after the given duration or on the given date."
        elif command == "stells":
            return "stells - List all tells sent by you that have not yet been received."
        elif command == "rtell":
            return "rtell <message> - Remove the earlier message sent by you that matches."
    
    def execute(self, message: IRCMessage):
        params = message.parameterList
        responses = []
        if message.command == "tell" or message.command == "tellafter":
            if len(params) == 0 or len(params) == 1:
                return IRCResponse(ResponseType.Say, "Tell who?", message.replyTo)
            elif len(params) == 1 and message.command == "tellafter":
                return IRCResponse(ResponseType.Say, "Tell it when?", message.replyTo)
            elif len(params) == 1 or len(params) == 2 and message.command == "tellafter":
                return IRCResponse(ResponseType.Say, "Tell {} what?".format(params[0]), message.replyTo)
            sentTells = []
            if message.command == "tellafter":
                date = now() + timedelta(seconds=timeparse(params[1]))
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
                self.tells.append(msg)
                sentTells.append(recep.replace("/", " or "))
            if len(sentTells) > 0:
                self.bot.storage["tells"] = self.tells
                if message.command == "tellafter":
                    m = "Okay, I'll tell {} that when they speak after {}.".format("&".join(sentTells),
                                                                                   strftimeWithTimezone(date))
                else:
                    m = "Okay, I'll tell {} that next time they speak.".format("&".join(sentTells))
                responses.append(IRCResponse(ResponseType.Say, m, message.replyTo))
        elif message.command == "stells":
            for tell in self.tells:
                if tell["from"].lower() == message.user.nick.lower():
                    responses.append(IRCResponse(ResponseType.Notice, _parseSentTell(tell), message.user.nick))
            if len(responses) == 0:
                return IRCResponse(ResponseType.Notice,
                                   "No undelivered messages sent by you were found.",
                                   message.user.nick)
        elif message.command == "rtell":
            if len(params) == 0:
                return IRCResponse(ResponseType.Say, "Remove what?", message.replyTo)
            tells = [x for x in self.tells if x["from"].lower() == message.user.nick.lower()]
            for tell in tells:
                if re2.search(" ".join(params), b64ToStr(tell["body"]), re2.IGNORECASE):
                    self.tells.remove(tell)
                    self.bot.storage["tells"] = self.tells
                    m = "Message {!r} was removed from the message database.".format(_parseSentTell(tell))
                    return IRCResponse(ResponseType.Notice, m, message.user.nick)
            else:
                return IRCResponse(ResponseType.Notice,
                                   "No tells matching {!r} were found.".format(" ".join(params)),
                                   message.user.nick)
        return responses

    def _processTells(self, message: IRCMessage):
        chanTells = []
        pmTells = []
        for tell in self.tells:
            if not any(fnmatch(message.user.nick.lower(), r) for r in tell["to"].split("/")):
                continue
            if now().isoformat() < tell["datetoreceive"]:
                continue
            if tell["source"][0] in self.bot.supportHelper.chanTypes and len(chanTells) < 3:
                if tell["source"] == message.replyTo:
                    chanTells.append(tell)
                    self.tells.remove(tell)
            elif tell["source"][0] not in self.bot.supportHelper.chanTypes:
                pmTells.append(tell)
                self.tells.remove(tell)

        responses = []
        for tell in chanTells:
            responses.append(IRCResponse(ResponseType.Say, _parseTell(message.user.nick, tell), message.replyTo))
        for tell in pmTells:
            responses.append(IRCResponse(ResponseType.Say, _parseTell(message.user.nick, tell), message.user.nick))
        if len(chanTells) > 0 or len(pmTells) > 0:
            self.bot.storage["tells"] = self.tells
        return responses


def _parseTell(nick, tell):
    return "{}: {} < From {} ({} ago).".format(nick,
                                               b64ToStr(tell["body"]),
                                               tell["from"],
                                               timeDeltaString(now(), parse(tell["date"])))


def _parseSentTell(tell):
    return "{} < Sent to {} on {}, to be received on {} in {}.".format(b64ToStr(tell["body"]), tell["to"],
                                                                       strftimeWithTimezone(tell["date"]),
                                                                       strftimeWithTimezone(tell["datetoreceive"]),
                                                                       tell["source"])


tellCommand = Tell()
