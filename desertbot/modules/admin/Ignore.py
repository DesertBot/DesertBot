"""
Created on Feb 09, 2018

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

import re
from collections import OrderedDict

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
            return IRCResponse("You didn't give me a user to ignore!", message.replyTo)

        for ignore in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if ignore in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[ignore]
                    ignore = '*!{}@{}'.format(user.nick, user.host)

            ignores = self.bot.config.getWithDefault('ignored', [])
            ignores.append(ignore)
            self.bot.config['ignored'] = ignores

        self.bot.config.writeConfig()
        return IRCResponse("Now ignoring specified users!", message.replyTo)

    @admin("Only my admins may remove ignores!")
    def _del(self, message):
        """del <full hostmask> - removes the specified user from the ignored list.
        You can list multiple users to remove them all at once."""
        if len(message.parameterList) < 2:
            return IRCResponse("You didn't give me a user to unignore!", message.replyTo)

        deleted = []
        skipped = []
        ignores = self.bot.config.getWithDefault('ignored', [])
        for unignore in message.parameterList[1:]:
            if message.replyTo in self.bot.channels:
                if unignore in self.bot.channels[message.replyTo].users:
                    user = self.bot.channels[message.replyTo].users[unignore]
                    unignore = '*!{}@{}'.format(user.nick, user.host)

            if unignore not in ignores:
                skipped.append(unignore)
                continue

            ignores.remove(unignore)
            deleted.append(unignore)

        self.bot.config['ignored'] = ignores
        self.bot.config.writeConfig()

        return IRCResponse("Removed '{}' from ignored list, {} skipped"
                           .format(', '.join(deleted), len(skipped)), message.replyTo)

    def _list(self, message):
        """list - lists all ignored users"""
        ignores = self.bot.config.getWithDefault('ignored', [])
        return IRCResponse("Ignored Users: {}".format(', '.join(ignores)), message.replyTo)

    subCommands = OrderedDict([
        ('add', _add),
        ('del', _del),
        ('list', _list)])

    def help(self, query) -> str:
        if len(query) > 1:
            subCommand = query[1].lower()
            if subCommand in self.subCommands:
                return ('{1}ignore {0}'
                        .format(re.sub(r"\s+", " ", self.subCommands[subCommand].__doc__),
                                self.bot.commandChar))
            else:
                return self._unrecognizedSubcommand(subCommand)
        else:
            return self._helpText()

    def _unrecognizedSubcommand(self, subCommand):
        return ("unrecognized subcommand '{}', "
                "available subcommands for ignore are: {}"
                .format(subCommand, ', '.join(self.subCommands)))

    def _helpText(self):
        return ("{1}ignore ({0})"
                " - manages ignored users."
                " Use '{1}help ignore <subcommand> for subcommand help."
                .format('/'.join(self.subCommands), self.bot.commandChar))

    def execute(self, message):
        if len(message.parameterList) > 0:
            subCommand = message.parameterList[0].lower()
            if subCommand not in self.subCommands:
                return IRCResponse(self._unrecognizedSubcommand(subCommand), message.replyTo)
            return self.subCommands[subCommand](self, message)
        else:
            return IRCResponse(self._helpText(), message.replyTo)


ignore = Ignore()
