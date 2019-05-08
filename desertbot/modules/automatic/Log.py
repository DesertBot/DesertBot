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
import parsedatetime

from desertbot.message import IRCMessage, TargetTypes
from desertbot.response import IRCResponse, ResponseType


logFuncs = {
    'PRIVMSG': lambda m: formatPrivmsg(m),
    'ACTION': lambda m: f'* {m.user.nick} {m.messageString}',
    'NOTICE': lambda m: f'[{m.user.nick}] {m.messageString}',
    'JOIN': lambda m: f'>> {m.user.nick} ({m.user.ident}@{m.user.host}) joined {m.replyTo}',
    'NICK': lambda m: f'{m.user.nick} is now known as {m.messageString}',
    'PART': lambda m: f'<< {m.user.nick} ({m.user.ident}@{m.user.host}) left {m.replyTo}{": " + m.messageString if m.messageString else ""}',
    'QUIT': lambda m: f'<< {m.user.nick} ({m.user.ident}@{m.user.host}) quit{": " + m.messageString if m.messageString else ""}',
    'KICK': lambda m: f'-- {m.metadata["kicked"]} was kicked by {m.user.nick}{": " + m.messageString if m.messageString else ""}',
    'TOPIC': lambda m: f'-- {m.user.nick} set the topic to: {m.messageString}',
    'MODE': lambda m: formatMode(m),
}

logSelfFuncs = {
    ResponseType.Say: lambda bot, r: formatSelfPrivmsg(bot, r),
    ResponseType.Do: lambda bot, r: f'*{bot.nick} {r.response}*',
    ResponseType.Notice: lambda bot, r: f'[{bot.nick}] {r.response}',
}

targetFuncs = {
    'NICK': lambda bot, msg: [name for name, chan in bot.channels.items() if msg.user.nick in chan.users],
    'QUIT': lambda bot, msg: [chan.name for chan in msg.metadata['quitChannels']],
}


def formatSelfPrivmsg(bot, response):
    if bot.nick in bot.users and response.target in bot.channels:
        status = bot.channels[response.target].getHighestStatusOfUser(bot.users[bot.nick])
    else:
        status = ''

    return f'<{status}{bot.nick}> {response.response}'


def formatPrivmsg(msg: IRCMessage):
    if msg.targetType == TargetTypes.CHANNEL:
        status = msg.channel.getHighestStatusOfUser(msg.user)
    else:
        status = ''

    return f'<{status}{msg.user.nick}> {msg.messageString}'


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

    return f'-- {msg.user.nick} sets mode: {modeStr}'


def log(path, targets, text):
    now = datetime.datetime.utcnow()
    time = now.strftime("[%H:%M:%S]")
    data = f'{time} {text}'
    fileName = f'{now.strftime("%Y-%m-%d")}.log'

    for target in targets:
        print(target, data)

        fileDirs = os.path.join(path, target)
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
        return ['loglight', 'logdark']

    def help(self, arg):
        return 'loglight/logdark (-<numberofmessage>/<interval>) - Returns the log for the current channel.'

    def onLoad(self):
        self.cal = parsedatetime.Calendar()

    def input(self, message: IRCMessage):
        if message.type in logFuncs:
            logString = logFuncs[message.type](message)
            if message.type in targetFuncs:
                targets = targetFuncs[message.type](self.bot, message)
            else:
                targets = [message.replyTo]
            log(os.path.join(self.bot.logPath, self.bot.server), targets, logString)

    def output(self, response: IRCResponse):
        if response.type in logSelfFuncs:
            logString = logSelfFuncs[response.type](self.bot, response)
            log(os.path.join(self.bot.logPath, self.bot.server),
                [response.target],
                logString)

        return response

    def execute(self, message):
        if message.targetType != TargetTypes.CHANNEL:
            return IRCResponse(ResponseType.Say, "I don't keep logs for private messages.", message.replyTo)

        basePath = self.bot.logPath
        error = 'The date specified is invalid.'
        network = self.bot.server

        if len(message.parameterList) < 1:
            logDate = datetime.date.today()
        elif message.parameterList[0].startswith('-'):
            try:
                delta = int(message.parameterList[0][1:])
            except ValueError:
                return IRCResponse(ResponseType.Say, error, message.replyTo)
            logDate = datetime.date.today() - datetime.timedelta(delta)
        else:
            logDate = self.cal.parseDT(message.parameters)[0]

        strLogDate = logDate.strftime("%Y-%m-%d")
        logPath = os.path.join(basePath, network, message.replyTo, f'{strLogDate}.log')
        if not os.path.exists(logPath):
            return IRCResponse(ResponseType.Say, "I don't have that log.", message.replyTo)

        baseUrl = self.bot.config.getWithDefault('logurl', 'http://irc.example.com')
        channel = message.channel.name
        dark = f"{(message.command == 'logdark')}".lower()
        url = f'{baseUrl}?channel={channel[1:]}&network={network}&date={strLogDate}&darkmode={dark}'
        shortUrl = self.bot.moduleHandler.runActionUntilValue('shorten-url', url)
        if not shortUrl:
            shortUrl = url
        return IRCResponse(ResponseType.Say, f'Log for {channel} on {strLogDate}: {shortUrl}', message.replyTo)


logger = Log()
