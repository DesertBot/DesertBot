# -*- coding: utf-8 -*-
"""
Created on Feb 09, 2018

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer
from typing import List

import re
from collections import OrderedDict

from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Admin(BotCommand):
    def triggers(self):
        return ['admin']

    @admin("Only my admins may add new admins!")
    def _add(self, message):
        """add <nick/full hostmask> - adds the specified user to the bot admins list.
        You can list multiple users to add them all at once.
        Nick alone will be converted to a glob hostmask, eg: *!user@host"""

        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u"You didn't give me a user to add!",
                               message.replyTo)

        for adminName in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if adminName in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[adminName]
                    adminName = u'*!{}@{}'.format(user.user, user.host)

            admins = self.bot.config.getWithDefault('admins', [])
            admins.append(adminName)
            self.bot.config['admins'] = admins

        self.bot.config.writeConfig()
        return IRCResponse(ResponseType.Say,
                           u"Added specified users as bot admins!",
                           message.replyTo)

    @admin("Only my admins may remove admins!")
    def _del(self, message):
        """del <full hostmask> - removes the specified user from the bot admins list.
        You can list multiple users to remove them all at once."""
        if len(message.parameterList) < 2:
            return IRCResponse(ResponseType.Say,
                               u"You didn't give me a user to remove!",
                               message.replyTo)

        deleted = []
        skipped = []
        admins = self.bot.config.getWithDefault('admins', [])
        for adminName in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if adminName in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[admin]
                    adminName = u'*!{}@{}'.format(user.user, user.host)

            if adminName not in admins:
                skipped.append(adminName)
                continue

            admins.remove(adminName)
            deleted.append(adminName)

        self.bot.config['admins'] = admins
        self.bot.config.writeConfig()

        return IRCResponse(ResponseType.Say,
                           u"Removed '{}' as admin(s), {} skipped"
                           .format(u', '.join(deleted), len(skipped)),
                           message.replyTo)

    def _list(self, message):
        """list - lists all admins"""
        owners = self.bot.config.getWithDefault('owners', [])
        admins = self.bot.config.getWithDefault('admins', [])
        return IRCResponse(ResponseType.Say,
                           u"Owners: {} | Admins: {}".format(u', '.join(owners),
                                                             u', '.join(admins)),
                           message.replyTo)

    subCommands = OrderedDict([
        (u'add', _add),
        (u'del', _del),
        (u'list', _list)])

    def help(self, query: List[str]) -> str:
        if len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                return u'{1}admin {0}'.format(re.sub(r"\s+", u" ", self.subCommands[subCommand].__doc__),
                                              self.bot.commandChar)
            else:
                return self._unrecognizedSubcommand(subCommand)
        else:
            return self._helpText()

    def _helpText(self):
        return u"{1}admin ({0}) - manages users with bot admin permissions. " \
               u"Use '{1}help admin <subcommand> for subcommand help.".format(u'/'.join(self.subCommands.keys()),
                                                                              self.bot.commandChar)

    def _unrecognizedSubcommand(self, subCommand):
        return u"unrecognized subcommand '{}', " \
               u"available subcommands for admin are: {}".format(subCommand, u', '.join(self.subCommands.keys()))

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


adminCommand = Admin()
