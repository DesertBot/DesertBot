# -*- coding: utf-8 -*-
"""
Created on Mar 27, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer
from typing import List

import zlib
from collections import OrderedDict

import requests

from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class LangPlayground(BotCommand):
    def triggers(self):
        return self.commands.keys()

    def help(self, query: List[str]) -> str:
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
        return u"{}lang <lang> <code> - evaluates the given code using https://tio.run".format(self.bot.commandChar)

    def _tio(self, lang: str, code: str, userInput: str="") -> str:
        if self.languages == None:
            langUrl = "https://raw.githubusercontent.com/TryItOnline/tryitonline/master/usr/share/tio.run/languages.json"
            response = requests.get(langUrl)
            self.languages = response.json().keys()

        if lang not in self.languages:
            langList = self.bot.moduleHandler.runActionUntilValue('closest-matches',
                                                                  lang,
                                                                  self.languages,
                                                                  10,
                                                                  0.8)
            langString = ", ".join(langList)
            return "[Language {!r} unknown on tio.run. Perhaps you want: {}]".format(lang,
                                                                                     langString)

        request = [{'command': 'V', 'payload': {'lang': [lang]}},
                   {'command': 'F', 'payload': {'.code.tio': code}},
                   {'command': 'F', 'payload': {'.input.tio': userInput}},
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
        # Grab and check the exit code
        if int(errors.splitlines()[-1][len("Exit code: ")-1:]) != 0:
            paste = ("{code}\n"
                     "\n"
                     "/* --- stdout ---\n"
                     "{stdout}\n"
                     "*/\n"
                     "\n"
                     "/* --- stderr ---\n"
                     "{stderr}\n"
                     "*/".format(code=code,
                                 stdout=returned[0].decode('utf-8', 'ignore'),
                                 stderr=errors))
            url = self.bot.moduleHandler.runActionUntilValue('upload-pasteee',
                                                             paste,
                                                             "TIO stderr", 10)
            error = "Errors occurred! Output: {url}".format(url=url)
            if lang in self.templates:
                error += " (language uses a template, see link for framing code)"
            return error

        return u' | '.join(r.decode('utf-8', 'ignore') for r in returned)

    def _lang(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            lang = message.parameterList[0].lower()
            code = u' '.join(message.parameterList[1:])
            if lang in self.templates:
                code = self.templates[lang].format(code=code)
            result = self._tio(lang, code)
            return IRCResponse(ResponseType.Say,
                               result.replace("\n", " "),
                               message.replyTo)
        else:
            return IRCResponse(ResponseType.Say,
                               self._helpText(),
                               message.replyTo)

    def _langurl(self, message: IRCMessage):
        if len(message.parameterList) > 1:
            lang = message.parameterList[0].lower()
            url = message.parameterList[1]
            userInput = " ".join(message.parameterList[2:])
            page = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)
            code = page.body
            result = self._tio(lang, code, userInput)
            return IRCResponse(ResponseType.Say,
                               result.replace("\n", " "),
                               message.replyTo)
        else:
            return IRCResponse(ResponseType.Say,
                               self._helpText(),
                               message.replyTo)

    commands = OrderedDict([
        (u'lang', _lang),
        (u'langurl', _langurl)])

    def execute(self, message: IRCMessage):
        return self.commands[message.command.lower()](self, message)


langPlayground = LangPlayground()
