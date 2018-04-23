# -*- coding: utf-8 -*-
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance as ndld


@implementer(IPlugin, IModule)
class StringUtils(BotModule):
    def actions(self):
        return super(StringUtils, self).actions() + [('closest-matches', 1, self.closestMatches)]

    def closestMatches(self, search, wordList, numMatches, threshold):
        """
        @type search: str
        @type wordList: [str]
        @type numMatches: int
        @type threshold: float
        @rtype: [str]
        """
        similarities = sorted([(ndld(search, word), word) for word in wordList])
        closeMatches = [word for (diff, word) in similarities if diff <= threshold]
        topN = closeMatches[:numMatches]
        return topN


stringUtils = StringUtils()
