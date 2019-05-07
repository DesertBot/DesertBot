import json
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import admin, BotCommand
from desertbot.response import IRCResponse, ResponseType

from desertbot.utils.api_keys import path as api_key_path


@implementer(IPlugin, IModule)
class APIKeys(BotCommand):
    def triggers(self):
        return ["apikey"]

    def help(self, query):
        return f"{self.bot.commandChar}apikey add/remove <name> <apikey> -- Add or remove the specified API key to the bot."

    @admin("[APIKey] Only my admins may manage API keys!")
    def execute(self, message: IRCMessage):
        if len(message.parameterList) != 3:
            return self.help(None)
        command = message.parameterList[0].lower()
        keyname = message.parameterList[1]
        key = message.parameterList[2]

        if command == "add":
            try:
                with open(api_key_path) as f:
                    keys = json.load(f.read())

                keys[keyname] = key
                with open(api_key_path, "w") as f:
                    json.dump(keys, f)

            except Exception:
                self.logger.exception(f"Failed to add API key {keyname}!")
                return IRCResponse(ResponseType.Say, f"Failed to add API key {keyname} to the bot!", message.replyTo)
            else:
                return IRCResponse(ResponseType.Say, f"Added the API key {keyname} to the bot.", message.replyTo)
        elif command == "remove":
            try:
                with open(api_key_path) as f:
                    keys = json.load(f.read())

                if keyname in keys:
                    del keys[keyname]
                else:
                    return IRCResponse(ResponseType.Say, f"There is no API key named {keyname}!", message.replyTo)

                with open(api_key_path, "w") as f:
                    json.dump(keys, f)
            except Exception:
                self.logger.exception(f"Failed to remove API key {keyname}!")
                return IRCResponse(ResponseType.Say, f"Failed to remove API key {keyname} from the bot!", message.replyTo)
            else:
                return IRCResponse(ResponseType.Say, f"Removed the API key {keyname} from the bot.", message.replyTo)
        else:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)


apikeys = APIKeys()
