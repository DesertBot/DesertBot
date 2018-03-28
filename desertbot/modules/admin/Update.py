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
        helpDict = {
            u"update": u"update - pulls the latest code from GitHub",
            u"fullupdate": u"updatelibs - updates the libraries used by the bot (not implemented yet, does the same as update)"}
            
        command = query[0].lower()
        if command in helpDict:
            return helpDict[command]

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

        returnCode = subprocess.check_call(['git', 'merge', 'origin/master'])

        if returnCode != 0:
            return IRCResponse(ResponseType.Say,
                               'Merge after update failed, please merge manually',
                               message.ReplyTo)

        output = subprocess.check_output(['git', 'show', '--pretty=format:', '--name-only', '..origin/master'])
        changed_files = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        if 'requirements.txt' in changed_files:
            try:
                subprocess.check_call([os.path.join(os.path.dirname(sys.executable), 'pip'),
                                       'install', '-r', 'requirements.txt'])
            except Exception:
                self.logger.exception("Exception when updating requirements!")
                response += "Requirements update failed, check log."
            finally:
                response += " | No auto-reload due to requirements change, please restart bot."
        else:
            modules_to_reload = []
            for filename in changed_files:
                if filename in self.bot.moduleHandler.fileMap:
                    modules_to_reload.append(self.bot.moduleHandler.fileMap[filename])
                else:
                    modules_to_reload = []
                    response += " | No auto-reload due to change(s) in bot core, please restart bot."

            reloaded_modules = []
            failures = []
            for module_name in modules_to_reload:
                try:
                    self.bot.moduleHandler.reloadModule(module_name)
                except Exception:
                    failures.append(module_name)
                    self.logger.exception("Exception when auto-reloading module {!r}".format(module_name))
                else:
                    reloaded_modules.append(module_name)
            if len(reloaded_modules) > 0:
                response += " | Reloaded modules: {}".format(", ".join(reloaded_modules))
            if len(failures) > 0:
                response += " | Failed to reload modules: {}".format(", ".join(failures))

        return IRCResponse(ResponseType.Say,
                           response,
                           message.ReplyTo)


update = Update()
