from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse

import requests
import http.client
from urllib3.exceptions import LocationParseError


@implementer(IPlugin, IModule)
class Down(BotCommand):
    def triggers(self):
        return ['down']

    def help(self, query):
        return 'down <url> - Check if the specified website URL is up'

    def execute(self, message: IRCMessage):
        if not message.parameterList:
            return IRCResponse("You didn't give me a URL to check!", message.replyTo)

        url = message.parameterList[0].strip()

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"

        try:
            res = self.bot.moduleHandler.runActionUntilValue("fetch-url", url, handleErrors=False)
        except LocationParseError:
            return IRCResponse("I don't know how to parse that URL!", message.replyTo)
        except requests.exceptions.Timeout:
            return IRCResponse(f"{url} looks to be down! It timed out after 10 seconds.", message.replyTo)
        except requests.exceptions.SSLError:
            return IRCResponse(f"{url} looks to be down! SSL verification failed.", message.replyTo)
        except requests.exceptions.ConnectionError:
            return IRCResponse(f"{url} looks to be down! I failed to connect to it.", message.replyTo)
        except Exception as e:
            self.logger.exception(e)
            return IRCResponse(f"{url} looks to be down? requests broke on it. Send help.", message.replyTo)

        if res.ok:
            return IRCResponse(f"{url} looks up to me! It returned {res.status_code} ({http.client.responses[res.status_code]}).", message.replyTo)
        else:
            return IRCResponse(f"{url} looks to be down! It returned {res.status_code} ({http.client.responses[res.status_code]}).", message.replyTo)


down = Down()
