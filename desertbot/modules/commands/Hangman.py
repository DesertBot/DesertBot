"""
Created on Jan 23, 2017

@author: StarlitGhost
"""
import random
import re
from collections import OrderedDict
from typing import List, Union
from unicodedata import category as unicodeCategory

from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand, admin
from desertbot.response import IRCResponse


class AlreadyGuessedException(Exception):
    def __init__(self, letter):
        self.letter = letter
        self.message = "the letter '{}' has already been guessed".format(letter)


class WrongPhraseLengthException(Exception):
    def __init__(self, guessedLen, phraseLen):
        self.guessedLen = guessedLen
        self.phraseLen = phraseLen
        self.message = ("your guess is {} letters, but the target is {} letters long"
                        .format(guessedLen, phraseLen))


class PhraseMismatchesGuessesException(Exception):
    def __init__(self):
        self.message = "your guess does not match the revealed letters"


class PhraseUsesKnownBadLettersException(Exception):
    def __init__(self):
        self.message = "your guess uses letters that are known to be wrong"


class InvalidCharacterException(Exception):
    def __init__(self, char):
        self.char = char
        self.message = "'{}' is not a valid word character".format(char)


class GameState(object):
    def __init__(self, phrase, maxBadGuesses):
        self.phrase = phrase
        self.guesses = []
        self.badGuesses = 0
        self.maxBadGuesses = maxBadGuesses
        self.finished = False

    def guessLetter(self, letter):
        letter = letter.lower()
        if letter in self.guesses:
            raise AlreadyGuessedException(letter)
        if not self._isLetter(letter):
            raise InvalidCharacterException(letter)

        self.guesses.append(letter)

        if self._renderMaskedPhrase() == self.phrase:
            self.finished = True

        if letter not in self.phrase:
            self._incrementBadGuesses()
            return False
        else:
            return True

    def guessPhrase(self, phrase):
        phrase = phrase.lower()
        if not len(phrase) == len(self.phrase):
            raise WrongPhraseLengthException(len(phrase), len(self.phrase))

        maskedPhrase = self._renderMaskedPhrase()
        for i, c in enumerate(maskedPhrase):
            if c == '␣':
                if phrase[i] in self.guesses:
                    raise PhraseUsesKnownBadLettersException()
                if not self._isLetter(phrase[i]):
                    raise InvalidCharacterException(phrase[i])
                continue
            if phrase[i] != maskedPhrase[i]:
                raise PhraseMismatchesGuessesException()

        if phrase == self.phrase:
            for c in self.phrase:
                if c not in self.guesses:
                    self.guesses.append(c)
            self.finished = True
            return True
        else:
            self._incrementBadGuesses()
            return False

    def wOrP(self):
        if ' ' in self.phrase:
            return 'phrase'
        else:
            return 'word'

    def render(self):
        return '{} {} {} {}'.format(
                self._renderMaskedPhrase(),
                self._renderPhraseLen(),
                self._renderBadGuessIndicator(),
                self._renderGuesses())

    def _renderMaskedPhrase(self):
        maskedPhrase = [
            c if not self._isLetter(c) or c in self.guesses
            else '␣'
            for c in self.phrase
        ]
        return ''.join(maskedPhrase)

    def _renderPhraseLen(self):
        return '({})'.format(len(self.phrase))

    def _renderBadGuessIndicator(self):
        trail = []

        for pos in range(self.maxBadGuesses):
            if pos - self.badGuesses == 0:
                # spark
                trail.append('*')
            elif pos - self.badGuesses < 0:
                # bad guesses
                trail.append('.')
            else:
                # guesses remaining
                trail.append('-')

        if self.badGuesses != self.maxBadGuesses:
            bomb = 'O'
        else:
            bomb = '#'

        return '[{}{}]'.format(''.join(trail), bomb)

    def _renderGuesses(self):
        colouredGuesses = []
        for g in self.guesses:
            if g in self.phrase:
                colouredGuesses.append(colour(A.bold[A.fg.green[g]]))
            else:
                colouredGuesses.append(colour(A.fg.red[g]))
        reset = colour(A.normal[''])
        return '[{}{}]'.format(''.join(colouredGuesses), reset)

    def _incrementBadGuesses(self):
        self.badGuesses += 1
        if self.badGuesses == self.maxBadGuesses:
            self.finished = True

    @staticmethod
    def _isLetter(letter):
        return unicodeCategory(letter)[0] in ['L']


class PhraseList(object):
    def __init__(self):
        self.dataPath = 'data/hangman.txt'
        self.phraseList = self._loadPhrases()
        random.shuffle(self.phraseList)
        self.phraseGenerator = (p for p in self.phraseList)

    def shuffle(self):
        random.shuffle(self.phraseList)
        self.phraseGenerator = (p for p in self.phraseList)

    def getWord(self):
        try:
            return next(self.phraseGenerator)
        except StopIteration:
            self.shuffle()
            return next(self.phraseGenerator)

    def _loadPhrases(self):
        try:
            with open(self.dataPath, 'r') as f:
                return [str(line.rstrip()) for line in f]
        except IOError:
            return ['hangman.txt is missing!']

    def _savePhrases(self):
        with open(self.dataPath, 'w') as f:
            f.writelines(sorted(self.phraseList))


@implementer(IPlugin, IModule)
class Hangman(BotCommand):
    def triggers(self):
        return ['hangman', 'hm']

    def onLoad(self):
        self._helpText = ("{1}hangman ({0}/<letter>/<phrase>)"
                          " - plays games of hangman in the channel. "
                          "Use '{1}help hangman <subcommand>' for subcommand help."
                          .format('/'.join(self.subCommands.keys()), self.bot.commandChar))
        self.gameStates = {}
        self.phraseList = PhraseList()
        self.maxBadGuesses = 8

    def _start(self, message):
        """start - starts a game of hangman!"""
        channel = message.replyTo.lower()
        if channel in self.gameStates:
            return [IRCResponse('[Hangman] game is already in progress!', channel),
                    IRCResponse(self.gameStates[channel].render(), message.replyTo)]

        responses = []

        word = self.phraseList.getWord()
        self.gameStates[channel] = GameState(word, self.maxBadGuesses)
        responses.append(IRCResponse('[Hangman] started!', message.replyTo))
        responses.append(IRCResponse(self.gameStates[channel].render(), message.replyTo))

        return responses

    def _stop(self, message, suppressMessage=False):
        """stop - stops the current game. Bot-admin only"""
        if not suppressMessage:
            if not self.checkPermissions(message):
                return IRCResponse('[Hangman] only my admins can stop games!', message.replyTo)
        channel = message.replyTo.lower()
        if channel in self.gameStates:
            del self.gameStates[channel]
            if not suppressMessage:
                return IRCResponse('[Hangman] game stopped!', message.replyTo)

    @admin("[Hangman] only my admins can set the maximum bad guesses!")
    def _setMaxBadGuesses(self, message):
        """max <num> - sets the maximum number of bad guesses allowed in future games.\
        Must be between 1 and 20. Bot-admin only"""
        try:
            if len(message.parameterList[1]) < 3:
                maxBadGuesses = int(message.parameterList[1])
            else:
                raise ValueError
            if 0 < maxBadGuesses < 21:
                response = ('[Hangman] maximum bad guesses changed from {} to {}'
                            .format(self.maxBadGuesses, maxBadGuesses))
                self.maxBadGuesses = maxBadGuesses
                return IRCResponse(response, message.replyTo)
            else:
                raise ValueError
        except ValueError:
            maxBadMessage = '[Hangman] maximum bad guesses should be an integer between 1 and 20'
            return IRCResponse(maxBadMessage, message.replyTo)

    def _guess(self, message: IRCMessage) -> Union[IRCResponse, List[IRCResponse]]:
        channel = message.replyTo.lower()
        if channel not in self.gameStates:
            return IRCResponse('[Hangman] no game running, use {}hangman start to begin!'
                               .format(self.bot.commandChar), message.replyTo)

        responses = []
        gs = self.gameStates[channel]

        guess = message.parameters.lower()
        # single letter
        if len(guess) == 1:
            try:
                correct = gs.guessLetter(guess)
            except (AlreadyGuessedException,
                    InvalidCharacterException) as e:
                return self._exceptionFormatter(e, message.replyTo)
        # whole phrase
        else:
            try:
                correct = gs.guessPhrase(guess)
            except (WrongPhraseLengthException,
                    PhraseMismatchesGuessesException,
                    PhraseUsesKnownBadLettersException) as e:
                return self._exceptionFormatter(e, message.replyTo)

        user = message.user.nick
        # split the username with a zero-width space
        # hopefully this kills client highlighting on nick mentions
        # user = user[:1] + '\u200b' + user[1:]
        # try a tiny arrow instead, some clients actually render zero-width spaces
        colUser = user[:1] + '\u034e' + user[1:]
        if correct:
            colUser = colour(A.normal[A.fg.green[colUser]])
        else:
            colUser = colour(A.normal[A.fg.red[colUser]])
        responses.append(IRCResponse('{} - {}'.format(gs.render(), colUser), message.replyTo))

        if gs.finished:
            if correct:
                responses.append(
                    IRCResponse('[Hangman] Congratulations {}!'.format(user), message.replyTo))
            else:
                responses.append(IRCResponse('[Hangman] {} blew up the bomb! The {} was {}'
                                             .format(user, gs.wOrP(), gs.phrase), message.replyTo))
            self._stop(message, suppressMessage=True)

        return responses

    @staticmethod
    def _exceptionFormatter(exception, target):
        return IRCResponse('[Hangman] {}'.format(exception.message), target)

    subCommands = OrderedDict([
        ('start', _start),
        ('stop', _stop),
        ('max', _setMaxBadGuesses),
    ])

    def help(self, message: IRCMessage):
        if len(message.parameterList) == 1:
            return self._helpText

        subCommand = message.parameterList[1].lower()
        if subCommand in self.subCommands:
            if getattr(self.subCommands[subCommand], '__doc__'):
                docstring = self.subCommands[subCommand].__doc__
                docstring = re.sub(r'\s+', ' ', docstring)
                return '{1}hangman {0}'.format(docstring, self.bot.commandChar)
            else:
                return "Oops! The help text for 'hangman {}' seems to be missing. "\
                       "Tell my owners!".format(subCommand)
        else:
            return self._helpText

    def execute(self, message: IRCMessage):
        if len(message.parameterList) == 0:
            return self._start(message)

        subCommand = message.parameterList[0].lower()
        if subCommand in self.subCommands:
            return self.subCommands[subCommand](self, message)
        else:
            return self._guess(message)


hangman = Hangman()
