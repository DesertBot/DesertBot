# -*- coding: utf-8 -*-
"""
Created on Mar 27, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import json
from collections import OrderedDict

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

    def _helpText(self):
        langs = u'/'.join(self._subCommands.keys())
        return u"{1}lang <{0}> <code> - evaluates the given code " \
               u"using a playground service for the given language".format(langs,
                                                                           self.bot.commandChar)

    def _rust(self, code):
        """
        @type code: str
        @rtype str
        """
        template = (
"""fn main() {{
    println!("{{:?}}", {{
        {code}
    }});
}}""")
        code = template.format(code=code)

        url = "https://play.rust-lang.org/execute"
        response = self.bot.moduleHandler.runActionUntilValue('post-url', url, None, {
            "code": code,
            "channel": "stable",
            "mode": "debug",
            "crateType": "bin",
            "tests": False,
            })
        j = json.loads(response.body)

        if j["success"]:
            result = j["stdout"]
        else:
            result = j["stderr"].splitlines()
            result = result[1]

            paste = "{code}\n\n/* --- stderr ---\n{stderr}\n*/\n\n/* --- stdout ---\n{stdout}\n*/"
            paste = paste.format(code=code, stderr=j["stderr"], stdout=j["stdout"])

            url = self.bot.moduleHandler.runActionUntilValue('upload-pasteee',
                                                             paste, result, 10)

            result = "{}\nFull error output: {}".format(result, url)
        return result

    def _haskell(self, code):
        """
        @type code: str
        @rtype str
        """
        url = "https://tryhaskell.org/eval"
        response = self.bot.moduleHandler.runActionUntilValue('post-url', url, {
            "exp": code,
            })
        print(response.body)
        j = json.loads(response.body)

        if "success" in j:
            if j["success"]["stdout"]:
                result = j["success"]["stdout"]
            else:
                result = j["success"]["value"]
        else:
            result = u" | ".join(l.strip() for l in j["error"].splitlines())
        return result

    _subCommands = OrderedDict([
        (u'rust', _rust),
        (u'haskell', _haskell),
        ])

    def _unrecognizedLanguage(self, lang):
        return u"unrecognized language {!r}, " \
               u"available languages are: {}".format(lang, u', '.join(self._subCommands.keys()))

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        if len(message.ParameterList) > 0:
            lang = message.ParameterList[0].lower()
            if lang not in self._subCommands:
                return IRCResponse(ResponseType.Say,
                                   self._unrecognizedLanguage(lang),
                                   message.ReplyTo)
            result = self._subCommands[lang](self, u' '.join(message.ParameterList[1:]))
        else:
            return IRCResponse(ResponseType.Say, self._helpText(), message.ReplyTo)

        return IRCResponse(ResponseType.Say, result, message.ReplyTo)


langPlayground = LangPlayground()
