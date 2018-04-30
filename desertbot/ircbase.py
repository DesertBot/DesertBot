from enum import Enum
from twisted.protocols.basic import LineOnlyReceiver
from typing import Any, Dict, List, Optional, Tuple, Union


class ModeType(Enum):
    LIST = 0,
    PARAM_SET = 1,
    PARAM_SET_UNSET = 2,
    NO_PARAM = 3


# Taken from txircd:
# https://github.com/ElementalAlchemist/txircd/blob/26dd2ee9d21b846cbd33cd5bd6e8abe7df712034/txircd/ircbase.py
class IRCBase(LineOnlyReceiver):
    delimiter = b"\n"  # Default to splitting by \n, and then we'll also split \r in the handler

    def lineReceived(self, data: bytes) -> None:
        for lineRaw in data.split(b"\r"):
            line = lineRaw.decode("utf-8", "replace")
            command, params, prefix, tags = self._parseLine(line)
            if command:
                self.handleCommand(command, params, prefix, tags)

    def _parseLine(self, line: str) -> Union[Tuple[str, List[str], str, Dict[str, Optional[str]]], Tuple[None, None, None, None]]:
        line = line.replace("\0", "")
        if not line:
            return None, None, None, None

        if line[0] == "@":
            if " " not in line:
                return None, None, None, None
            tagLine, line = line.split(" ", 1)
            tags = self._parseTags(tagLine[1:])
        else:
            tags = {}

        prefix = None
        if line[0] == ":":
            if " " not in line:
                return None, None, None, None
            prefix, line = line.split(" ", 1)
            prefix = prefix[1:]

        if " :" in line:
            linePart, lastParam = line.split(" :", 1)
        else:
            linePart = line
            lastParam = None
        if not linePart:
            return None, None, None, None

        if " " in linePart:
            command, paramLine = linePart.split(" ", 1)
            params = paramLine.split(" ")
        else:
            command = linePart
            params = []
        while "" in params:
            params.remove("")
        if lastParam is not None:
            params.append(lastParam)
        return command.upper(), params, prefix, tags

    def _parseTags(self, tagLine: str) -> Dict[str, Optional[str]]:
        tags = {}
        for tagval in tagLine.split(";"):
            if not tagval:
                continue
            if "=" in tagval:
                tag, escapedValue = tagval.split("=", 1)
                escaped = False
                valueChars = []
                for char in escapedValue:
                    if escaped:
                        if char == "\\":
                            valueChars.append("\\")
                        elif char == ":":
                            valueChars.append(";")
                        elif char == "r":
                            valueChars.append("\r")
                        elif char == "n":
                            valueChars.append("\n")
                        elif char == "s":
                            valueChars.append(" ")
                        else:
                            valueChars.append(char)
                        escaped = False
                        continue
                    if char == "\\":
                        escaped = True
                        continue
                    valueChars.append(char)
                value = "".join(valueChars)
            else:
                tag = tagval
                value = None
            tags[tag] = value
        return tags

    def handleCommand(self, command: str, params: List[str], prefix: str, tags: Dict[str, Optional[str]]) -> None:
        pass

    def sendMessage(self, command: str, *params: str, **kw: Any) -> None:
        if "tags" in kw:
            tags = self._buildTagString(kw["tags"])
        else:
            tags = None
        if "prefix" in kw:
            prefix = kw["prefix"]
        else:
            prefix = None
        if "alwaysPrefixLastParam" in kw:
            alwaysPrefixLastParam = kw["alwaysPrefixLastParam"]
        else:
            alwaysPrefixLastParam = False
        params = list(params)
        if params:
            for param in params[:-1]:
                for badChar in (" ", "\r", "\n", "\0"):
                    if badChar in param:
                        raise ValueError("Illegal character {!r} found in parameter {!r}".format(badChar, param))
                if param and param[0] == ":":
                    raise ValueError("Parameter {!r} formatted like a final parameter, but it isn't last".format(param))
            for badChar in ("\r", "\n", "\0"):
                if badChar in params[-1]:
                    raise ValueError("Illegal character {!r} found in parameter {!r}".format(badChar, params[-1]))
            if alwaysPrefixLastParam or not params[-1] or " " in params[-1] or params[-1][0] == ":":
                params[-1] = ":{}".format(params[-1])
        lineToSend = ""
        if tags:
            lineToSend += "@{} ".format(tags)
        if prefix:
            lineToSend += ":{} ".format(prefix)
        lineToSend += "{} {}".format(command, " ".join(params))
        self.sendLine(lineToSend.replace("\0", ""))

    def _buildTagString(self, tags: Dict[str, Optional[str]]) -> str:
        tagList = []
        for tag, value in tags.items():
            for char in tag:
                if not char.isalnum() and char not in ("-", "/", "."):
                    raise ValueError("Illegal character {!r} found in key {!r}".format(char, tag))
            if value is None:
                tagList.append(tag)
            else:
                if "\0" in value:
                    raise ValueError("Illegal character '\\0' found in value for key {!r}".format(tag))
                escapedValue = value.replace("\\", "\\\\").replace(";", "\\:").replace(" ", "\\s").replace("\r", "\\r").replace("\n", "\\n")
                tagList.append("{}={}".format(tag, escapedValue))
        return ";".join(tagList)

    def sendLine(self, line: str) -> None:
        self.transport.write("{}\r\n".format(line).encode("utf-8"))
