# -*- coding: utf-8 -*-
"""
Created on Nov 07, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Flip(BotCommand):
    def triggers(self):
        return ['flip']

    def help(self, query):
        return 'flip <text> - flips the text given to it'

    def onLoad(self):
        table = {
            'a': 'ɐ',    'A': '∀',
            'b': 'q',    'B': 'ᗺ',
            'c': 'ɔ',    'C': 'Ↄ',
            'd': 'p',    'D': '◖',
            'e': 'ǝ',    'E': 'Ǝ',
            'f': 'ɟ',    'F': 'Ⅎ',
            'g': 'ƃ',    'G': '⅁',
            'h': 'ɥ',    'H': 'H',
            'i': 'ı',    'I': 'I',
            'j': 'ɾ',    'J': 'ſ',
            'k': 'ʞ',    'K': '⋊',
            'l': 'ʃ',    'L': '⅂',
            'm': 'ɯ',    'M': 'W',
            'n': 'u',    'N': 'ᴎ',
            'o': 'o',    'O': 'O',
            'p': 'd',    'P': 'Ԁ',
            'q': 'b',    'Q': 'Ό',
            'r': 'ɹ',    'R': 'ᴚ',
            's': 's',    'S': 'S',
            't': 'ʇ',    'T': '⊥',
            'u': 'n',    'U': '∩',
            'v': 'ʌ',    'V': 'Λ',
            'w': 'ʍ',    'W': 'M',
            'x': 'x',    'X': 'X',
            'y': 'ʎ',    'Y': '⅄',
            'z': 'z',    'Z': 'Z',
            '0': '0',
            '1': '⇂',
            '2': 'ᘔ',
            '3': 'Ɛ',
            '4': 'ᔭ',
            '5': '5',
            '6': '9',
            '7': 'Ɫ',
            '8': '8',
            '9': '6',
            '.': '˙',
            ',': "'",
            "'": ',',
            '"': '„',
            '!': '¡',
            '?': '¿',
            '<': '>',
            '(': ')',
            '[': ']',
            '{': '}',
            '_': '‾',
            '^': '∨',
            ';': '؛',
            '&': '⅋',
            '⁅': '⁆',
            '∴': '∵',
            '‿': '⁀',
        }
        # Create and append the inverse dictionary
        table.update({v: k for k, v in table.items()})
        self.translation = {ord(k): v for k, v in table.items()}

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            translated = message.parameters.translate(self.translation)
            reversed = translated[::-1]
            return IRCResponse(ResponseType.Say, reversed, message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, 'Flip what?', message.replyTo)


flip = Flip()
