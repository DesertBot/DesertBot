# -*- coding: utf-8 -*-
"""
Created on Feb 15, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import datetime
import re
import os
from collections import OrderedDict

from croniter import croniter
from twisted.internet import task
from twisted.internet import reactor
# from pytimeparse.timeparse import timeparse
from ruamel.yaml import YAML, yaml_object
from six import iteritems

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from desertbot.channel import IRCChannel
# from desertbot.utils import string

yaml = YAML()


@yaml_object(yaml)
class Task(object):
    yaml_tag = u'!Task'

    def __init__(self, type, timeStr, command, params, user, channel, bot):
        """
        @param type: str
        @param timeStr: str
        @param command: str
        @param params: list[str]
        @param user: str
        @param channel: str
        @param bot: DesertBot
        """
        self.type = type
        self.timeStr = timeStr
        self.commandStr = command
        self.params = params
        self.user = user
        self.channel = channel
        self.task = None

        # these will be set by self.reInit()
        self.bot = None
        self.command = None
        self.cron = None
        self.nextTime = None
        self.cronStr = None

        self.reInit(bot)

    def reInit(self, bot):
        self.bot = bot
        triggers = bot.moduleHandler.mappedTriggers
        self.command = triggers[self.commandStr].execute

        self.cronStr = {
            'cron': self.timeStr
        }[self.type]

        self.cron = croniter(self.cronStr, datetime.datetime.utcnow())
        self.nextTime = self.cron.get_next(datetime.datetime)

    def start(self):
        delta = self.nextTime - datetime.datetime.utcnow()
        seconds = delta.total_seconds()
        self.task = task.deferLater(reactor, seconds, self.activate)
        self.task.addCallback(self.cycle)

    def activate(self):
        commandStr = u'{}{} {}'.format(self.bot.commandChar, self.commandStr,
                                       u' '.join(self.params))
        message = IRCMessage('PRIVMSG', self.user, IRCChannel(self.channel),
                             commandStr,
                             self.bot)

        return self.command(message)

    def cycle(self, response):
        if not isinstance(response, list):
            response = [response]
        self.bot.moduleHandler.sendResponses(response)
        if self.type in ['cron']:
            self.nextTime = self.cron.get_next(datetime.datetime)
            self.start()

    def stop(self):
        if self.task:
            self.task.cancel()

    @classmethod
    def to_yaml(cls, representer, node):
        # trim out complex objects and things we can recreate
        skip = ['bot', 'task', 'command', 'cron', 'nextTime']
        cleanedTask = dict((k, v)
                           for (k, v) in node.__dict__.items()
                           if k not in skip)
        return representer.represent_mapping(cls.yaml_tag, cleanedTask)


@implementer(IPlugin, IModule)
class Schedule(BotCommand):
    def triggers(self):
        return ['schedule']

    def _cron(self, message):
        """cron <min> <hour> <day> <month> <day of week> <task name> <command> (<params>)
        - schedules a repeating task using cron syntax https://crontab.guru/"""
        if len(message.ParameterList) < 7:
            return IRCResponse(ResponseType.Say,
                               u'{}'.format(re.sub(r"\s+", u" ",
                                                   self._cron.__doc__)),
                               message.ReplyTo)

        taskName = message.ParameterList[6]
        if taskName in self.schedule:
            response = u'There is already a scheduled task called {!r}'.format(taskName)
            return IRCResponse(ResponseType.Say, response, message.ReplyTo)

        command = message.ParameterList[7].lower()
        if command not in self.bot.moduleHandler.mappedTriggers:
            return IRCResponse(ResponseType.Say,
                               u'{!r} is not a recognized command'.format(command),
                               message.ReplyTo)

        params = message.ParameterList[8:]

        cronStr = u' '.join(message.ParameterList[1:6])

        self.schedule[taskName] = Task('cron', cronStr, command, params,
                                       message.User.String,
                                       message.Channel.Name,
                                       self.bot)
        self.schedule[taskName].start()

        self._saveSchedule()

        return IRCResponse(ResponseType.Say,
                           u'Task {!r} created! Next execution: {}'
                           .format(taskName, self.schedule[taskName].nextTime),
                           message.ReplyTo)

    def _list(self, message):
        """list - lists scheduled task titles with their next execution time.
        * after the time indicates a repeating task"""
        taskList = [u'{} ({}){}'.format(n, t.nextTime, '*' if t.type in ['cron'] else '')
                    for n, t in iteritems(self.schedule)]
        tasks = u'Scheduled Tasks: ' + u', '.join(taskList)
        return IRCResponse(ResponseType.Say, tasks, message.ReplyTo)

    def _show(self, message):
        """show <task name> - gives you detailed information
        for the named task"""
        if len(message.ParameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u'Show which task?',
                               message.ReplyTo)

        taskName = message.ParameterList[1]

        if taskName not in self.schedule:
            return IRCResponse(ResponseType.Say,
                               u'Task {!r} is unknown'.format(taskName),
                               message.ReplyTo)

        t = self.schedule[taskName]
        return IRCResponse(ResponseType.Say,
                           u'{} {} {} {} | {}'
                           .format(t.type, t.timeStr, t.commandStr,
                                   u' '.join(t.params), t.nextTime),
                           message.ReplyTo)

    def _stop(self, message):
        """stop <task name> - stops the named task"""
        if len(message.ParameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u'Stop which task?',
                               message.ReplyTo)

        taskName = message.ParameterList[1]

        if taskName not in self.schedule:
            return IRCResponse(ResponseType.Say,
                               u'Task {!r} is unknown'.format(taskName),
                               message.ReplyTo)

        self.schedule[taskName].stop()
        del self.schedule[taskName]

        self._saveSchedule()

        return IRCResponse(ResponseType.Say,
                           u'Task {!r} stopped'.format(taskName),
                           message.ReplyTo)

    subCommands = OrderedDict([
        (u'cron', _cron),
        (u'list', _list),
        (u'show', _show),
        (u'stop', _stop),
    ])

    def help(self, query):
        """
        @type query: list[str]
        @rtype str
        """
        if len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                sub = re.sub(r"\s+", u" ",
                             self.subCommands[subCommand].__doc__)
                return u'{1}schedule {0}'.format(sub, self.bot.commandChar)
            else:
                return self._unrecognizedSubCommand(subCommand)
        else:
            return self._helpText()

    def _unrecognizedSubCommand(self, subCommand):
        return (u"unrecognized sub-command '{}', "
                u"available sub-commands for schedule are: {}"
                .format(subCommand, u', '.join(self.subCommands.keys())))

    def _helpText(self):
        return (u"{1}schedule ({0}) - manages scheduled tasks. "
                u"Use '{1}help schedule <sub-command> for sub-command help."
                .format(u'/'.join(self.subCommands.keys()),
                        self.bot.commandChar))

    def _saveSchedule(self):
        path = os.path.join(self.bot.dataPath, 'schedule.yaml')
        with open(path, 'w') as file:
            yaml.dump(self.schedule, file)

    def onLoad(self):
        # load schedule from data file
        try:
            path = os.path.join(self.bot.dataPath, 'schedule.yaml')
            with open(path, 'r') as file:
                self.schedule = yaml.load(file)

            if not self.schedule:
                self.schedule = {}

            # start them all going
            for _, t in iteritems(self.schedule):
                t.reInit(self.bot)
                t.start()
        except FileNotFoundError:
            self.schedule = {}

    def onUnload(self):
        # cancel everything
        for _, t in iteritems(self.schedule):
            t.stop()

    def execute(self, message):
        """
        @type message: IRCMessage
        """
        if len(message.ParameterList) > 0:
            subCommand = message.ParameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(ResponseType.Say,
                                   self._unrecognizedSubCommand(subCommand),
                                   message.ReplyTo)
            return self.subCommands[subCommand](self, message)
        else:
            return IRCResponse(ResponseType.Say,
                               self._helpText(),
                               message.ReplyTo)


schedule = Schedule()
