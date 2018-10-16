"""
Created on Feb 15, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer
from typing import List

import datetime
import re
import os
from collections import OrderedDict
import logging

from croniter import croniter
from twisted.internet import task
from twisted.internet import reactor
# from pytimeparse.timeparse import timeparse
from ruamel.yaml import YAML, yaml_object

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from desertbot.channel import IRCChannel
from desertbot.user import IRCUser
# from desertbot.utils import string

yaml = YAML()


@yaml_object(yaml)
class Task(object):
    yaml_tag = '!Task'

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
        self.command = command
        self.params = params
        self.user = user
        self.channel = channel

        # this will be set by start()
        self.task = None

        # these will be set by self.reInit()
        self.bot = None
        self.logger = None
        self.cron = None
        self.nextTime = None
        self.cronStr = None

        self.reInit(bot)

    def reInit(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('desertbot.{}'.format(Schedule.__name__))

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
        self.task.addErrback(self._deferredError)

    def activate(self):
        commandStr = '{}{} {}'.format(self.bot.commandChar, self.command,
                                      ' '.join(self.params))
        self.logger.info("Activated {!r}".format(commandStr))
        message = IRCMessage('PRIVMSG',
                             IRCUser(self.user),
                             IRCChannel(self.channel, self.bot),
                             commandStr,
                             self.bot)

        trigger = self.bot.moduleHandler.mappedTriggers[self.command].execute

        return trigger(message)

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
        skip = ['bot', 'task', 'cron', 'nextTime', 'logger']
        cleanedTask = dict((k, v)
                           for (k, v) in node.__dict__.items()
                           if k not in skip)
        return representer.represent_mapping(cls.yaml_tag, cleanedTask)

    def _deferredError(self, error):
        self.logger.exception("Python Execution Error in deferred call {!r}".format(error))
        self.logger.exception(error)


@implementer(IPlugin, IModule)
class Schedule(BotCommand):
    def triggers(self):
        return ['schedule']

    def _cron(self, message):
        """cron <min> <hour> <day> <month> <day of week> <task name> <command> (<params>)
        - schedules a repeating task using cron syntax https://crontab.guru/"""
        if len(message.parameterList) < 7:
            return IRCResponse(ResponseType.Say,
                               '{}'.format(re.sub(r"\s+", " ",
                                                  self._cron.__doc__)),
                               message.replyTo)

        taskName = message.parameterList[6]
        if taskName in self.schedule:
            response = 'There is already a scheduled task called {!r}'.format(taskName)
            return IRCResponse(ResponseType.Say, response, message.replyTo)

        command = message.parameterList[7].lower()
        if command not in self.bot.moduleHandler.mappedTriggers:
            return IRCResponse(ResponseType.Say,
                               '{!r} is not a recognized command'.format(command),
                               message.replyTo)

        params = message.parameterList[8:]

        cronStr = ' '.join(message.parameterList[1:6])

        self.schedule[taskName] = Task('cron', cronStr, command, params,
                                       message.user.fullUserPrefix(),
                                       message.channel.name,
                                       self.bot)
        self.schedule[taskName].start()

        self._saveSchedule()

        return IRCResponse(ResponseType.Say,
                           'Task {!r} created! Next execution: {}'
                           .format(taskName, self.schedule[taskName].nextTime),
                           message.replyTo)

    def _list(self, message):
        """list - lists scheduled task titles with their next execution time.
        * after the time indicates a repeating task"""
        taskList = ['{} ({}){}'.format(n, t.nextTime, '*' if t.type in ['cron'] else '')
                    for n, t in self.schedule.items()]
        tasks = 'Scheduled Tasks: ' + ', '.join(taskList)
        return IRCResponse(ResponseType.Say, tasks, message.replyTo)

    def _show(self, message):
        """show <task name> - gives you detailed information
        for the named task"""
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               'Show which task?',
                               message.replyTo)

        taskName = message.parameterList[1]

        if taskName not in self.schedule:
            return IRCResponse(ResponseType.Say,
                               'Task {!r} is unknown'.format(taskName),
                               message.replyTo)

        t = self.schedule[taskName]
        return IRCResponse(ResponseType.Say,
                           '{} {} {} {} | {}'
                           .format(t.type, t.timeStr, t.command,
                                   ' '.join(t.params), t.nextTime),
                           message.replyTo)

    def _stop(self, message):
        """stop <task name> - stops the named task"""
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               'Stop which task?',
                               message.replyTo)

        taskName = message.parameterList[1]

        if taskName not in self.schedule:
            return IRCResponse(ResponseType.Say,
                               'Task {!r} is unknown'.format(taskName),
                               message.replyTo)

        self.schedule[taskName].stop()
        del self.schedule[taskName]

        self._saveSchedule()

        return IRCResponse(ResponseType.Say,
                           'Task {!r} stopped'.format(taskName),
                           message.replyTo)

    subCommands = OrderedDict([
        ('cron', _cron),
        ('list', _list),
        ('show', _show),
        ('stop', _stop),
    ])

    def help(self, query: List[str]) -> str:
        if len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                sub = re.sub(r"\s+", " ",
                             self.subCommands[subCommand].__doc__)
                return '{1}schedule {0}'.format(sub, self.bot.commandChar)
            else:
                return self._unrecognizedSubCommand(subCommand)
        else:
            return self._helpText()

    def _unrecognizedSubCommand(self, subCommand):
        return ("unrecognized sub-command '{}', "
                "available sub-commands for schedule are: {}"
                .format(subCommand, ', '.join(self.subCommands.keys())))

    def _helpText(self):
        return ("{1}schedule ({0}) - manages scheduled tasks. "
                "Use '{1}help schedule <sub-command> for sub-command help."
                .format('/'.join(self.subCommands.keys()),
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
            for _, t in self.schedule.items():
                t.reInit(self.bot)
                t.start()
        except FileNotFoundError:
            self.schedule = {}

    def onUnload(self):
        # cancel everything
        for _, t in self.schedule.items():
            t.stop()

    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            subCommand = message.parameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(ResponseType.Say,
                                   self._unrecognizedSubCommand(subCommand),
                                   message.replyTo)
            return self.subCommands[subCommand](self, message)
        else:
            return IRCResponse(ResponseType.Say,
                               self._helpText(),
                               message.replyTo)


schedule = Schedule()
