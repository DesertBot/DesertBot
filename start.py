# -*- coding: utf-8 -*-
import argparse
import os

from desertbot.config import Config, ConfigError
from desertbot.factory import DesertBotFactory


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='An IRC bot written in Python.')
    parser.add_argument('-c', '--config', help='the config file to read from', type=str, required=True)
    cmdArgs = parser.parse_args()

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    config = Config(cmdArgs.config)
    try:
        config.loadConfig()
    except ConfigError as e:
        print(e)
    else:
        factory = DesertBotFactory(config)
