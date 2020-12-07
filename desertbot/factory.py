import logging

from twisted.internet import reactor, protocol

from desertbot.config import Config
from desertbot.desertbot import DesertBot

# Try to enable SSL support
try:
    from twisted.internet import ssl
except ImportError:
    ssl = None


class DesertBotFactory(protocol.ReconnectingClientFactory):
    def __init__(self, config: Config):
        self.logger = logging.getLogger('desertbot.factory')
        self.exitStatus = 0
        self.connectionAttempts = 0

        self.bot = DesertBot(self, config)
        self.protocol = self.bot

        self.server = config['server']
        self.port = config.getWithDefault('port', 6667)
        if config.getWithDefault('tls', False):
            self.logger.info('Attempting secure connection to {}:{}...'
                             .format(self.server, self.port))
            if ssl is not None:
                reactor.connectSSL(self.server, self.port, self, ssl.ClientContextFactory())
            else:
                self.logger.error('Connection to {}:{} failed;'
                                  ' PyOpenSSL is required for secure connections.'
                                  .format(self.server, self.port))
        else:
            self.logger.info('Attempting connection to {}:{}'.format(self.server, self.port))
            reactor.connectTCP(self.server, self.port, self)

    def startedConnecting(self, connector):
        self.connectionAttempts += 1
        self.logger.info(f'Started to connect, attempt #{self.connectionAttempts}')

    def buildProtocol(self, addr):
        self.logger.info('Connected.')
        self.logger.info('Resetting reconnection delay.')
        self.resetDelay()
        return self.bot

    def clientConnectionLost(self, connector, reason):
        if not self.bot.quitting and self.connectionAttempts < 10:
            self.logger.error('Connection lost! - {}'.format(reason))
            protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
        else:
            protocol.ClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        if self.connectionAttempts < 10:
            self.logger.error('Connection failed! - {}'.format(reason))
            protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
        else:
            protocol.ClientFactory.clientConnectionFailed(self, connector, reason)
