# -*- coding: utf-8 -*-
"""
Created on Dec 07, 2013

@author: Tyranic-Moron
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import subprocess
import os
import sys


@implementer(IPlugin, IModule)
class Update(BotCommand):
    def triggers(self):
        return ['update']
    
    def help(self, query):
        """
        @type query: list[str]
        """
        return "update - pulls the latest code from GitHub and reloads affected modules"

    @admin
    def execute(self, message):
        """
        @type message: IRCMessage
        """
        subprocess.check_call(['git', 'fetch'])

        output = subprocess.check_output(['git', 'log', '--no-merges',
                                          '--pretty=format:%s %b', '..origin/master'])
        changes = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        if len(changes) == 0:
            return IRCResponse(ResponseType.Say, 'The bot is already up to date', message.ReplyTo)

        changes = list(reversed(changes))
        response = u'New commits: {}'.format(u' | '.join(changes))
        
        output = subprocess.check_output(['git', 'show', '--pretty=format:', '--name-only', '..origin/master'])
        changedFiles = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        returnCode = subprocess.check_call(['git', 'merge', 'origin/master'])

        if returnCode != 0:
            return IRCResponse(ResponseType.Say,
                               'Merge after update failed, please merge manually',
                               message.ReplyTo)

        if 'requirements.txt' in changedFiles:
            try:
                subprocess.check_call([os.path.join(os.path.dirname(sys.executable), 'pip'),
                                       'install', '-r', 'requirements.txt'])
            except Exception:
                self.logger.exception("Exception when updating requirements!")
                response += " | Requirements update failed, check log."
            finally:
                response += " | No auto-reload due to requirements change, please restart bot."
        else:
            modulesToReload = []
            for filename in changedFiles:
                if filename in self.bot.moduleHandler.fileMap:
                    modulesToReload.append(self.bot.moduleHandler.fileMap[filename])
                else:
                    modulesToReload = []
                    response += " | No auto-reload due to change(s) in bot core, please restart bot."
                    self.logger.info("No auto-reload due to change in file {!r}".format(filename))
                    break

            reloadedModules = []
            failures = []
            for moduleName in modulesToReload:
                if moduleName == "Update":
                    failures.append(moduleName)
                try:
                    self.bot.moduleHandler.reloadModule(moduleName)
                except Exception:
                    failures.append(moduleName)
                    self.logger.exception("Exception when auto-reloading module {!r}".format(moduleName))
                else:
                    reloadedModules.append(moduleName)
            if len(reloadedModules) > 0:
                response += " | Reloaded modules: {}".format(", ".join(reloadedModules))
            if len(failures) > 0:
                response += " | Failed to reload modules: {}".format(", ".join(failures))

        return IRCResponse(ResponseType.Say,
                           response,
                           message.ReplyTo)


update = Update()
