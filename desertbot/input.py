from desertbot.channel import IRCChannel
from desertbot.ircbase import ModeType
from desertbot.message import IRCMessage
from desertbot.user import IRCUser
from base64 import b64encode
from datetime import datetime
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from desertbot.desertbot import DesertBot


class InputHandler(object):
    def __init__(self, bot: 'DesertBot'):
        self.bot = bot

    def handleCommand(self, command: str, prefix: str, params: List[str]) -> None:
        parsedPrefix = parseUserPrefix(prefix)
        nick = parsedPrefix[0]
        ident = parsedPrefix[1]
        host = parsedPrefix[2]

        method = getattr(self, f'_handle{command}', None)
        if method:
            method(nick, ident, host, params)

    def handleNumeric(self, numeric: str, prefix: str, params: List[str]) -> None:
        method = getattr(self, f'_handleNumeric{numeric}', None)
        if method:
            method(prefix, params)

    def _handleACCOUNT(self, nick, ident, host, params):
        if 'account-notify' not in self.bot.capabilities['finished']:
            return

        if nick not in self.bot.users:
            self.bot.logger.warning(f'Received ACCOUNT message for unknown user {nick}.')
            return

        user = self.bot.users[nick]
        if params[0] == '*':
            user.account = None
        else:
            user.account = params[0]

    def _handleAUTHENTICATE(self, nick, ident, host, params):
        if params[0] == '+':
            username = self.bot.config.getWithDefault('sasl_username', '')
            password = self.bot.config.getWithDefault('sasl_password', '')
            payload = b64encode((username + '\u0000' + username + '\u0000' + password).encode('ascii'))
            self.bot.output.cmdAUTHENTICATE(payload.decode('utf-8'))

    def _handleAWAY(self, nick, ident, host, params):
        if 'away-notify' not in self.bot.capabilities['finished']:
            return

        if nick not in self.bot.users:
            self.bot.logger.warning(f'Received AWAY message for unknown user {nick}.')
            return

        user = self.bot.users[nick]
        if len(params) == 1:
            user.isAway = True
            user.awayMessage = params[0]
        else:
            user.isAway = False
            user.awayMessage = None

    def _handleCAP(self, nick, ident, host, params):
        subCommand = params[1]
        if subCommand == 'LS':
            self.bot.logger.info(f'Received CAP LS reply, supported caps: {params[2]}')
            serverCaps = _parseCapReply(params[2])
            for reqCap in [x for x in self.bot.capabilities['available'] if x in serverCaps]:
                self.bot.capabilities['requested'].append(reqCap)
            self.checkCAPNegotiationFinished()
            if self.bot.capabilities['init']:
                toRequest = ' '.join(self.bot.capabilities['requested'])
                self.bot.logger.info(f'Requesting capabilities: {toRequest}...')
                self.bot.output.cmdCAP_REQ(toRequest)
        elif subCommand == 'ACK' or subCommand == 'NAK':
            capList = _parseCapReply(params[2])
            self.bot.capabilities['requested'] = [x for x in self.bot.capabilities['requested'] if x not in capList]
            if params[1] == 'ACK':
                for capName, capParam in capList.items():
                    if capName not in self.bot.capabilities['enabled']:
                        self.bot.capabilities['enabled'].append(capName)
                    
                    if capName == 'sasl':
                        self._handleSASL(capParam)
                    elif capName not in self.bot.capabilities['finished']:
                        self.bot.capabilities['finished'].append(capName)

                self.bot.logger.info(f'Acknowledged capability changes: {params[2]}.')
            else:
                self.bot.logger.info(f'Rejected capability changes: {params[2]}.')
            self.checkCAPNegotiationFinished()

    def _handleCHGHOST(self, nick, ident, host, params):
        if 'chghost' not in self.bot.capabilities['finished']:
            return

        if nick not in self.bot.users:
            self.bot.logger.warning(f'Received CHGHOST message for unknown user {nick}.')
            return

        user = self.bot.users[nick]
        user.ident = params[0]
        user.host = params[1]

    def _handleERROR(self, nick, ident, host, params):
        self.bot.logger.info(f'Connection terminated ({params[0]})')

    def _handleINVITE(self, nick, ident, host, params):
        if nick in self.bot.users:
            inviter = self.bot.users[nick]
        else:
            inviter = IRCUser(nick, ident, host)

        invitee = None
        if 'invite-notify' in self.bot.capabilities['finished'] and len(params) > 1:
            if params[0] not in self.bot.users:
                invitee = IRCUser(params[0])
            else:
                invitee = self.bot.users[nick]
            chanName = params[1]
        else:
            chanName = params[0]

        if chanName not in self.bot.channels:
            channel = IRCChannel(params[0], self.bot)
        else:
            channel = self.bot.channels[chanName]
        if not invitee or invitee.nick == self.bot.nick:
            self.bot.output.cmdJOIN(chanName)
        message = IRCMessage('INVITE', inviter, channel, '', self.bot, {'invitee': invitee})
        self.handleMessage(message)

    def _handleJOIN(self, nick, ident, host, params):
        if nick not in self.bot.users:
            user = IRCUser(nick, ident, host)
            if 'extended-join' in self.bot.capabilities['finished'] and len(params) > 1:
                if params[1] != '*':
                    user.account = params[1]
                user.gecos = params[2]
            self.bot.users[nick] = user
        else:
            user = self.bot.users[nick]
            user.ident = ident
            user.host = host

        if params[0] not in self.bot.channels:
            channel = IRCChannel(params[0], self.bot)
            self.bot.output.cmdWHO(params[0])
            self.bot.output.cmdMODE(params[0])
            self.bot.channels[params[0]] = channel
        else:
            channel = self.bot.channels[params[0]]
        channel.users[nick] = user
        channel.ranks[nick] = ''
        message = IRCMessage('JOIN', user, channel, '', self.bot)
        self.handleMessage(message)

    def _handleKICK(self, nick, ident, host, params):
        if params[0] not in self.bot.channels:
            self.bot.logger.warning(f'Received KICK message for unknown channel {params[0]}.')
            return
        channel = self.bot.channels[params[0]]
        if params[1] not in channel.users:
            self.bot.logger.warning(f'Received KICK message for unknown user {nick} in channel {params[0]}.')
            return
        if nick not in self.bot.users:
            # Technically opers could KICK a user despite not being in the channel themselves
            kicker = IRCUser(nick, ident, host)
        else:
            kicker = self.bot.users[nick]
        kicked = self.bot.users[params[1]]
        reason = ''
        if len(params) > 2:
            reason = params[2]

        message = IRCMessage('KICK', kicker, channel, reason, self.bot, {'kicked': kicked})
        self.handleMessage(message)

        # We need to run the action before we actually get rid of the user
        if kicked.nick == self.bot.nick:
            del self.bot.channels[params[0]]
        else:
            del channel.users[kicked.nick]
            del channel.ranks[kicked.nick]

    def _handleMODE(self, nick, ident, host, params):
        message = None
        if nick in self.bot.users:
            user = self.bot.users[nick]
        else:
            user = IRCUser(nick, ident, host)
        if len(params) > 2:
            modeParams = params[2:]
        else:
            modeParams = []
        if params[0][0] in self.bot.supportHelper.chanTypes:
            if params[0] not in self.bot.channels:
                self.bot.logger.warning(f'Received MODE message for unknown channel {params[0]}.')
                return
            channel = self.bot.channels[params[0]]
            modes = channel.setModes(params[1], modeParams)
            if not modes:
                return
            if len(modes['added']) > 0 or len(modes['removed']) > 0:
                message = IRCMessage('MODE', user, channel, '', self.bot, modes)
        elif params[0] == self.bot.nick:
            modes = self.bot.setUserModes(params[1])
            if not modes:
                return
            if len(modes['added']) > 0 or len(modes['removed']) > 0:
                message = IRCMessage('MODE', user, None, '', self.bot, modes)
        if message:
            self.handleMessage(message)

    def _handleNICK(self, nick, ident, host, params):
        if nick not in self.bot.users:
            self.bot.logger.warning(f'Received NICK message for unknown user {nick}.')
            return
        user = self.bot.users[nick]
        newNick = params[0]
        user.nick = newNick
        self.bot.users[newNick] = user
        del self.bot.users[nick]
        for channel in self.bot.channels.values():
            if nick in channel.users:
                channel.users[newNick] = user
                channel.ranks[newNick] = channel.ranks[nick]
                del channel.users[nick]
                del channel.ranks[nick]
        if nick == self.bot.nick:
            self.bot.nick = newNick
        message = IRCMessage('NICK', user, None, newNick, self.bot, {'oldnick': nick})
        self.handleMessage(message)

    def _handleNOTICE(self, nick, ident, host, params):
        user = None
        if params[0][0] in self.bot.supportHelper.chanTypes:
            if params[0] in self.bot.channels:
                source = self.bot.channels[params[0]]
            else:
                # We got a notice for an unknown channel. Create a temporary IRCChannel object for it.
                source = IRCChannel(params[0], self.bot)
            if nick in self.bot.users:
                user = self.bot.users[nick]
            else:
                user = IRCUser(nick, ident, host)
        elif nick in self.bot.users:
            source = self.bot.users[nick]
        else:
            # We got a notice from an unknown user. Create a temporary IRCUser object for them.
            source = IRCUser(nick, ident, host)
        if isinstance(source, IRCChannel):
            message = IRCMessage('NOTICE', user, source, params[1], self.bot)
        else:
            message = IRCMessage('NOTICE', source, None, params[1], self.bot)
        self.handleMessage(message)

    def _handlePART(self, nick, ident, host, params):
        if params[0] not in self.bot.channels:
            self.bot.logger.warning(f'Received PART message for unknown channel {params[0]}.')
            return
        channel = self.bot.channels[params[0]]
        if nick not in channel.users:
            self.bot.logger.warning(f'Received PART message for unknown user {nick} in channel {params[0]}.')
            return
        reason = ''
        if len(params) > 1:
            reason = params[1]
        user = self.bot.users[nick]
        # We need to run the action before we actually get rid of the user
        message = IRCMessage('PART', user, channel, reason, self.bot)
        self.handleMessage(message)
        if nick == self.bot.nick:
            del self.bot.channels[params[0]]
        else:
            del channel.users[nick]
            del channel.ranks[nick]

    def _handlePING(self, nick, ident, host, params):
        self.bot.moduleHandler.handlePing()
        self.bot.output.cmdPONG(' '.join(params))

    def _handlePRIVMSG(self, nick, ident, host, params):
        user = None
        if params[0][0] in self.bot.supportHelper.chanTypes:
            if params[0] in self.bot.channels:
                source = self.bot.channels[params[0]]
            else:
                # We got a message for an unknown channel. Create a temporary IRCChannel object for it.
                source = IRCChannel(params[0], self.bot)
            if nick in self.bot.users:
                user = self.bot.users[nick]
            else:
                user = IRCUser(nick, ident, host)
        elif nick in self.bot.users:
            source = self.bot.users[nick]
            user = source
        else:
            # We got a message from an unknown user. Create a temporary IRCUser object for them.
            source = IRCUser(nick, ident, host)
        if len(params) == 1:
            self.bot.logger.warning('Received a blank PRIVMSG')
            params.append('')
        if params[1] and params[1][0] == '\x01':
            msgType = 'CTCP'
            msgStr = params[1][1:len(params[1]) - 1]
            if msgStr.upper().startswith('ACTION'):
                msgType = 'ACTION'
                msgStr = msgStr[7:]
            if isinstance(source, IRCChannel):
                message = IRCMessage(msgType, user, source, msgStr, self.bot)
            else:
                message = IRCMessage(msgType, source, None, msgStr, self.bot)
        elif isinstance(source, IRCChannel):
            message = IRCMessage('PRIVMSG', user, source, params[1], self.bot)
        else:
            message = IRCMessage('PRIVMSG', source, None, params[1], self.bot)
        self.handleMessage(message)

    def _handleQUIT(self, nick, ident, host, params):
        if nick not in self.bot.users:
            self.bot.logger.warning(f'Received a QUIT message for unknown user {nick}.')
            return
        reason = ''
        if len(params) > 0:
            reason = params[0]
        user = self.bot.users[nick]
        quitChannels = [chan for _, chan in self.bot.channels.items() if nick in chan.users]
        message = IRCMessage('QUIT', user, None, reason, self.bot, {'quitChannels': quitChannels})
        self.handleMessage(message)
        for channel in self.bot.channels.values():
            if nick in channel.users:
                del channel.users[nick]
                del channel.ranks[nick]

    def _handleTOPIC(self, nick, ident, host, params):
        if params[0] not in self.bot.channels:
            self.bot.logger.warning(f'Received TOPIC message for unknown channel {params[0]}.')
            return
        channel = self.bot.channels[params[0]]
        if nick not in self.bot.users:
            # A user that's not in the channel can change the topic so let's make a temporary user.
            user = IRCUser(nick, ident, host)
        else:
            user = self.bot.users[nick]
        oldTopic = channel.topic
        channel.topic = params[1]
        channel.topicSetter = user.fullUserPrefix()
        channel.topicTimestamp = timestamp(now())
        message = IRCMessage('TOPIC', user, channel, params[1], self.bot, {'oldtopic': oldTopic})
        self.handleMessage(message)

    def _handleNumeric001(self, prefix, params):
        # 001: RPL_WELCOME
        self.bot.loggedIn = True
        self.bot.factory.connectionAttempts = 0
        message = IRCMessage('001', IRCUser(prefix), None, '', self.bot)
        self.handleMessage(message)
        channels = self.bot.config.getWithDefault('channels', {})
        for channel, key in channels.items():
            self.bot.output.cmdJOIN(channel, key if key else '')

    def _handleNumeric004(self, prefix, params):
        # 004: RPL_MYINFO
        if len(params) < 4:
            self.bot.logger.warning('Received malformed MY_INFO reply, params: {}'.format(' '.join(params)))
            return

        self.bot.supportHelper.serverName = params[1]
        self.bot.supportHelper.serverVersion = params[2]
        self.bot.supportHelper.userModes = params[3]

    def _handleNumeric005(self, prefix, params):
        # 005: RPL_ISUPPORT
        tokens = {}
        # The first param is our prefix and the last one is ':are supported by this server'
        for param in params[1: -1]:
            keyValuePair = param.split('=')
            if len(keyValuePair) > 1:
                tokens[keyValuePair[0]] = keyValuePair[1]
            else:
                tokens[keyValuePair[0]] = ''
        if 'CHANTYPES' in tokens:
            self.bot.supportHelper.chanTypes = tokens['CHANTYPES']
        if 'CHANMODES' in tokens:
            self.bot.supportHelper.chanModes.clear()
            groups = tokens['CHANMODES'].split(',')
            for mode in groups[0]:
                self.bot.supportHelper.chanModes[mode] = ModeType.LIST
            for mode in groups[1]:
                self.bot.supportHelper.chanModes[mode] = ModeType.PARAM_SET_UNSET
            for mode in groups[2]:
                self.bot.supportHelper.chanModes[mode] = ModeType.PARAM_SET
            for mode in groups[3]:
                self.bot.supportHelper.chanModes[mode] = ModeType.NO_PARAM
        if 'NETWORK' in tokens:
            self.bot.supportHelper.network = tokens['NETWORK']
        if 'PREFIX' in tokens:
            self.bot.supportHelper.statusModes.clear()
            self.bot.supportHelper.statusSymbols.clear()
            modes = tokens['PREFIX'][1:tokens['PREFIX'].find(')')]
            symbols = tokens['PREFIX'][tokens['PREFIX'].find(')') + 1:]
            self.bot.supportHelper.statusOrder = modes
            for i in range(len(modes)):
                self.bot.supportHelper.statusModes[modes[i]] = symbols[i]
                self.bot.supportHelper.statusSymbols[symbols[i]] = modes[i]
        self.bot.supportHelper.rawTokens.update(tokens)

    def _handleNumeric324(self, prefix, params):
        # 324: RPL_CHANNELMODEIS
        channel = self.bot.channels[params[1]]
        modeParams = params[3].split() if len(params) > 3 else []
        modes = channel.setModes(params[2], modeParams)
        if modes:
            message = IRCMessage('324', IRCUser(prefix), None, '', self.bot, modes)
            self.handleMessage(message)

    def _handleNumeric329(self, prefix, params):
        # 329: RPL_CREATIONTIME
        channel = self.bot.channels[params[1]]
        channel.creationTime = int(params[2])

    def _handleNumeric332(self, prefix, params):
        # 332: RPL_TOPIC
        channel = self.bot.channels[params[1]]
        channel.topic = params[2]

    def _handleNumeric333(self, prefix, params):
        # 333: RPL_TOPICWHOTIME
        channel = self.bot.channels[params[1]]
        channel.topicSetter = params[2]
        channel.topicTimestamp = int(params[3])

    def _handleNumeric352(self, prefix, params):
        # 352: RPL_WHOREPLY
        if params[5] not in self.bot.users:
            self.bot.logger.warning(f'Received WHO reply for unknown user {params[5]}.')
            return
        user = self.bot.users[params[5]]
        user.ident = params[2]
        user.host = params[3]
        user.server = params[4]
        flags = list(params[6])
        if flags.pop(0) == 'G':
            user.isAway = True
        if len(flags) > 0 and flags[0] == '*':
            user.isOper = True
            flags.pop(0)
        if params[1] in self.bot.channels:
            channel = self.bot.channels[params[1]]
            channel.ranks[params[5]] = ''
            for status in flags:
                channel.ranks[params[5]] += self.bot.supportHelper.statusSymbols[status]
        hopsGecos = params[7].split()
        user.hops = int(hopsGecos[0])
        if len(hopsGecos) > 1:
            user.gecos = hopsGecos[1]
        else:
            user.gecos = 'No info'

    def _handleNumeric353(self, prefix, params):
        # 353: RPL_NAMREPLY
        channel = self.bot.channels[params[2]]
        if channel.userlistComplete:
            channel.userlistComplete = False
            channel.users.clear()
            channel.ranks.clear()
        for userPrefix in params[3].split():
            parsedPrefix = parseUserPrefix(userPrefix)
            nick = parsedPrefix[0]
            ranks = ''
            while nick[0] in self.bot.supportHelper.statusSymbols:
                ranks += self.bot.supportHelper.statusSymbols[nick[0]]
                nick = nick[1:]
            if nick in self.bot.users:
                user = self.bot.users[nick]
                user.ident = parsedPrefix[1]
                user.host = parsedPrefix[2]
            else:
                user = IRCUser(nick, parsedPrefix[1], parsedPrefix[2])
                self.bot.users[nick] = user
            channel.users[nick] = user
            channel.ranks[nick] = ranks

    def _handleNumeric366(self, prefix, params):
        # 366: RPL_ENDOFNAMES
        channel = self.bot.channels[params[1]]
        channel.userlistComplete = True

    def _handleNumeric401(self, prefix, params):
        # This is assuming the numeric is even sent to begin with, which some unsupported IRCds don't even seem to do.
        if params[0] == 'CAP':
            self.bot.logger.info('Server does not support capability negotiation.')
            self.bot.capabilities['init'] = False

    def _handleNumeric433(self, prefix, params):
        # 433: ERR_NICKNAMEINUSE
        newNick = '{self.bot.nick}_'
        self.bot.logger.info('Nickname {self.bot.nick} is in use, retrying with {newNick} ...')
        self.bot.nick = newNick
        self.bot.output.cmdNICK(self.bot.nick)

    def _handleNumeric900(self, prefix, params):
        self._handleAuthSuccessful()

    def _handleNumeric902(self, prefix, params):
        self._handleAuthFailed()

    def _handleNumeric903(self, prefix, params):
        self._handleAuthSuccessful()

    def _handleNumeric904(self, prefix, params):
        self._handleAuthFailed()

    def _handleNumeric905(self, prefix, params):
        self._handleAuthFailed()

    def _handleNumeric907(self, prefix, params):
        self._handleAuthFailed()

    def handleMessage(self, message: IRCMessage):
        self.bot.moduleHandler.handleMessage(message)

    def _handleSASL(self, capParam):
        if capParam is None:
            saslMechs = [ 'PLAIN' ] # IRCv3.1 reply, assume PLAIN is available
        else:
            saslMechs = capParam.split(',')
        
        if 'PLAIN' in saslMechs:
            self.bot.logger.info('Sending SASL authentication request (PLAIN)...')
            self.bot.output.cmdAUTHENTICATE('PLAIN')
        else:
            self.bot.logger.warning('Aborting SASL authentication; server does not support PLAIN mechanism!')

    def _handleAuthSuccessful(self):
        self.bot.capabilities['finished'].append('sasl')
        self.bot.logger.info('SASL authentication successful.')
        self.checkCAPNegotiationFinished()

    def _handleAuthFailed(self):
        self.bot.capabilities['finished'].append('sasl')
        self.bot.logger.warning('SASL authentication failed!')
        self.checkCAPNegotiationFinished()

    def checkCAPNegotiationFinished(self):
        if not self.bot.capabilities['init'] or len(self.bot.capabilities['requested']) != 0:
            return

        if set(self.bot.capabilities['enabled']) == set(self.bot.capabilities['finished']):
            self.bot.output.cmdCAP_END()
            self.bot.logger.info('Capability negotiation completed.')
            self.bot.capabilities['init'] = False


def parseUserPrefix(prefix: str) -> Tuple[str, Optional[str], Optional[str]]:
    if prefix is None:
        prefix = ''

    if '!' in prefix:
        nick = prefix[:prefix.find('!')]
        ident = prefix[prefix.find('!') + 1:prefix.find('@')]
        host = prefix[prefix.find('@') + 1:]
        return nick, ident, host

    # Not all 'users' have idents and hostnames
    nick = prefix

    return nick, None, None


def now():
    return datetime.utcnow().replace(microsecond=0)


def timestamp(time):
    unixEpoch = datetime.utcfromtimestamp(0)
    return int((time - unixEpoch).total_seconds())


def _parseCapReply(reply):
    parsedReply = {}
    for serverCap in reply.split():
        if '=' in serverCap:
            key, value = serverCap.split('=')
        else:
            key = serverCap
            value = None
        parsedReply[key] = value
    return parsedReply
