# -*- coding: utf-8 -*-
"""
Created on Mar 27, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import zlib

import requests

from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class LangPlayground(BotCommand):
    def triggers(self):
        return ['lang']

    def help(self, query):
        """
        @type query: list[str]
        @rtype str
        """
        return self._helpText()

    def onLoad(self):
        self.languages = None
        self.templates = {
            'rust':
"""fn main() {{
    println!("{{:?}}", {{
        {code}
    }});
}}""",
            'cpp-clang':
"""#include <iostream>
int main() {{
    std::cout << ({code}) << std::endl;
}}""",
            'cpp-gcc':
"""#include <iostream>
int main() {{
    std::cout << ({code}) << std::endl;
}}"""
        }

    def _helpText(self):
        return u"{}lang <lang> <code> - evaluates the given code using TryItOnline.net".format(self.bot.commandChar)

    def _tio(self, lang, code):
        """
        @type lang: str
        @type code: str
        @rtype str
        """
        if self.languages == None:
            langUrl = "https://raw.githubusercontent.com/TryItOnline/tryitonline/master/usr/share/tio.run/languages.json"
            response = requests.get(langUrl)
            self.languages = response.json().keys()

        if lang not in self.languages:
            return "[Language {!r} unknown on TryItOnline.net]"

        if lang in self.templates:
            code = self.templates[lang].format(code=code)

        request = [{'command': 'V', 'payload': {'lang': [lang]}},
                   {'command': 'F', 'payload': {'.code.tio': code}},
                   {'command': 'RC'}]
        req = b''
        for instr in request:
            req += instr['command'].encode()
            if 'payload' in instr:
                [(name, value)] = instr['payload'].items()
                req += b'%s\0' % name.encode()
                if type(value) == str:
                    value = value.encode()
                req += b'%u\0' % len(value)
                if type(value) != bytes:
                    value = '\0'.join(value).encode() + b'\0'
                req += value
        req_raw = zlib.compress(req, 9)[2:-4]

        url = "https://tio.run/cgi-bin/static/b666d85ff48692ae95f24a66f7612256-run/93d25ed21c8d2bb5917e6217ac439d61"
        res = requests.post(url, data=req_raw)
        res = zlib.decompress(res.content, 31)
        delim = res[:16]
        ret = res[16:].split(delim)
        count = len(ret) >> 1
        returned, errors = ret[:count], ret[count:]
        errors = errors[0].decode('utf-8', 'ignore')
        # this heuristic is guesstimated from python3, cpp-gcc, rust, and haskell output
        # potential improvement: expected amount of lines for various languages
        if len(errors.splitlines()[0:-5]) > 2:
            paste = "{code}\n\n/* --- stderr ---\n{stderr}\n*/".format(code=code, stderr=errors)
            url = self.bot.moduleHandler.runActionUntilValue('upload-pasteee',
                                                             paste, "TIO stderr", 10)
            error = "Errors occurred! Output: {url}".format(url=url)
            if lang in self.templates:
                error += " (language uses a template, see link for framing code)"
            return error

        return u' | '.join(r.decode('utf-8', 'ignore') for r in returned)

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        if len(message.ParameterList) > 0:
            lang = message.ParameterList[0].lower()
            result = self._tio(lang, u' '.join(message.ParameterList[1:]))
        else:
            return IRCResponse(ResponseType.Say, self._helpText(), message.ReplyTo)

        return IRCResponse(ResponseType.Say, result, message.ReplyTo)


langPlayground = LangPlayground()
