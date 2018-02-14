# -*- coding: utf-8 -*-
"""
Created on May 11, 2014

@author: Tyranic-Moron
"""

from pymoronbot.postprocessinterface import PostProcessInterface
from pymoronbot.utils import string


class StripColour(PostProcessInterface):

    def shouldExecute(self, response):
        """
        @type response: IRCResponse
        """
        if PostProcessInterface.shouldExecute(self, response):
            channel = self.bot.getChannel(response.Target)
            if channel is not None and 'c' in channel.Modes:
                # strip formatting if colours are blocked on the channel
                return True

    def execute(self, response):
        """
        @type response: IRCResponse
        """
        response.Response = string.stripFormatting(response.Response)
        return response
