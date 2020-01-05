from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot


class OutputHandler(object):
    def __init__(self, bot: 'DesertBot'):
        self.bot = bot

    def cmdCAP_END(self):
        self.bot.sendMessage('CAP', 'END')

    def cmdCAP_LS(self):
        self.bot.sendMessage('CAP', 'LS', '302')

    def cmdCAP_REQ(self, toRequest: str):
        self.bot.sendMessage('CAP', 'REQ', toRequest)

    def cmdINVITE(self, user: str, channel: str) -> None:
        self.bot.sendMessage("INVITE", user, channel)

    def cmdJOIN(self, channel: str, key: str = "") -> None:
        if channel[0] not in self.bot.supportHelper.chanTypes:
            channel = "#{}".format(channel)
        self.bot.sendMessage("JOIN", channel, key)

    def cmdKICK(self, channel: str, user: str, reason: str = "") -> None:
        self.bot.sendMessage("KICK", channel, user, reason)

    def cmdMODE(self, target: str, modes: str = "", params: str = "") -> None:
        if params and isinstance(params, str):
            params = [params]
        self.bot.sendMessage("MODE", target, modes, params)

    def cmdNAMES(self, channel: str) -> None:
        self.bot.sendMessage("NAMES", channel)

    def cmdNICK(self, nick: str) -> None:
        self.bot.sendMessage("NICK", nick)

    def cmdNOTICE(self, target: str, message: str) -> None:
        self.bot.sendMessage("NOTICE", target, message)

    def cmdPART(self, channel: str, reason: str = "") -> None:
        self.bot.sendMessage("PART", channel, reason)

    def cmdPASS(self, password: str) -> None:
        self.bot.sendMessage("PASS", password)

    def cmdPING(self, message: str) -> None:
        self.bot.sendMessage("PING", message)

    def cmdPRIVMSG(self, target: str, message: str) -> None:
        self.bot.sendMessage("PRIVMSG", target, message)

    def cmdPONG(self, message: str) -> None:
        self.bot.sendMessage("PONG", message)

    def cmdTOPIC(self, channel: str, topic: str) -> None:
        self.bot.sendMessage("TOPIC", channel, topic)

    def cmdQUIT(self, reason: str) -> None:
        self.bot.sendMessage("QUIT", reason)

    def cmdUSER(self, ident: str, gecos: str) -> None:
        # RFC2812 allows usermodes to be set, but this isn't implemented much in IRCds at all.
        # Pass 0 for usermodes instead.
        self.bot.sendMessage("USER", ident, "0", "*", gecos)

    def cmdWHO(self, mask: str) -> None:
        if not mask:
            mask = "*"
        self.bot.sendMessage("WHO", mask)

    def ctcpACTION(self, target: str, action: str) -> None:
        # We're keeping most CTCP stuff out of the core, but actions are used a lot and don't really belong in CTCP.
        self.cmdPRIVMSG(target, "\x01ACTION {}\x01".format(action))
