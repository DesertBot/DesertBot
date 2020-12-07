import re
from base64 import b64decode, b64encode
from collections import OrderedDict
from datetime import timedelta
from enum import Enum
from html.entities import name2codepoint

from dateutil.parser import parse
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A

graySplitter = colour(A.normal[' ', A.fg.gray['|'], ' '])


def isNumber(s: str) -> bool:
    """returns True if string s can be cast to a number, False otherwise"""
    try:
        float(s)
        return True
    except ValueError:
        return False


# From this SO answer: http://stackoverflow.com/a/6043797/331047
def splitUTF8(s: str, n: int) -> str:
    """Split UTF-8 s into chunks of maximum byte length n"""
    while len(s) > n:
        k = n
        while (ord(s[k]) & 0xc0) == 0x80:
            k -= 1
        yield s[:k]
        s = s[k:]
    yield s


# Taken from txircd
# https://github.com/ElementalAlchemist/txircd/blob/99e86d53f1fa43e0916497edd08ee3f34f69c4b0/txircd/utils.py#L218
# \x02: bold
# \x1f: underline
# \x16: reverse
# \x1d: italic
# \x0f: normal
# \x03: color stop
# \x03FF: set foreground
# \x03FF,BB: set fore/background
format_chars = re.compile(r'[\x02\x1f\x16\x1d\x0f]|\x03([0-9]{1,2}(,[0-9]{1,2})?)?')


def stripFormatting(text: str) -> str:
    """
    Removes IRC formatting from the provided text.
    """
    return format_chars.sub('', text)


class colour(Enum):
    white = 0
    black = 1
    blue = 2
    green = 3
    ltred = 4
    red = 5
    magenta = 6
    orange = 7
    yellow = 8
    ltgreen = 9
    cyan = 10
    ltcyan = 11
    ltblue = 12
    ltmagenta = 13
    grey = 14
    ltgrey = 15


def formatColour(t: str = "",
                 f: colour = None, b: colour = None,
                 close: bool = True) -> str:
    """
    Applies IRC colour formatting to the provided text (t),
    optionally resetting formatting at the end of it (True by default).
    """
    reset = '\x0f'
    return f"\x03{f.value if f else ''}{f',{b.value}' if b else ''}{t}{reset if close else ''}"


def formatBold(t: str = "", close: bool = True) -> str:
    """
    Applies IRC bold formatting to the provided text (t),
    optionally resetting formatting at the end of it (True by default).
    """
    reset = '\x0f'
    return f"\x02{t}{reset if close else ''}"


def formatUnderline(t: str = "", close: bool = True) -> str:
    """
    Applies IRC underline formatting to the provided text (t),
    optionally resetting formatting at the end of it (True by default).
    """
    reset = '\x0f'
    return f"\x1f{t}{reset if close else ''}"


def formatReverse(t: str = "", close: bool = True) -> str:
    """
    Applies IRC reverse formatting to the provided text (t),
    optionally resetting formatting at the end of it (True by default).
    """
    reset = '\x0f'
    return f"\x16{t}{reset if close else ''}"


def formatItalic(t: str = "", close: bool = True) -> str:
    """
    Applies IRC italic formatting to the provided text (t),
    optionally resetting formatting at the end of it (True by default).
    """
    reset = '\x0f'
    return f"\x1d{t}{reset if close else ''}"


# mostly taken from dave_random's UnsafeBot (whose source is not generally accessible)
def deltaTimeToString(timeDelta: timedelta, resolution: str='m') -> str:
    """
    returns a string version of the given timedelta,
    with a resolution of minutes ('m') or seconds ('s')
    """
    d = OrderedDict()
    d['days'] = timeDelta.days
    d['hours'], rem = divmod(timeDelta.seconds, 3600)
    if resolution == 'm' or resolution == 's':
        d['minutes'], seconds = divmod(rem, 60)
        if resolution == 's':
            d['seconds'] = seconds

    def lex(durationWord, duration):
        if duration == 1:
            return '{0} {1}'.format(duration, durationWord[:-1])
        else:
            return '{0} {1}'.format(duration, durationWord)

    deltaString = ' '.join([lex(word, number) for word, number in d.items() if number > 0])
    return deltaString if len(deltaString) > 0 else 'seconds'


# Taken from PyHeufyBot.
def timeDeltaString(date1, date2):
    delta = date1 - date2
    dayString = "{} day{}".format(delta.days, "" if delta.days == 1 else "s")
    hours = delta.seconds // 3600
    hourString = "{} hour{}".format(hours, "" if hours == 1 else "s")
    minutes = (delta.seconds // 60) % 60
    minuteString = "{} minute{}".format(minutes, "" if minutes == 1 else "s")
    if delta.days == 0 and hours == 0 and minutes == 0:
        return "less than a minute"
    return "{}, {} and {}".format(dayString, hourString, minuteString)


def strftimeWithTimezone(date):
    if isinstance(date, str):
        date = parse(date)

    return date.strftime("%Y-%m-%d %H:%M UTC")


# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
def unescapeXHTML(text: str) -> str:
    def fixup(m):
        escapeText = m.group(0)
        if escapeText[:2] == '&#':
            # character reference
            try:
                if escapeText[:3] == '&#x':
                    return chr(int(escapeText[3:-1], 16))
                else:
                    return chr(int(escapeText[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                escapeText = chr(name2codepoint[escapeText[1:-1]])
            except KeyError:
                pass
        return escapeText  # leave as is
    return re.sub('&#?\w+;', fixup, text)


def strToB64(text: str):
    return b64encode(text.encode('utf-8', 'ignore')).decode('utf-8')


def b64ToStr(text: bytes):
    return b64decode(text).decode('utf-8')
