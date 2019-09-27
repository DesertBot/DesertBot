from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, ignore
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import random
import datetime
import re

from desertbot.message import IRCMessage
from desertbot.response import ResponseType, IRCResponse


@implementer(IPlugin, IModule)
class Responses(BotCommand):
    def actions(self):
        return super(Responses, self).actions() + [('message-channel', 1, self.respond),
                                                   ('message-user', 1, self.respond),
                                                   ('action-channel', 1, self.respond),
                                                   ('action-user', 1, self.respond)]

    def help(self, query):
        return ('Talkwords from the mouth place'
                ' - response <name> to enable/disable a particular response'
                ' (might need to check the source for names)')

    def onLoad(self):
        try:
            self.responses = MobroResponseDict()

            ##################################
            #                                #
            #    ADD RESPONSES HERE, BRO     #
            #                                #
            ##################################

            # '''Example'''
            # self.responses.add(MobroResponse(	name,
            #                    Response Message(s),
            #                    Regex(es),
            #                    ResponseType (default Say),
            #                    Enabled (default True),
            #                    Seconds Until Response Can Trigger Again (default 300),
            #                    All Regexes Must Match (default True)))

            '''Responds to inappropriately combined adjectives'''
            self.responses.add(MobroResponse('squishy',
                                             'GODDAMMIT, GET YOUR HAND OUT OF THERE',
                                             ["([^a-zA-Z]|^)wet (and|&|'?n'?) squishy([^a-zA-Z]|$)",
                                              "([^a-zA-Z]|^)squishy (and|&|'?n'?) wet([^a-zA-Z]|$)"],
                                             ResponseType.Say,
                                             True,
                                             300,
                                             False))

            '''Responds to the ocean as a caffeinated Pika'''
            self.responses.add(MobroResponse('ocean',
                                             'mimes out a *WHOOOOSH!*',
                                             '([^a-zA-Z]|^)ocean([^a-zA-Z]|$)',
                                             ResponseType.Do))

            '''Responds to incorrect windmill assumptions'''
            self.responses.add(MobroResponse('windmill',
                                             ['WINDMILLS DO NOT WORK THAT WAY!', 'GOODNIGHT!'],
                                             ['([^a-zA-Z]|^)windmills?([^a-zA-Z]|$)',
                                              '([^a-zA-Z]|^)cool([^a-zA-Z]|$)']))

            '''Responds to Pokemon as Joseph Ducreux'''
            self.responses.add(MobroResponse('pokemon',
                                             'Portable Atrocities! Must be encapsulated en masse!',
                                             '([^a-zA-Z]|^)pokemon([^a-zA-Z]|$)',
                                             ResponseType.Say,
                                             False))

            '''Guards against the Dutch'''
            self.responses.add(MobroResponse('dutch',
                                             'The Dutch, AGAIN!',
                                             '([^a-zA-Z]|^)dutch([^a-zA-Z]|$)',
                                             ResponseType.Say,
                                             False))

            '''Sensitive to bees'''
            self.responses.add(MobroResponse('bees',
                                             'BEES?! AAAARRGGHGHFLFGFGFLHL',
                                             '([^a-zA-Z]|^)bee+s?([^a-zA-Z]|$)'))

            '''Responds to cheese'''
            self.responses.add(MobroResponse('cheese',
                                             'loves cheese',
                                             '([^a-zA-Z]|^)cheese([^a-zA-Z]|$)',
                                             ResponseType.Do))

            '''Also respond to French cheese'''
            self.responses.add(MobroResponse('fromage',
                                             'adore le fromage',
                                             '([^a-zA-Z]|^)fromage([^a-zA-Z]|$)',
                                             ResponseType.Do))

            '''And Dutch cheese because it'll be funny if it ever comes up'''
            self.responses.add(MobroResponse('kaas',
                                             'is gek op kaas',
                                             '([^a-zA-Z]|^)kaas([^a-zA-Z]|$)',
                                             ResponseType.Do))

            '''Respond to Finnish cheese because lel'''
            self.responses.add(MobroResponse('juusto',
                                             'rakastaa juustoa',
                                             '([^a-zA-Z]|^)juusto([^a-zA-Z]|$)',
                                             ResponseType.Do))

            '''And why not German too?'''  # because it breaks everything apparently
#            self.responses.add(MobroResponse(u'Käse',
#                                             u'liebt Käse',
#                                             ur'([^a-zA-Z]|^)Käse([^a-zA-Z]|$)',
#                                             ResponseType.Do))

            '''Responds to JavaScript's insane shenanigans'''
            self.responses.add(MobroResponse('wat',
                                             'NaNNaNNaNNaN https://www.destroyallsoftware.com/talks/wat man!',
                                             '([^a-zA-Z]|^)wat([^a-zA-Z]|$)',
                                             ResponseType.Say,
                                             False))

            # Sorry man, I had to. I HAD to.
            '''Responds to Ponies'''
            self.responses.add(MobroResponse('ponies',
                                             'Ponies Ponies Ponies SWAG! https://www.youtube.com/watch?v=hx30VHwKa0Q',
                                             '([^a-zA-Z]|^)ponies([^a-zA-Z]|$)',
                                             ResponseType.Say,
                                             False))

            '''Responds to EVERYTHING being FINE'''
            self.responses.add(MobroResponse('everythingfine',
                                             "IT'S FINE, EVERYTHING IS FINE",
                                             "([^a-zA-Z]|^)everything('?s| is) fine([^a-zA-Z]|$)"))

            """Responds to traditional assertions."""
            self.responses.add(MobroResponse('tradition',
                                             'As is tradition.',
                                             '([^a-zA-Z]|^)as is tradition([^a-zA-Z]|$)'))

            # This one needs to mess with the object to work right.
            '''Responds to DuctTape being a dick in minecraft'''
            def ducktapeMatch(message):
                match = re.search('([^a-zA-Z]|^)minecraft([^a-zA-Z]|$)', message, re.IGNORECASE)
                self.ductMatch = re.search('([^a-zA-Z]|^)(?P<duc>duc[kt]tape)([^a-zA-Z]|$)', message, re.IGNORECASE)
                return match and self.ductMatch

            def ducktapeTalkwords(message):
                return [IRCResponse(ResponseType.Say,
                                    'Just saying, %s is a dick in Minecraft' % self.ductMatch.group('duc'),
                                    message.replyTo)]

            ducktape = MobroResponse('ducktape', '', '')
            ducktape.match = ducktapeMatch
            ducktape.talkwords = ducktapeTalkwords
            self.responses.add(ducktape)

            '''Responds randomly to various animal sounds'''
            def animalMatch(message):
                matchDict = {
                    r'(woo+f|r+u+ff+|arf|ba+r+k)': 'puppeh',
                    r'(bo+r+k)': 'pupper',
                    r'nya+n?~?': 'neko ₍˄·͈༝·͈˄₎◞',
                    r'squeak': 'mouse',
                    r'moo+': 'cow',
                    r'(twee+t|ca+w+|chirp)': 'bird',
                    r'ne+i+gh': 'horse',
                    r'ri+bb+i+t': 'frog',
                    r'bloo+p': 'fish',
                    r'o+i+n+k+': 'piggy',
                    r'ho+n+k+': 'goose',
                    r'hi+ss+': 'snake',
                    r'r+o+a+r+': 'lion',
                    r'(ho+w+l+|a+w?oo+)': 'wolf',
                    r'blee+p\s+bloo+p': 'droid',
                    r'y?arr+': 'pirate',
                    r'qua+ck': 'duck',
                    r'(hoo+t|whoo+)': 'owl',
                    r'br+a+i+n+s+': 'zombie',
                    r'(ba+w+k|clu+ck)': 'chicken',
                    r'baa+': 'sheep',
                    r'(blub(\s+)?)+': 'deep one',
                    r'bu*zz+': 'bee',
                    r'(boo+|oooo+)': 'spoopy goast',
                    r'(noo+t ?)+': 'penguin',
                    r'too+t': 'mastodon',
                    r'whee+k': 'guinea pig'
                }

                self.animal = None
                for match, animal in matchDict.items():
                    if re.search(r'^{}([^\s\w]+)?$'.format(match), message, re.IGNORECASE):
                        self.animal = animal
                        return True

                return False

            def animalTalkwords(message):
                # Specific user animals
                if self.animal == 'cow' and message.user.nick.lower() == 'neo-gabi':
                    return [IRCResponse(ResponseType.Do,
                                        'points at {0}, and says "{0} was the cow all along!"'
                                        .format(message.user.nick),
                                        message.replyTo)]

                randomChance = random.randint(1, 20)

                # Emily Bonus
                if message.user.nick == 'Emily':
                    randomChance = random.randint(1, 25)

                article = 'an' if self.animal[0] in 'aeiou' else 'a'

                # General user animals
                if randomChance == 1:
                    ''' User Critically Failed '''
                    if self.animal == 'droid':
                        return [IRCResponse(ResponseType.Say,
                                            '{} is DEFINITELY NOT the droid you are looking for.'.format(message.user.nick),
                                            message.replyTo)]
                    elif self.animal == 'goose':
                        return [IRCResponse(ResponseType.Say,
                                            '{} is a clown!'.format(message.user.nick),
                                            message.replyTo)]
                    else:
                        return [IRCResponse(ResponseType.Say,
                                            '{} critically fails at being {} {}.'.format(message.user.nick, article, self.animal),
                                            message.replyTo)]

                elif randomChance <= 8:
                    ''' User Is Not A [animal] '''
                    if self.animal == 'droid':
                        return [IRCResponse(ResponseType.Say,
                                            '{} is not the droid you are looking for.'.format(message.user.nick),
                                            message.replyTo)]
                    else:
                        return [IRCResponse(ResponseType.Say,
                                            '{} is not {} {}.'.format(message.user.nick, article, self.animal),
                                            message.replyTo)]
                elif randomChance <= 14:
                    '''User Might Be A [animal] '''
                    if self.animal == 'droid':
                        return [IRCResponse(ResponseType.Say,
                                            '{} might be the droid you are looking for.'.format(message.user.nick),
                                            message.replyTo)]
                    else:
                        return [IRCResponse(ResponseType.Say,
                                            '{} /might/ be {} {}.'.format(message.user.nick, article, self.animal),
                                            message.replyTo)]
                elif randomChance <= 19:
                    ''' User Is A [animal] '''
                    if self.animal == 'droid':
                        return [IRCResponse(ResponseType.Say,
                                            '{} is the droid you are looking for.'.format(message.user.nick),
                                            message.replyTo)]
                    else:
                        return [IRCResponse(ResponseType.Say,
                                            '{} is DEFINITELY {} {}.'.format(message.user.nick, article, self.animal),
                                            message.replyTo)]
                elif randomChance == 20:
                    ''' User Is A Critical [animal] '''
                    if self.animal == 'droid':
                        return [IRCResponse(ResponseType.Say,
                                            '{} is DEFINITELY the droid you are looking for.'.format(message.user.nick),
                                            message.replyTo)]
                    else:
                        return [IRCResponse(ResponseType.Say,
                                            '{} is a CRITICAL {}!'.format(message.user.nick, self.animal),
                                            message.replyTo)]
                else:
                    ''' Roll is outside of bounds, Magic! '''
                    return [IRCResponse(ResponseType.Say,
                                        'You are clearly a magician rolling out of bounds like that!',
                                        message.replyTo)]

            animalResponse = MobroResponse('animal', '', '', seconds=0)
            animalResponse.match = animalMatch
            animalResponse.talkwords = animalTalkwords
            self.responses.add(animalResponse)

            ##################################
            #                                #
            #   OK I'VE GOT THIS NOW, BRO    #
            #                                #
            ##################################
        except Exception:
            self.logger.exception("Exception in response.")

    @ignore
    def respond(self, message: IRCMessage):
        if message.command:
            return

        triggers = []
        for response in self.responses.dict:
            trig = self.responses.dict[response].trigger(message)
            if isinstance(trig, str):
                trig = [trig]
            try:
                triggers.extend(trig)
            except Exception:
                triggers = triggers
        return triggers

    @ignore
    def execute(self, message: IRCMessage):
        if len(message.parameterList) > 0:
            enableds = []
            for param in message.parameterList:
                enableds.append(self.responses.toggle(param, message))
            return enableds
        else:
            enabled = []
            disabled = []
            for name, response in self.responses.dict.items():
                if response.enabled:
                    enabled.append(name)
                else:
                    disabled.append(name)

            enabled = sorted(enabled)
            disabled = sorted(disabled)

            return [IRCResponse(ResponseType.Say,
                                'Enabled responses: {}'.format(', '.join(enabled)),
                                message.replyTo),
                    IRCResponse(ResponseType.Say,
                                'Disabled responses: {}'.format(', '.join(disabled)),
                                message.replyTo)]


class MobroResponse(object):
    lastTriggered = datetime.datetime.min

    def __init__(self, name, response, regex, responseType=ResponseType.Say,
                 enabled=True, seconds=300, regexMustAllMatch=True):
        self.name = name
        self.response = response
        self.regex = regex
        self.enabled = enabled
        self.seconds = seconds
        self.mustAllMatch = regexMustAllMatch
        self.responseType = responseType

    # overwrite this with your own match(message) function if a response calls for different logic
    def match(self, message):
        if isinstance(self.regex, str):
            self.regex = [self.regex]
        for regex in self.regex:
            if re.search(regex, message, re.IGNORECASE | re.UNICODE):
                if not self.mustAllMatch:
                    return True
            elif self.mustAllMatch:
                return False
        return self.mustAllMatch

    def eligible(self, message):
        return (self.enabled and
                (datetime.datetime.utcnow() - self.lastTriggered).seconds >= self.seconds and
                self.match(message))

    def chat(self, saywords: str, chatMessage: IRCMessage) -> IRCResponse:
        return IRCResponse(self.responseType, saywords, chatMessage.replyTo)

    def toggle(self, chatMessage: IRCMessage):
        self.enabled = not self.enabled
        return self.chat("Response {!r} {}".format(self.name, 'enabled' if self.enabled else 'disabled'), chatMessage)

    # overwrite this with your own talkwords(IRCMessage) function if a response calls for it
    def talkwords(self, chatMessage: IRCMessage):
        if isinstance(self.response, str):
            self.response = [self.response]
        responses = []
        for response in self.response:
            responses.append(self.chat(response, chatMessage))
        return responses

    def trigger(self, chatMessage: IRCMessage):
        if self.eligible(chatMessage.messageString):
            self.lastTriggered = datetime.datetime.utcnow()
            return self.talkwords(chatMessage)


class MobroResponseDict(object):
    dict = {}

    def add(self, mbr):
        self.dict[mbr.name] = mbr

    def toggle(self, name: str, chatMessage: IRCMessage):
        if name.lower() in self.dict:
            return self.dict[name.lower()].toggle(chatMessage)
        return


responses = Responses()
