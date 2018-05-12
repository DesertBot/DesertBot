# -*- coding: utf-8 -*-
import argparse
import logging
import os
import sys

from twisted.internet import reactor

from desertbot.config import Config, ConfigError
from desertbot.factory import DesertBotFactory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An IRC bot written in Python.')
    parser.add_argument('-c', '--config',
                        help='the config file to read from',
                        type=str, required=True)
    parser.add_argument('-l', '--loglevel',
                        help='the logging level (default INFO)',
                        type=str, default='INFO')
    cmdArgs = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Set up logging for stdout on the root 'desertbot' logger
    # Modules can then just add more handlers to the root logger to capture all logs to files in various ways
    rootLogger = logging.getLogger('desertbot')
    numericLevel = getattr(logging, cmdArgs.loglevel.upper(), None)
    if isinstance(numericLevel, int):
        rootLogger.setLevel(numericLevel)
    else:
        raise ValueError('Invalid log level {}'.format(cmdArgs.loglevel))

    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%H:%M:%S')

    streamHandler = logging.StreamHandler(stream=sys.stdout)
    streamHandler.setFormatter(logFormatter)

    rootLogger.addHandler(streamHandler)

    config = Config(cmdArgs.config)
    try:
        config.loadConfig()
    except ConfigError:
        rootLogger.exception("Failed to load configuration file {}".format(cmdArgs.config))
    else:
        factory = DesertBotFactory(config)
        reactor.run()
