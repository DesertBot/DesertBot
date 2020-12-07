"""
Created on Oct 22, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Style(BotCommand):
    def triggers(self):
        return ['style']

    def help(self, query):
        return ('style <style> <text> - converts the given text to the given unicode style | '
                'options are: {}'.format('/'.join(self.styles)))

    def onLoad(self):
        self.styles = {
            'script': {
                ord('a'): '𝓪',    ord('A'): '𝓐',
                ord('b'): '𝓫',    ord('B'): '𝓑',
                ord('c'): '𝓬',    ord('C'): '𝓒',
                ord('d'): '𝓭',    ord('D'): '𝓓',
                ord('e'): '𝓮',    ord('E'): '𝓔',
                ord('f'): '𝓯',    ord('F'): '𝓕',
                ord('g'): '𝓰',    ord('G'): '𝓖',
                ord('h'): '𝓱',    ord('H'): '𝓗',
                ord('i'): '𝓲',    ord('I'): '𝓘',
                ord('j'): '𝓳',    ord('J'): '𝓙',
                ord('k'): '𝓴',    ord('K'): '𝓚',
                ord('l'): '𝓵',    ord('L'): '𝓛',
                ord('m'): '𝓶',    ord('M'): '𝓜',
                ord('n'): '𝓷',    ord('N'): '𝓝',
                ord('o'): '𝓸',    ord('O'): '𝓞',
                ord('p'): '𝓹',    ord('P'): '𝓟',
                ord('q'): '𝓺',    ord('Q'): '𝓠',
                ord('r'): '𝓻',    ord('R'): '𝓡',
                ord('s'): '𝓼',    ord('S'): '𝓢',
                ord('t'): '𝓽',    ord('T'): '𝓣',
                ord('u'): '𝓾',    ord('U'): '𝓤',
                ord('v'): '𝓿',    ord('V'): '𝓥',
                ord('w'): '𝔀',    ord('W'): '𝓦',
                ord('x'): '𝔁',    ord('X'): '𝓧',
                ord('y'): '𝔂',    ord('Y'): '𝓨',
                ord('z'): '𝔃',    ord('Z'): '𝓩',
            },
            'gothic': {
                ord('a'): '𝖆',    ord('A'): '𝕬',
                ord('b'): '𝖇',    ord('B'): '𝕭',
                ord('c'): '𝖈',    ord('C'): '𝕮',
                ord('d'): '𝖉',    ord('D'): '𝕯',
                ord('e'): '𝖊',    ord('E'): '𝕰',
                ord('f'): '𝖋',    ord('F'): '𝕱',
                ord('g'): '𝖌',    ord('G'): '𝕲',
                ord('h'): '𝖍',    ord('H'): '𝕳',
                ord('i'): '𝖎',    ord('I'): '𝕴',
                ord('j'): '𝖏',    ord('J'): '𝕵',
                ord('k'): '𝖐',    ord('K'): '𝕶',
                ord('l'): '𝖑',    ord('L'): '𝕷',
                ord('m'): '𝖒',    ord('M'): '𝕸',
                ord('n'): '𝖓',    ord('N'): '𝕹',
                ord('o'): '𝖔',    ord('O'): '𝕺',
                ord('p'): '𝖕',    ord('P'): '𝕻',
                ord('q'): '𝖖',    ord('Q'): '𝕼',
                ord('r'): '𝖗',    ord('R'): '𝕽',
                ord('s'): '𝖘',    ord('S'): '𝕾',
                ord('t'): '𝖙',    ord('T'): '𝕿',
                ord('u'): '𝖚',    ord('U'): '𝖀',
                ord('v'): '𝖛',    ord('V'): '𝖁',
                ord('w'): '𝖜',    ord('W'): '𝖂',
                ord('x'): '𝖝',    ord('X'): '𝖃',
                ord('y'): '𝖞',    ord('Y'): '𝖄',
                ord('z'): '𝖟',    ord('Z'): '𝖅',
            },
            'smallcaps': {
                ord('a'): 'ᴀ',
                ord('b'): 'ʙ',
                ord('c'): 'ᴄ',
                ord('d'): 'ᴅ',
                ord('e'): 'ᴇ',
                ord('f'): 'ꜰ',
                ord('g'): 'ɢ',
                ord('h'): 'ʜ',
                ord('i'): 'ɪ',
                ord('j'): 'ᴊ',
                ord('k'): 'ᴋ',
                ord('l'): 'ʟ',
                ord('m'): 'ᴍ',
                ord('n'): 'ɴ',
                ord('o'): 'ᴏ',
                ord('p'): 'ᴘ',
                ord('q'): 'ǫ',
                ord('r'): 'ʀ',
                ord('s'): 'ꜱ',
                ord('t'): 'ᴛ',
                ord('u'): 'ᴜ',
                ord('v'): 'ᴠ',
                ord('w'): 'ᴡ',
                ord('y'): 'ʏ',
                ord('z'): 'ᴢ',
            },
            'double': {
                ord('a'): '𝕒',    ord('A'): '𝔸',    ord('0'): '𝟘',
                ord('b'): '𝕓',    ord('B'): '𝔹',    ord('1'): '𝟙',
                ord('c'): '𝕔',    ord('C'): 'ℂ',    ord('2'): '𝟚',
                ord('d'): '𝕕',    ord('D'): '𝔻',    ord('3'): '𝟛',
                ord('e'): '𝕖',    ord('E'): '𝔼',    ord('4'): '𝟜',
                ord('f'): '𝕗',    ord('F'): '𝔽',    ord('5'): '𝟝',
                ord('g'): '𝕘',    ord('G'): '𝔾',    ord('6'): '𝟞',
                ord('h'): '𝕙',    ord('H'): 'ℍ',    ord('7'): '𝟟',
                ord('i'): '𝕚',    ord('I'): '𝕀',    ord('8'): '𝟠',
                ord('j'): '𝕛',    ord('J'): '𝕁',    ord('9'): '𝟡',
                ord('k'): '𝕜',    ord('K'): '𝕂',
                ord('l'): '𝕝',    ord('L'): '𝕃',
                ord('m'): '𝕞',    ord('M'): '𝕄',
                ord('n'): '𝕟',    ord('N'): 'ℕ',
                ord('o'): '𝕠',    ord('O'): '𝕆',
                ord('p'): '𝕡',    ord('P'): 'ℙ',
                ord('q'): '𝕢',    ord('Q'): 'ℚ',
                ord('r'): '𝕣',    ord('R'): 'ℝ',
                ord('s'): '𝕤',    ord('S'): '𝕊',
                ord('t'): '𝕥',    ord('T'): '𝕋',
                ord('u'): '𝕦',    ord('U'): '𝕌',
                ord('v'): '𝕧',    ord('V'): '𝕍',
                ord('w'): '𝕨',    ord('W'): '𝕎',
                ord('x'): '𝕩',    ord('X'): '𝕏',
                ord('y'): '𝕪',    ord('Y'): '𝕐',
                ord('z'): '𝕫',    ord('Z'): 'ℤ',
            },
            'fullwidth': {
                ord('a'): 'ａ',    ord('A'): 'Ａ',    ord('0'): '０',
                ord('b'): 'ｂ',    ord('B'): 'Ｂ',    ord('1'): '１',
                ord('c'): 'ｃ',    ord('C'): 'Ｃ',    ord('2'): '２',
                ord('d'): 'ｄ',    ord('D'): 'Ｄ',    ord('3'): '３',
                ord('e'): 'ｅ',    ord('E'): 'Ｅ',    ord('4'): '４',
                ord('f'): 'ｆ',    ord('F'): 'Ｆ',    ord('5'): '５',
                ord('g'): 'ｇ',    ord('G'): 'Ｇ',    ord('6'): '６',
                ord('h'): 'ｈ',    ord('H'): 'Ｈ',    ord('7'): '７',
                ord('i'): 'ｉ',    ord('I'): 'Ｉ',    ord('8'): '８',
                ord('j'): 'ｊ',    ord('J'): 'Ｊ',    ord('9'): '９',
                ord('k'): 'ｋ',    ord('K'): 'Ｋ',    ord('.'): '．',
                ord('l'): 'ｌ',    ord('L'): 'Ｌ',    ord(','): '，',
                ord('m'): 'ｍ',    ord('M'): 'Ｍ',    ord("'"): '＇',
                ord('n'): 'ｎ',    ord('N'): 'Ｎ',    ord('!'): '！',
                ord('o'): 'ｏ',    ord('O'): 'Ｏ',    ord('?'): '？',
                ord('p'): 'ｐ',    ord('P'): 'Ｐ',    ord('('): '（',
                ord('q'): 'ｑ',    ord('Q'): 'Ｑ',    ord(')'): '）',
                ord('r'): 'ｒ',    ord('R'): 'Ｒ',    ord('['): '［',
                ord('s'): 'ｓ',    ord('S'): 'Ｓ',    ord(']'): '］',
                ord('t'): 'ｔ',    ord('T'): 'Ｔ',    ord('{'): '｛',
                ord('u'): 'ｕ',    ord('U'): 'Ｕ',    ord('}'): '｝',
                ord('v'): 'ｖ',    ord('V'): 'Ｖ',    ord('_'): '＿',
                ord('w'): 'ｗ',    ord('W'): 'Ｗ',    ord('^'): '＾',
                ord('x'): 'ｘ',    ord('X'): 'Ｘ',    ord(';'): '；',
                ord('y'): 'ｙ',    ord('Y'): 'Ｙ',    ord('&'): '＆',
                ord('z'): 'ｚ',    ord('Z'): 'Ｚ',    ord('#'): '＃',
                ord('*'): '＊',    ord('%'): '％',    ord('$'): '＄',
                ord('~'): '～',    ord('@'): '＠',    ord(':'): '：',
                ord('/'): '／',    ord('\\'): '＼',   ord('|'): '｜',
                ord('`'): '｀',    ord('='): '＝',    ord('"'): '＂',
                ord('+'): '＋',    ord('-'): '－',    ord('<'): '＜',
                ord('¦'): '￤',    ord('¬'): '￢',    ord('>'): '＞',
                ord('£'): '￡',    ord('¥'): '￥',    ord('₩'): '￦',
                ord('¢'): '￠',    ord('⸨'): '｟',    ord('⸩'): '｠',
                ord('¯'): '￣',
            },
            'superscript': {
                ord('a'): 'ᵃ',    ord('A'): 'ᴬ',    ord('0'): '⁰',
                ord('b'): 'ᵇ',    ord('B'): 'ᴮ',    ord('1'): '¹',
                ord('c'): 'ᶜ',    ord('C'): 'ᶜ',    ord('2'): '²',
                ord('d'): 'ᵈ',    ord('D'): 'ᴰ',    ord('3'): '³',
                ord('e'): 'ᵉ',    ord('E'): 'ᴱ',    ord('4'): '⁴',
                ord('f'): 'ᶠ',    ord('F'): 'ᶠ',    ord('5'): '⁵',
                ord('g'): 'ᵍ',    ord('G'): 'ᴳ',    ord('6'): '⁶',
                ord('h'): 'ʰ',    ord('H'): 'ᴴ',    ord('7'): '⁷',
                ord('i'): 'ⁱ',    ord('I'): 'ᴵ',    ord('8'): '⁸',
                ord('j'): 'ʲ',    ord('J'): 'ᴶ',    ord('9'): '⁹',
                ord('k'): 'ᵏ',    ord('K'): 'ᴷ',
                ord('l'): 'ˡ',    ord('L'): 'ᴸ',
                ord('m'): 'ᵐ',    ord('M'): 'ᴹ',
                ord('n'): 'ⁿ',    ord('N'): 'ᴺ',
                ord('o'): 'ᵒ',    ord('O'): 'ᴼ',
                ord('p'): 'ᵖ',    ord('P'): 'ᴾ',
                ord('r'): 'ʳ',    ord('R'): 'ᴿ',
                ord('s'): 'ˢ',    ord('S'): 'ˢ',
                ord('t'): 'ᵗ',    ord('T'): 'ᵀ',
                ord('u'): 'ᵘ',    ord('U'): 'ᵁ',
                ord('v'): 'ᵛ',    ord('V'): 'ⱽ',
                ord('w'): 'ʷ',    ord('W'): 'ᵂ',
                ord('x'): 'ˣ',    ord('X'): 'ˣ',
                ord('y'): 'ʸ',    ord('Y'): 'ʸ',
                ord('z'): 'ᶻ',    ord('Z'): 'ᶻ',
            },
        }

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse(self.help(None), message.replyTo)
        style = message.parameterList[0].lower()
        if style not in self.styles:
            return IRCResponse("{!r} is not a known text style"
                               .format(message.parameterList[0]), message.replyTo)
        if len(message.parameterList) == 1:
            return IRCResponse("You didn't give me any text to style with {!r}"
                               .format(message.parameterList[0]), message.replyTo)

        text = ' '.join(message.parameterList[1:])
        styled = text.translate(self.styles[style])
        return IRCResponse(styled, message.replyTo)


style = Style()
