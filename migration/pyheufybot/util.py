from desertbot.config import Config
from desertbot.datastore import DataStore
import argparse, os, shelve


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
            self.data = storage[section][options.network]
            storage.close()

        self.rootDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.dataPath = os.path.join(self.rootDir, 'data', self.network)
        if not os.path.exists(self.dataPath):
            os.makedirs(self.dataPath)

        self.storage = DataStore(os.path.join(self.dataPath, 'desertbot.json'))
