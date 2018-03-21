# -*- coding: utf-8 -*-
import logging
from twisted.internet import reactor, protocol

from desertbot.desertbot import DesertBot


class DesertBotFactory(protocol.ReconnectingClientFactory):
    def __init__(self, config):
        """
        @type config: Config
        """
        self.logger = logging.getLogger('desertbot.factory')

        self.bot = DesertBot(self, config)
        self.protocol = self.bot

        self.server = config['server']
        self.port = config.getWithDefault('port', 6667)

        reactor.connectTCP(self.server, self.port, self)
        reactor.run()

    def startedConnecting(self, connector):
        self.logger.info('Started to connect')

    def buildProtocol(self, addr):
        self.logger.info('Connected.')
        self.logger.info('Resetting reconnection delay.')
        self.resetDelay()
        return self.bot

    def clientConnectionLost(self, connector, reason):
        if not self.bot.quitting:
            self.logger.error('Connection lost! - {}'.format(reason))
            protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        self.logger.error('Connection failed! - {}'.format(reason))
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
