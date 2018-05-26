from desertbot.config import Config
from desertbot.datastore import Session
from sqlalchemy import create_engine
import argparse, dbm, os, pickle, shelve


class PyHeufyBotUtil(object):
    def __init__(self, section):
        parser = argparse.ArgumentParser(description='PyHeufyBot shelve parsing tool.')
        parser.add_argument('-s', '--storage', help='The storage file to use', type=str, default='../../data/heufybot.db')
        parser.add_argument('-n', '--network', help='The network name to import from', type=str, required=True)
        parser.add_argument('-c', '--config', help='the config file to read from', type=str, required=True)
        options = parser.parse_args()

        self.config = Config(options.config)
        self.config.loadConfig()

        with shelve.open(options.storage) as storage:
            for key in storage.keys():
                print(key)
            self.data = storage[section][options.network]
            storage.close()

        self.databaseEngine = create_engine(
            self.config.getWithDefault('database_engine', 'sqlite:///data/{}.db'.format(self.config['server'])))
        Session.configure(bind=self.databaseEngine)
