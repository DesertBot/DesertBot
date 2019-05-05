import sys
sys.path.insert(0, '../../')

from desertbot.utils.string import strToB64
from desertbot.utils.timeutils import timestamp
from migration.pyheufybot.util import PyHeufyBotUtil


if __name__ == '__main__':
    util = PyHeufyBotUtil('tells')
    if 'tells' not in util.storage or not type(util.storage['tells'] == list):
        util.storage['tells'] = []
    for tell in util.data:
        tell['date'] = tell['date'].isoformat()
        tell['datetoreceive'] = tell['datetoreceive'].isoformat()
        tell['body'] = strToB64(tell['body'])
        util.storage['tells'].append(tell)
    util.storage.save()
