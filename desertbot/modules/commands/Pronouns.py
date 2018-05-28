from desertbot.datastore import Base
from sqlalchemy import Column, Integer, String

from twisted.plugin import IPlugin
from desertbot.datastore import sessionScope
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


class Pronoun(Base):
    __tablename__ = "pronouns"

    id = Column(Integer, primary_key=True)
    nick = Column(String)
    pronouns = Column(String)


@implementer(IPlugin, IModule)
class Pronouns(BotCommand):
    def triggers(self):
        return ["pronouns", "setpron", "rmpron"]

    def help(self, query):
        return "Commands: pronouns <user>, setpron <pronouns>, rmpron | "\
               "Query the user's pronouns, specify your own pronouns, or remove your pronouns from the database."

    def onLoad(self):
        Base.metadata.create_all(self.bot.databaseEngine)

    def onUnload(self):
        Base.metadata.remove(Pronoun.__table__)

    def execute(self, message: IRCMessage):
        with sessionScope() as session:
            if message.command == "setpron":
                if len(message.parameterList) < 1:
                    return IRCResponse(ResponseType.Say, "Your pronouns are... blank?", message.replyTo)
                userPronouns = session.query(Pronoun).filter(Pronoun.nick == message.user.nick.lower()).first()
                if userPronouns is not None:
                    userPronouns.pronouns = message.parameters
                else:
                    userPronouns = Pronoun(nick=message.user.nick.lower(), pronouns=message.parameters)
                session.add(userPronouns)
                return IRCResponse(ResponseType.Say, "Your pronouns have been set as <{}>.".format(message.parameters),
                                   message.replyTo)
            elif message.command == "rmpron":
                userPronouns = session.query(Pronoun).filter(Pronoun.nick == message.user.nick.lower()).first()
                if userPronouns is None:
                    return IRCResponse(ResponseType.Say, "I don't even know your pronouns!", message.replyTo)
                else:
                    session.delete(userPronouns)
                    return IRCResponse(ResponseType.Say, "Your pronouns have been deleted.", message.replyTo)
            elif message.command == "pronouns":
                if len(message.parameterList) < 1:
                    lookup = message.user.nick
                else:
                    lookup = message.parameterList[0]

                user = session.query(Pronoun).filter(Pronoun.nick == lookup.lower()).first()
                if user is None:
                    return IRCResponse(ResponseType.Say, "User's pronouns have not been specified.", message.replyTo)
                else:
                    return IRCResponse(ResponseType.Say, "{} uses <{}> pronouns.".format(lookup, str(user.pronouns)),
                                       message.replyTo)


pronouns = Pronouns()
