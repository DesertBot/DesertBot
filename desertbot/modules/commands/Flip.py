"""
Created on Nov 07, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse


@implementer(IPlugin, IModule)
class Flip(BotCommand):
    def triggers(self):
        return ['flip']

    def help(self, query):
        return 'flip <text> - flips the text given to it'

    def onLoad(self):
        table = {
            'a': 'ɐ',    'A': '∀',    '0': '0',    '‿': '⁀',
            'b': 'q',    'B': 'ᗺ',    '1': '⇂',    '🙂': '🙃',
            'c': 'ɔ',    'C': 'Ↄ',    '2': 'ᘔ',
            'd': 'p',    'D': '◖',    '3': 'Ɛ',
            'e': 'ǝ',    'E': 'Ǝ',    '4': 'ᔭ',
            'f': 'ɟ',    'F': 'Ⅎ',    '5': '5',
            'g': 'ƃ',    'G': '⅁',    '6': '9',
            'h': 'ɥ',    'H': 'H',    '7': 'Ɫ',
            'i': 'ı',    'I': 'I',    '8': '8',
            'j': 'ɾ',    'J': 'ſ',    '9': '6',
            'k': 'ʞ',    'K': '⋊',    '.': '˙',
            'l': 'ʃ',    'L': '⅂',    ',': "'",
            'm': 'ɯ',    'M': 'W',    "'": ',',
            'n': 'u',    'N': 'ᴎ',    '"': '„',
            'o': 'o',    'O': 'O',    '!': '¡',
            'p': 'd',    'P': 'Ԁ',    '?': '¿',
            'q': 'b',    'Q': 'Ό',    '<': '>',
            'r': 'ɹ',    'R': 'ᴚ',    '(': ')',
            's': 's',    'S': 'S',    '[': ']',
            't': 'ʇ',    'T': '⊥',    '{': '}',
            'u': 'n',    'U': '∩',    '_': '‾',
            'v': 'ʌ',    'V': 'Λ',    '^': '∨',
            'w': 'ʍ',    'W': 'M',    ';': '؛',
            'x': 'x',    'X': 'X',    '&': '⅋',
            'y': 'ʎ',    'Y': '⅄',    '⁅': '⁆',
            'z': 'z',    'Z': 'Z',    '∴': '∵',
        }
        # Create and append the inverse dictionary
        table.update({v: k for k, v in table.items()})
        self.translation = {ord(k): v for k, v in table.items()}

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            translated = message.parameters.translate(self.translation)
            reversed = translated[::-1]
            return IRCResponse(reversed, message.replyTo)
        else:
            return IRCResponse('Flip what?', message.replyTo)


flip = Flip()
