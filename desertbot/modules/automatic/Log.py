"""
Created on May 11, 2014

@author: StarlitGhost
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime
import codecs
import os

from desertbot.message import IRCMessage, TargetTypes
from desertbot.response import IRCResponse, ResponseType


logFuncs = {
    'PRIVMSG': lambda m: formatPrivmsg(m),
    'ACTION': lambda m: '*{0} {1}*'.format(m.user.nick, m.messageString),
    'NOTICE': lambda m: '[{0}] {1}'.format(m.user.nick, m.messageString),
    'JOIN': lambda m: '>> {0} ({1}@{2}) joined {3}'.format(m.user.nick, m.user.ident, m.user.host, m.replyTo),
    'NICK': lambda m: '{0} is now known as {1}'.format(m.user.nick, m.messageString),
    'PART': lambda m: '<< {0} ({1}@{2}) left {3}{4}'.format(m.user.nick, m.user.ident, m.user.host, m.replyTo, ': ' + m.messageString if m.messageString else ''),
    'QUIT': lambda m: '<< {0} ({1}@{2}) quit{3}'.format(m.user.nick, m.user.ident, m.user.host, ': '+m.messageString if m.messageString else ''),
    'KICK': lambda m: '-- {0} was kicked by {1}{2}'.format(m.metadata['kicked'], m.user.nick, ': '+m.messageString if m.messageString else ''),
    'TOPIC': lambda m: '-- {0} set the topic to: {1}'.format(m.user.nick, m.messageString),
    'MODE': lambda m: formatMode(m),
}

logSelfFuncs = {
    ResponseType.Say: lambda bot, r: formatSelfPrivmsg(bot, r),
    ResponseType.Do: lambda bot, r: '*{0} {1}*'.format(bot.nick, r.response),
    ResponseType.Notice: lambda bot, r: '[{0}] {1}'.format(bot.nick, r.response),
}

def formatSelfPrivmsg(bot, response):
    if bot.nick in bot.users and response.target in bot.channels:
        status = bot.channels[response.target].getHighestStatusOfUser(bot.users[bot.nick])
    else:
        status = ''

    return '<{0}{1}> {2}'.format(status, bot.nick, response.response)

def formatPrivmsg(msg: IRCMessage):
    if msg.targetType == TargetTypes.CHANNEL:
        status = msg.channel.getHighestStatusOfUser(msg.user)
    else:
        status = ''

    return '<{0}{1}> {2}'.format(status, msg.user.nick, msg.messageString)

def formatMode(msg: IRCMessage):
    added = msg.metadata['added']
    removed = msg.metadata['removed']
    if 'addedParams' in msg.metadata:
        addedParams = [p for p in msg.metadata['addedParams'] if p is not None]
    else:
        addedParams = []
    if 'removedParams' in msg.metadata:
        removedParams = [p for p in msg.metadata['removedParams'] if p is not None]
    else:
        removedParams = []

    if len(added) > 0:
        modeStr = '+{}'.format(''.join(added))
        if len(addedParams) > 0:
            modeStr += ' {}'.format(' '.join(addedParams))
    else:
        modeStr = '-{}'.format(''.join(removed))
        if len(removedParams) > 0:
            modeStr += ' {}'.format(' '.join(removedParams))

    return '-- {} sets mode: {}'.format(msg.user.nick, modeStr)


def log(path, target, text):
    now = datetime.datetime.utcnow()
    time = now.strftime("[%H:%M:%S]")
    data = '{0} {1}'.format(time, text)
    print(target, data)

    fileName = "{0}{1}.txt".format(target, now.strftime("-%Y%m%d"))
    fileDirs = path
    if not os.path.exists(fileDirs):
        os.makedirs(fileDirs)
    filePath = os.path.join(fileDirs, fileName)

    with codecs.open(filePath, 'a+', 'utf-8') as f:
        f.write(data + '\n')


@implementer(IPlugin, IModule)
class Log(BotCommand):
    def actions(self):
        return super(Log, self).actions() + [('message-channel', 100, self.input),
                                             ('message-user', 100, self.input),
                                             ('action-channel', 100, self.input),
                                             ('action-user', 100, self.input),
                                             ('notice-channel', 100, self.input),
                                             ('notice-user', 100, self.input),
                                             ('channeljoin', 100, self.input),
                                             ('channelinvite', 100, self.input),
                                             ('channelpart', 100, self.input),
                                             ('channelkick', 100, self.input),
                                             ('userquit', 100, self.input),
                                             ('usernick', 100, self.input),
                                             ('modeschanged-channel', 100, self.input),
                                             ('modeschanged-user', 100, self.input),
                                             ('channeltopic', 100, self.input),
                                             ('response-message', -1, self.output),
                                             ('response-action', -1, self.output),
                                             ('response-notice', -1, self.output)]

    def triggers(self):
        return []  # ['log']

    def help(self, arg):
        return "Logs {} messages.".format("/".join(logFuncs.keys()))
        # return ("log (-n / yyyy-mm-dd) - "
        # "without parameters, links to today's log. "
        # "-n links to the log n days ago. "
        # "yyyy-mm-dd links to the log for the specified date")

    def input(self, message: IRCMessage):
        if message.type in logFuncs:
            logString = logFuncs[message.type](message)
            log(os.path.join(self.bot.logPath, self.bot.server), message.replyTo, logString)

    def output(self, response: IRCResponse):
        if response.type in logSelfFuncs:
            logString = logSelfFuncs[response.type](self.bot, response)
            log(os.path.join(self.bot.logPath, self.bot.server),
                response.target,
                logString)

        return response

    def execute(self, message):
        # log linking things
        pass


logger = Log()
