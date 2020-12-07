"""
Created on May 27, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.channel import IRCChannel
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer
from typing import Dict

import re

from twisted.internet import task, threads

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Dominotifications(BotModule):
    def actions(self):
        return super(Dominotifications, self).actions() + [('urlfollow', 2, self.trackPizza)]

    def help(self, query):
        return "Automatic module that tracks Domino's pizza tracker links, " \
           "informing you of the progress of your pizza until delivery"

    def onLoad(self):
        self.trackers = Dict[str, TrackingDetails]

    def onUnload(self):
        self._stopAllPizzaTrackers()

    def trackPizza(self, message: IRCMessage, url: str):
        regex = r'www\.dominos\.(co\.uk|ie)/pizzatracker/?\?id=(?P<orderID>[a-zA-Z0-9=]+)'
        match = re.search(regex, url, re.IGNORECASE)

        if not match:
            return

        orderID = match.group('orderID')

        if orderID not in self.trackers:
            self.trackers[orderID] = TrackingDetails(message.user.nick, message.channel,
                                                     task.LoopingCall(self._pizzaLoop, orderID))
            self._startPizzaTracker(orderID)
            return ("PIZZA DETECTED! Now tracking {}'s Domino's pizza order!"
                    .format(message.user.nick),
                    '')
        else:
            return ("I'm already tracking that pizza for {}"
                    .format(self.trackers[orderID].orderer),
                    '')

    def _startPizzaTracker(self, orderID: str):
        self.trackers[orderID].tracker.start(30)

    def _pizzaLoop(self, orderID: str):
        return threads.deferToThread(self._pizzaTracker, orderID)

    def _pizzaTracker(self, orderID: str):
        steps = {6: "{}'s pizza order has been placed",
                 7: "{}'s pizza is being prepared",
                 5: "{}'s pizza is in the oven",
                 8: "{}'s pizza is sitting on a shelf, waiting for a driver",
                 9: "{}'s pizza is out for delivery",
                 3: "{}'s pizza has been delivered! Tracking stopped"}

        trackingDetails = self.trackers[orderID]

        trackURL = 'https://www.dominos.co.uk/pizzaTracker/getOrderDetails?id={}'.format(orderID)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', trackURL)

        if not response:
            # tracking API didn't respond
            self._stopPizzaTracker(orderID)
            self.bot.sendResponse(IRCResponse("The pizza tracking page linked by {}"
                                              " had some kind of error, tracking stopped"
                                              .format(trackingDetails.orderer), trackingDetails.channel.name))
            return

        j = response.json()

        if j['customerName'] is None:
            self._stopPizzaTracker(orderID)
            self.bot.sendResponse(IRCResponse("There are no pizza tracking details"
                                              " at the page linked by {}."
                                              .format(trackingDetails.orderer), trackingDetails.channel.name))
            return

        response = None

        step = j['statusId']
        if step != trackingDetails.step:
            trackingDetails.step = step
            response = IRCResponse(steps[step].format(trackingDetails.orderer), trackingDetails.channel.name)

        if step == 3:
            self._stopPizzaTracker(orderID)

        if response is not None:
            self.bot.sendResponse(response)

    def _stopPizzaTracker(self, orderID: str):
        if orderID in self.trackers:
            if self.trackers[orderID].tracker.running:
                self.trackers[orderID].tracker.stop()
            del self.trackers[orderID]
            return True
        return False

    def _stopAllPizzaTrackers(self):
        for orderID in self.trackers:
            self._stopPizzaTracker(orderID)


class TrackingDetails(object):
    def __init__(self, orderer: str, channel: IRCChannel, tracker: task.LoopingCall):
        self.orderer = orderer
        self.channel = channel
        self.tracker = tracker
        self.step = 0


dominotifications = Dominotifications()
