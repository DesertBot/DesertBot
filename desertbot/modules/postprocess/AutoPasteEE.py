"""
Created on May 21, 2014

@author: StarlitGhost
"""

from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

from desertbot.response import IRCResponse
from desertbot.utils import string


@implementer(IPlugin, IModule)
class AutoPasteEE(BotModule):
    def actions(self):
        return super(AutoPasteEE, self).actions() + [('response-message', 100, self.execute),
                                                     ('response-action', 100, self.execute),
                                                     ('response-notice', 100, self.execute)]

    def help(self, query):
        return ("Automatic module that uploads overly "
                "long reponses to paste.ee and gives you a link instead")

    def execute(self, response: IRCResponse):
        limit = 700  # chars
        expire = 10  # minutes
        if len(response.response) > limit:
            description = ('Response longer than {} chars intended for {}'
                           .format(limit, response.target))
            mh = self.bot.moduleHandler
            replaced = mh.runActionUntilValue('upload-pasteee',
                                              string.stripFormatting(response.response),
                                              description,
                                              expire)

            response.response = ('Response too long, pasted here instead: '
                                 '{} (Expires in {} minutes)'.format(replaced, expire))


autopasteee = AutoPasteEE()
