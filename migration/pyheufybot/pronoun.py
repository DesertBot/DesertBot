import sys
sys.path.insert(0, '../../')

from desertbot.datastore import Base, Session
from desertbot.modules.commands.Pronouns import Pronoun
from migration.pyheufybot.util import PyHeufyBotUtil


if __name__ == '__main__':
    util = PyHeufyBotUtil('pronouns')
    Base.metadata.create_all(util.databaseEngine)
    session = Session()
    for nick, pronouns in util.data.items():
        userPronouns = Pronoun(nick=nick, pronouns=pronouns)
        session.add(userPronouns)
    session.commit()
    session.close()
