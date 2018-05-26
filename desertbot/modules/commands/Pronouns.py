from desertbot.datastore import Base
from sqlalchemy import Column, Integer, String

from twisted.plugin import IPlugin
from desertbot.datastore import Session
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
class PronounCommand(BotCommand):
    def triggers(self):
        return ["pronouns", "setpron", "rmpron"]

    def help(self, query):
        return "Commands: pronouns <user>, setpron <pronouns>, rmpron | "\
               "Query the user's pronouns, specify your own pronouns, or remove your pronouns from the database."

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse(ResponseType.Say, self.help(message.command), message.replyTo)

        session = Session()

        if message.command == "setpron":
            if len(message.parameterList) < 1:
                return IRCResponse(ResponseType.Say, "Your pronouns are... blank?", message.replyTo)
            user_pronouns = Pronoun(nick=message.user.nick, pronouns=message.parameterList[0])
            session.add(user_pronouns)
            session.commit()
        elif message.command == "rmpron":
            user_pronouns = session.query(Pronoun).filter(Pronoun.nick == message.user.nick).first()
            if user_pronouns is None:
                return IRCResponse(ResponseType.Say, "I don't even know your pronouns!", message.replyTo)
            else:
                session.delete(user_pronouns)
                session.commit()
                return IRCResponse(ResponseType.Say, "Your pronouns have been deleted.", message.replyTo)
        elif message.command == "pronouns":
            if len(message.parameterList) < 1:
                lookup = message.user.nick
            else:
                lookup = message.parameterList[0]

            user_pronouns = session.query(Pronoun.pronouns).filter(Pronoun.nick == lookup).first()
            if user_pronouns is None:
                return IRCResponse(ResponseType.Say, "User's pronouns have not been specified.", message.replyTo)
            return IRCResponse(ResponseType.Say, "{} uses <{}> pronouns.".format(lookup, user_pronouns), message.replyTo)


pronoun = PronounCommand()
