from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse, ResponseType
from zope.interface import implementer
from urllib.parse import quote_plus
from typing import List, Union
import re


@implementer(IPlugin, IModule)
class WolframAlpha(BotCommand):
    waBaseURL = "https://api.wolframalpha.com/v2/query"

    def triggers(self):
        return ['wolframalpha']

    def help(self, query: Union[List[str], None]) -> str:
        return 'Commands: wolframalpha <query> - Search Wolfram Alpha with a given query.'

    def onLoad(self):
        self.apiKey = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'WolframAlpha')

    def execute(self, message: IRCMessage) -> Union[IRCResponse, List[IRCResponse]]:
        if not self.apiKey:
            return IRCResponse(ResponseType.Say, "No API key found.", message.replyTo)

        if len(message.parameterList) == 0:
            return IRCResponse(ResponseType.Say, "You didn't give me a search query.", message.replyTo)

        params = {
            'input': message.parameters,
            'output': 'json',
            'appid': self.apiKey,
            'podindex': '5,4,3,2,1'
        }
        result = self.bot.moduleHandler.runActionUntilValue("fetch-url", self.waBaseURL, params)
        if not result or 'queryresult' not in result.json():
            output = 'No Wolfram Alpha data could be found at this moment. Try again later.'
        else:
            j = result.json()['queryresult']
            if 'error' in j and j['error'] != False:
                if 'msg' in j['error']:
                    output = f"Wolfram Alpha returned an error: {j['error']['msg']}"
                else:
                    output = 'Wolfram Alpha returned an unknown error'

            elif 'success' not in j or j['success'] == False:
                output = 'No results found.'
                didyoumeans = []
                if 'didyoumeans' in j:
                    tmpList = []
                    if isinstance(j['didyoumeans'], dict):
                        tmpList.append(j['didyoumeans'])
                    else:
                        tmpList = j['didyoumeans']

                    for didyoumean in tmpList:
                        if didyoumean['level'] != 'low':
                            didyoumeans.append(didyoumean['val'])
                if len(didyoumeans) > 0:
                    output = f"{output} Did you mean {','.join(didyoumeans)}?"
            else:
                result = None
                for pod in j['pods'][1:]:
                    if 'input' in [pod['id'].lower(), pod['title'].lower()]:
                        continue
                    for subpod in pod['subpods']:
                        if 'plaintext' not in subpod or subpod['plaintext'].startswith('\n'):
                            continue
                        plaintext = subpod['plaintext'].replace('\n', ' | ').strip()
                        if not plaintext:
                            continue # Probably an image
                        result = plaintext
                        break

                    if result:
                        break

                output = result if result else 'No relevant information was found'
                url = f'http://www.wolframalpha.com/input/?i={quote_plus(message.parameters)}'
                shortenedUrl = self.bot.moduleHandler.runActionUntilValue('shorten-url', url)
                if not shortenedUrl:
                    shortenedUrl = url
                output = f'{output} | {shortenedUrl}'
            graySplitter = colour(A.normal['', A.fg.gray['|'], ''])
            output = re.sub('(\| )+', '| ', re.sub(' +', ' ', output)).replace('|', graySplitter)
            return IRCResponse(ResponseType.Say, output, message.replyTo)


wolframAlpha = WolframAlpha()
