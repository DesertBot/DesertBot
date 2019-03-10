import sys
sys.path.insert(0, '../../')

from migration.pyheufybot.util import PyHeufyBotUtil


if __name__ == '__main__':
    util = PyHeufyBotUtil('pronouns')
    if "pronouns" not in util.storage or not type(util.storage["pronouns"] == dict):
            util.storage["pronouns"] = {}  
    for nick, pronouns in util.data.items():
        util.storage["pronouns"][nick] = pronouns
    util.storage.save()
