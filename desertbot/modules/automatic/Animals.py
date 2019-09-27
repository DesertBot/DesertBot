from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule, ignore
from zope.interface import implementer

import random
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Animals(BotModule):
    def actions(self):
        return super(Animals, self).actions() + [('message-channel', 1, self.respond),
                                                 ('message-user', 1, self.respond),
                                                 ('action-channel', 1, self.respond),
                                                 ('action-user', 1, self.respond)]

    def help(self, arg):
        return 'Responds to animal noises.'

    def onLoad(self) -> None:
        defaultReactions = {
            "1": "{user} critically fails at being {article} {animal}.",
            "8": "{user} is not {article} {animal}.",
            "14": "{user} /might/ be {article} {animal}.",
            "19": "{user} is DEFINITELY {article} {animal}.",
            "20": "{user} is {article} CRITICAL {animal}!"
        }
        self.animalResponses = self.bot.storage["animals"]
        self.animalReactions = dict(self.bot.storage["animalCustomReactions"])  # copy stored dict so we can extend with defaultReactions
        for _, animalName in self.animalResponses.items():
            self.animalReactions[animalName] = dict(defaultReactions)

    @ignore
    def respond(self, message: IRCMessage) -> IRCResponse:
        for match, animal in self.animalResponses.items():
            if re.search(r'^{}([^\s\w]+)?$'.format(match), message.messageString, re.IGNORECASE):
                # roll a d20
                roll = random.randint(1, 20)

                # construct animal reaction based on roll
                reactions = self.animalReactions[animal]
                # toungue-in-cheek default response, in case of Math Weirdness
                reaction = "{user} broke the animal responder, they're CLEARLY a magician!"
                # check each roll range and its matching reaction, which one do we want for the current roll?
                for rollMax, reactionCandidate in reactions.items():
                    if roll == int(rollMax):
                        # rolled exactly equal to one of the range maximums, this candidate is our wanted response
                        reaction = reactionCandidate
                        break
                    elif roll > int(rollMax):
                        # rolled higher than this range maximum, try next one
                        continue
                    else:
                        # rolled lower than this range maximum, but higher than a previous one, this candidate is our wanted response
                        reaction = reactionCandidate
                        break

                article = "an" if animal[0] in 'aeiou' else "a"
                # the reaction has placeholders, fill them out
                reaction = reaction.format(user=message.user.nick, article=article, animal=animal)

                return IRCResponse(ResponseType.Say, reaction, message.replyTo)


animals = Animals()
