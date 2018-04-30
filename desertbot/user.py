from typing import Optional


class IRCUser(object):
    def __init__(self, nick: str, ident: Optional[str] = None, host: Optional[str] = None):
        self.nick = nick
        self.ident = ident
        self.host = host
        self.gecos = None
        self.server = None
        self.hops = 0
        self.isOper = False
        self.isAway = False
        self.awayMessage = None
        self.account = None

    def fullUserPrefix(self) -> str:
        return "{}!{}@{}".format(self.nick, self.ident, self.host)
