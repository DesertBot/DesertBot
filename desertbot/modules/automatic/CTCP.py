from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule, ignore
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from datetime import datetime
from platform import platform
import subprocess


@implementer(IPlugin, IModule)
class CTCP(BotModule):
    def actions(self):
        return super(CTCP, self).actions() + [('ctcp-channel', 1, self.handleCTCP),
                                              ('ctcp-user', 1, self.handleCTCP)]

    def help(self, arg):
        return 'Responds to CTCP commands'

    @ignore
    def handleCTCP(self, message: IRCMessage):
        msg = message.messageString
        target = message.user.nick
        ctcpCommand = msg.upper()

        if ctcpCommand == 'PING' or ctcpCommand.startswith('PING '):
            return self._getResponse(target, 'PING', msg[5:])
        elif ctcpCommand == 'VERSION':
            try:
                versionNum = subprocess.check_output(['git', 'describe', '--always']).strip()
            except FileNotFoundError:
                versionNum = '1.0'
            return self._getResponse(target, 'VERSION', '{} v{} / {}'.format(self.bot.nick, versionNum, platform()))
        elif ctcpCommand == 'TIME':
            return self._getResponse(target, 'TIME', datetime.utcnow().replace(microsecond=0).strftime('%Y-%m-%d %H:%M UTC'))
        elif ctcpCommand == 'SOURCE':
            return self._getResponse(target, 'SOURCE', self.bot.config.getWithDefault('source', 'https://github.com/DesertBot/DesertBot/'))
        elif ctcpCommand == 'FINGER':
            return self._getResponse(target, 'FINGER', self.bot.config.getWithDefault('finger', 'GET YOUR FINGER OUT OF THERE'))

        return None

    def _getResponse(self, target: str, ctcpType: str, reply: str) -> IRCResponse:
        if reply:
            return IRCResponse(ResponseType.Notice, '\x01{} {}\x01'.format(ctcpType, reply), target)
        else:
            return IRCResponse(ResponseType.Notice, '\x01{}\x01'.format(ctcpType), target)


ctcp = CTCP()
