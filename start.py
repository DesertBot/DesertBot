# -*- coding: utf-8 -*-
import argparse
import logging
import os
import sys

from desertbot.config import Config, ConfigError
from desertbot.factory import DesertBotFactory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An IRC bot written in Python.')
    parser.add_argument('-c', '--config', help='the config file to read from', type=str, required=True)
    cmdArgs = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Set up logging for stdout on the root 'desertbot' logger
    # Modules can then just add more handlers to the root logger to capture all logs to files in various ways
    rootLogger = logging.getLogger('desertbot')
    rootLogger.setLevel(logging.INFO)  # TODO change this from config value once it's loaded

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
