"""
Created on Dec 07, 2013

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from zope.interface import implementer
from typing import List

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType

import subprocess
import os
import sys


@implementer(IPlugin, IModule)
class Update(BotCommand):
    def triggers(self):
        return ['update']

    def help(self, query: List[str]) -> str:
        return "update - pulls the latest code from GitHub and reloads affected modules"

    @admin
    def execute(self, message: IRCMessage):
        subprocess.check_call(['git', 'fetch'])

        output = subprocess.check_output(['git', 'log', '--no-merges',
                                          '--pretty=format:%s', '..origin/master'])
        changes = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        if len(changes) == 0:
            return IRCResponse('The bot is already up to date', message.replyTo)

        changes = list(reversed(changes))
        response = 'New commits: {}'.format(' | '.join(changes))

        # Get modified files
        output = subprocess.check_output(['git', 'show',
                                          '--pretty=format:',
                                          '--name-only',
                                          '--diff-filter=M',
                                          '..origin/master'])
        changedFiles = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        # Get added files
        output = subprocess.check_output(['git', 'show',
                                          '--pretty=format:',
                                          '--name-only',
                                          '--diff-filter=A',
                                          '..origin/master'])
        addedFiles = [s.strip().decode('utf-8', 'ignore') for s in output.splitlines()]

        returnCode = subprocess.check_call(['git', 'merge', 'origin/master'])

        if returnCode != 0:
            return IRCResponse('Merge after update failed, please merge manually', message.replyTo)

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
            changedPyFiles = [path for path in changedFiles if path.endswith(".py")]
            addedPyFiles = [path for path in addedFiles if path.endswith(".py")]

            modulesToReload = set()
            modulesToLoad = set()

            for filepath in changedPyFiles:
                # list contains full filepaths, split on os.path.sep and get last for filename
                filename = filepath.split(os.path.sep)[-1]
                if "modules" in filepath:
                    if filename in self.bot.moduleHandler.fileMap:
                        modulesToReload.add(self.bot.moduleHandler.fileMap[filename])
                else:
                    modulesToReload = set()
                    modulesToLoad = set()
                    response += (" | No auto-reload due to change(s) in bot core, "
                                 "please restart bot.")
                    self.logger.info("No auto-reload due to change in file {!r}".format(filename))
                    break

            for filepath in addedPyFiles:
                # list contains full filepaths, split on os.path.sep and get last for filename
                filename = filepath.split(os.path.sep)[-1]
                if "modules" in filepath:
                    # TODO a better way to do this, module name might not match file name.
                    modulesToLoad.add(filename.split(".py")[0])
                else:
                    modulesToReload = set()
                    modulesToLoad = set()
                    response += " | No auto-load due to change(s) in bot core, please restart bot."
                    self.logger.info("No auto-load due to change in file {!r}".format(filename))
                    break

            reloadedModules = []
            failures = []
            for moduleName in modulesToReload:
                if moduleName == "Update":
                    failures.append(moduleName)
                else:
                    try:
                        self.bot.moduleHandler.reloadModule(moduleName)
                    except Exception:
                        failures.append(moduleName)
                        self.logger.exception("Exception when auto-reloading module {!r}"
                                              .format(moduleName))
                    else:
                        reloadedModules.append(moduleName)
            if len(reloadedModules) > 0:
                response += " | Reloaded modules: {}".format(", ".join(reloadedModules))
            if len(failures) > 0:
                response += " | Failed to reload modules: {}".format(", ".join(failures))

            loadedModules = []
            failures = []
            for moduleName in modulesToLoad:
                try:
                    self.bot.moduleHandler.loadModule(moduleName)
                except Exception:
                    failures.append(moduleName)
                    self.logger.exception("Exception when auto-reloading module {!r}"
                                          .format(moduleName))
                else:
                    loadedModules.append(moduleName)
            if len(loadedModules) > 0:
                response += " | Loaded new modules: {}".format(", ".join(loadedModules))
            if len(failures) > 0:
                response += " | Failed to load new modules: {}".format(", ".join(failures))

        return IRCResponse(response, message.replyTo)


update = Update()
