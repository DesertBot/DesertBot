# -*- coding: utf-8 -*-
"""
Created on Feb 28, 2018

@author: Tyranic-Moron
"""

from fnmatch import fnmatch
from functools import wraps, partial
import logging

from desertbot.moduleinterface import BotModule
from desertbot.response import IRCResponse, ResponseType


def admin(func=None, msg=''):
    if callable(func):
        @wraps(func)
        def wrapped_func(inst, message):
            if not inst.checkPermissions(message):
                if msg:
                    return IRCResponse(ResponseType.Say, msg, message.ReplyTo)
                else:
                    return IRCResponse(ResponseType.Say,
                                       "Only my admins may use {!r}".format(message.Command),
                                       message.ReplyTo)
            return func(inst, message)

        return wrapped_func
    else:
        return partial(admin, msg=func)  # this seems wrong, should be msg=msg


class BotCommand(BotModule):
    def __init__(self):
        self.logger = logging.getLogger('desertbot.{}'.format(self.__class__.__name__))

    def triggers(self):
        return []

    def actions(self):
        return super(BotCommand, self).actions() + [('botmessage', 1, self.handleCommand)]

    def onLoad(self):
        self.triggerHelp = {}

    def displayHelp(self, query):
        if query[0].lower() in self.triggers() or query[0].lower() == self.__class__.__name__.lower():
            return self.help(query)

    def help(self, query):
        if query[0].lower() in self.triggerHelp:
            return self.triggerHelp[query[0].lower()]
        return super(BotCommand, self).help(query)

    def checkPermissions(self, message):
        """
        @type message: IRCMessage
        @rtype Boolean
        """
        for owner in self.bot.config.getWithDefault('owners', []):
            if fnmatch(message.User.String, owner):
                return True
        for admin in self.bot.config.getWithDefault('admins', []):
            if fnmatch(message.User.String, admin):
                return True
        return False

    def handleCommand(self, message):
        if not self.shouldExecute(message):
            return

        try:
            return self.execute(message)
        except Exception:
            self.logger.exception("Python execution error while running command {!r}".format(message.Command))

    def shouldExecute(self, message):
        """
        @type message: IRCMessage
        @rtype Boolean
        """
        if message.Command.lower() not in [t.lower() for t in self.triggers()]:
            return False

        return True

    def execute(self, message):
        """
        @type message: IRCMessage
        @rtype IRCResponse | list[IRCResponse]
        """
        return IRCResponse(ResponseType.Say, '<command not yet implemented>', message.ReplyTo)
