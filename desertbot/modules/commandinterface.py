"""
Created on Feb 28, 2018

@author: StarlitGhost
"""

from fnmatch import fnmatch
from functools import wraps, partial
from typing import Callable, List, Optional, Tuple, Union

from desertbot.message import IRCMessage
from desertbot.moduleinterface import BotModule
from desertbot.response import IRCResponse, ResponseType


def admin(func=None, msg=''):
    if callable(func):
        @wraps(func)
        def wrapped_func(inst, message):
            if not inst.checkPermissions(message):
                if msg:
                    return IRCResponse(ResponseType.Say, msg, message.replyTo)
                else:
                    return IRCResponse(ResponseType.Say,
                                       "Only my admins may use {!r}".format(message.command),
                                       message.replyTo)
            return func(inst, message)

        return wrapped_func
    else:
        return partial(admin, msg=func)  # this seems wrong, should be msg=msg


class BotCommand(BotModule):
    def __init__(self):
        BotModule.__init__(self)
        self.triggerHelp = {}

    def triggers(self):
        return []

    def actions(self) -> List[Tuple[str, int, Callable]]:
        return super(BotCommand, self).actions() + [('botmessage', 1, self.handleCommand)]

    def onLoad(self) -> None:
        pass

    def displayHelp(self, query: List[str]) -> str:
        lowQuery = query[0].lower()
        if lowQuery in self.triggers() or lowQuery == self.__class__.__name__.lower():
            return self.help(query)

    def help(self, query: Union[List[str], None]) -> str:
        if query is not None and query[0].lower() in self.triggerHelp:
            return self.triggerHelp[query[0].lower()]
        return super(BotCommand, self).help(query)

    def checkPermissions(self, message: IRCMessage) -> bool:
        for owner in self.bot.config.getWithDefault('owners', []):
            if fnmatch(message.user.fullUserPrefix(), owner):
                return True
        for admin in self.bot.config.getWithDefault('admins', []):
            if fnmatch(message.user.fullUserPrefix(), admin):
                return True
        return False

    def handleCommand(self, message: IRCMessage) -> Optional[IRCResponse]:
        if not self.shouldExecute(message):
            return

        try:
            return self.execute(message)
        except Exception as e:
            self.logger.exception("Python execution error while running command {!r}"
                                  .format(message.command))
            errorText = ("Python execution error while running command {!r}: {}: {}"
                         .format(message.command, type(e).__name__, str(e)))
            self.bot.output.cmdPRIVMSG(message.replyTo, errorText)

            self.bot.reraiseIfDebug(e)

    def shouldExecute(self, message: IRCMessage) -> bool:
        if message.command.lower() not in [t.lower() for t in self.triggers()]:
            return False

        return True

    def execute(self, message: IRCMessage) -> Union[IRCResponse, List[IRCResponse]]:
        return IRCResponse(ResponseType.Say, '<command not yet implemented>', message.replyTo)
