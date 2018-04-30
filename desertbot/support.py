from desertbot.ircbase import ModeType


class ISupport(object):
    def __init__(self):
        self.serverName = None
        self.serverVersion = None
        self.network = None
        self.rawTokens = {}
        self.userModes = "iosw"
        self.chanModes = {
            "b": ModeType.LIST,
            "k": ModeType.PARAM_SET_UNSET,
            "l": ModeType.PARAM_SET,
            "m": ModeType.NO_PARAM,
            "n": ModeType.NO_PARAM,
            "p": ModeType.NO_PARAM,
            "s": ModeType.NO_PARAM,
            "t": ModeType.NO_PARAM
        }
        self.statusModes = {
            "o": "@",
            "v": "+"
        }
        self.statusSymbols = {
            "@": "o",
            "+": "v"
        }
        self.statusOrder = "ov"
        self.chanTypes = "#"
