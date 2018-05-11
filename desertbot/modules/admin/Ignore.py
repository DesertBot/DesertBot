# -*- coding: utf-8 -*-
"""
Created on Feb 09, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

import re
from collections import OrderedDict

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Ignore(BotCommand):
    def triggers(self):
        return ['ignore']

    @admin("Only my admins may add new ignores!")
    def _add(self, message):
        """add <nick/full hostmask> - adds the specified user to the ignored list.
        You can list multiple users to add them all at once.
        Nick alone will be converted to a glob hostmask, eg: *!user@host"""
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u"You didn't give me a user to ignore!",
                               message.replyTo)

        for ignore in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if ignore in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[ignore]
                    ignore = u'*!{}@{}'.format(user.user, user.host)

            ignores = self.bot.config.getWithDefault('ignored', [])
            ignores.append(ignore)
            self.bot.config['ignored'] = ignores

        self.bot.config.writeConfig()
        return IRCResponse(ResponseType.Say,
                           u"Now ignoring specified users!",
                           message.replyTo)

    @admin("Only my admins may remove ignores!")
    def _del(self, message):
        """del <full hostmask> - removes the specified user from the ignored list.
        You can list multiple users to remove them all at once."""
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u"You didn't give me a user to unignore!",
                               message.replyTo)

        deleted = []
        skipped = []
        ignores = self.bot.config.getWithDefault('ignored', [])
        for unignore in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if unignore in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[unignore]
                    unignore = u'*!{}@{}'.format(user.user, user.host)

            if unignore not in ignores:
                skipped.append(unignore)
                continue

            ignores.remove(unignore)
            deleted.append(unignore)

        self.bot.config['ignored'] = ignores
        self.bot.config.writeConfig()

        return IRCResponse(ResponseType.Say,
                           u"Removed '{}' from ignored list, {} skipped"
                           .format(u', '.join(deleted), len(skipped)),
                           message.replyTo)

    def _list(self, message):
        """list - lists all ignored users"""
        ignores = self.bot.config.getWithDefault('ignored', [])
        return IRCResponse(ResponseType.Say,
                           u"Ignored Users: {}".format(u', '.join(ignores)),
                           message.replyTo)

    subCommands = OrderedDict([
        (u'add', _add),
        (u'del', _del),
        (u'list', _list)])

    def help(self, message: IRCMessage) -> str:
        if len(message.parameterList) > 1:
            subCommand = message.parameterList[1].lower()
            if subCommand in self.subCommands:
                return u'{1}ignore {0}'.format(re.sub(r"\s+", u" ", self.subCommands[subCommand].__doc__),
                                               self.bot.commandChar)
            else:
                return self._unrecognizedSubcommand(subCommand)
        else:
            return self._helpText()

    def _unrecognizedSubcommand(self, subCommand):
        return u"unrecognized subcommand '{}', " \
               u"available subcommands for ignore are: {}".format(subCommand, u', '.join(self.subCommands.keys()))

    def _helpText(self):
        return u"{1}ignore ({0}) - manages ignored users. Use '{1}help ignore <subcommand> for subcommand help.".format(
            u'/'.join(self.subCommands.keys()), self.bot.commandChar)

    def execute(self, message):
        if len(message.parameterList) > 0:
            subCommand = message.parameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(ResponseType.Say,
                                   self._unrecognizedSubcommand(subCommand),
                                   message.replyTo)
            return self.subCommands[subCommand](self, message)
        else:
            return IRCResponse(ResponseType.Say,
                               self._helpText(),
                               message.replyTo)


ignore = Ignore()
