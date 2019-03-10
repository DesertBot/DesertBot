import sys
sys.path.insert(0, '../../')

from migration.pyheufybot.util import PyHeufyBotUtil


if __name__ == '__main__':
    util = PyHeufyBotUtil('userlocations')
    if 'úserlocations' not in util.storage or not type(util.storage['userlocations'] == dict):
            util.storage['userlocations'] = {}  
    for nick, location in util.data.items():
        util.storage['userlocations'][nick] = location
    util.storage.save()
