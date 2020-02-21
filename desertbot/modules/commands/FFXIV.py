from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType
from zope.interface import implementer

from desertbot.utils.string import formatColour, colour as c, formatBold, formatReverse

import urllib.parse


@implementer(IPlugin, IModule)
class FFXIV(BotCommand):
    apiURL = "https://xivapi.com"

    def triggers(self):
        return ["ffxiv"]

    def help(self, arg):
        return "Commands: ffxiv [iam/forgetme/char/jobs/job <job abrv>/portrait] <name> <server>"

    def onLoad(self):
        if "chars" not in self.storage:
            self.storage["chars"] = {}

#   subCommands = {
#       'link': _link,
#       'char': _char,
#       'jobs': _jobs,
#       'job': _job,
#       'portrait': _portrait,
#   }

    def execute(self, message: IRCMessage):
        params = message.parameterList.copy()
        if not params:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        subCommand = params.pop(0).lower()

        if subCommand == 'char':
            if params:
                char = self._lookupCharacterByParams(params)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedParamLookup(params),
                                       message.replyTo)
            else:
                if message.user.nick.lower() not in self.storage["chars"]:
                    return IRCResponse(ResponseType.Say, self._noCharLinked(), message.replyTo)
                char = self._lookupCharacterByStorage(message.user.nick)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedLinkLookup(message.user.nick),
                                       message.replyTo)

            name = char['Character']['Name']
            title = char['Character']['Title']['Name']
            tPrefix = not char['Character']['TitleTop']
            if title:
                fTitle = f"{' ' if not tPrefix else ''}<*{title}*>{' ' if tPrefix else ''}"
            else:
                fTitle = ''

            nameTitle = f"{fTitle if tPrefix else ''}{name}{fTitle if not tPrefix else ''}"

            if char['FreeCompany']:
                FCName = char['FreeCompany']['Name']
                FCTag = char['FreeCompany']['Tag']
                FC = f"FC: {FCName} <{FCTag}>"
            else:
                FC = None

            if char['Character']['GrandCompany']:
                GCName = char['Character']['GrandCompany']['Company']['Name']
                GCRank = char['Character']['GrandCompany']['Rank']['Name']
                GC = f"{GCRank}{formatColour(' of the ', f=c.grey)}{GCName}"
            else:
                GC = None

            nameday = f"Nameday: {char['Character']['Nameday']}"

            deity = f"Guardian: {char['Character']['GuardianDeity']['Name']}"

            town = f"Start City: {char['Character']['Town']['Name']}"

            race = char['Character']['Race']['Name']
            tribe = char['Character']['Tribe']['Name']
            gender = {1: '♂', 2: '♀'}[char['Character']['Gender']]
            rcg = f"{race} {tribe} {gender}"

            details = [d for d in [nameTitle, rcg, nameday, deity, town, GC, FC] if d]

            s = f"{formatColour(' | ', f=c.grey)}"

            return IRCResponse(ResponseType.Say, s.join(details), message.replyTo)

        elif subCommand == 'portrait':
            if params:
                char = self._lookupCharacterByParams(params)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedParamLookup(params),
                                       message.replyTo)
            else:
                if message.user.nick.lower() not in self.storage["chars"]:
                    return IRCResponse(ResponseType.Say, self._noCharLinked(), message.replyTo)
                char = self._lookupCharacterByStorage(message.user.nick)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedLinkLookup(message.user.nick),
                                       message.replyTo)

            return IRCResponse(ResponseType.Say, char['Character']['Portrait'], message.replyTo)

        elif subCommand == 'jobs':
            if params:
                char = self._lookupCharacterByParams(params)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedParamLookup(params),
                                       message.replyTo)
            else:
                if message.user.nick.lower() not in self.storage["chars"]:
                    return IRCResponse(ResponseType.Say, self._noCharLinked(), message.replyTo)
                char = self._lookupCharacterByStorage(message.user.nick)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedLinkLookup(message.user.nick),
                                       message.replyTo)

            jobMap = self._mapJobAbrvs(char['Character'])

            def formatJL(jobGroup, colour=None):
                filtered = self._filterJobList(self.jobGroups[jobGroup], jobMap)
                if filtered:
                    formatted = self._formatJobList(filtered, jobMap)
                    return f"{formatColour(jobGroup, f=colour)}[{formatted}]"
                else:
                    return None

            outputGroups = [
                formatJL('mDPS', c.red),
                formatJL('rpDPS', c.red),
                formatJL('rmDPS', c.red),
                formatJL('Tank', c.blue),
                formatJL('Healer', c.green),
                formatJL('DoH', c.orange),
                formatJL('DoL', c.yellow),
            ]
            outputGroups = [group for group in outputGroups if group]
            return IRCResponse(ResponseType.Say,
                               " ".join(outputGroups),
                               message.replyTo)

        elif subCommand == 'job':
            jobAbrv = params.pop(0).upper()
            if jobAbrv not in self.jobAbrvMap.values():
                return IRCResponse(ResponseType.Say,
                                   f"'{jobAbrv}' is not a recognized FFXIV job abbreviation",
                                   message.replyTo)

            if params:
                char = self._lookupCharacterByParams(params)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedParamLookup(params),
                                       message.replyTo)
            else:
                if message.user.nick.lower() not in self.storage["chars"]:
                    return IRCResponse(ResponseType.Say, self._noCharLinked(), message.replyTo)
                char = self._lookupCharacterByStorage(message.user.nick)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       self._failedLinkLookup(message.user.nick),
                                       message.replyTo)

            jobMap = self._mapJobAbrvs(char['Character'])
            job = jobMap[jobAbrv]

            jobNames = job['Name'].split(' / ')
            if job['Level'] >= 30:
                jobName = jobNames[1].title()
            else:
                jobName = jobNames[0].title()

            lvl = self._formatLevel(job)

            groups = self._getJobGroups(jobAbrv)

            response = f"{jobName} | Categories: {','.join(groups)} | Lvl: {lvl}"

            xpMax = job['ExpLevelMax']
            if xpMax > 0:
                xpCurr = job['ExpLevel']
                xpTogo = job['ExpLevelTogo']
                xpPerc = (xpCurr / xpMax) * 100.0
                response += f" | Exp: {xpCurr:,}/{xpMax:,} {xpPerc:.2f}% ({xpTogo:,} to go)"

            return IRCResponse(ResponseType.Say, response, message.replyTo)

        elif subCommand == 'iam':
            if len(params) > 1:
                name = " ".join(params[0:-1])
                server = params[-1]
                playerID = self._lookupCharacterIDByName(name, server)
                if not playerID:
                    return IRCResponse(ResponseType.Say,
                                       self._failedParamLookup(params),
                                       message.replyTo)
                char = self._lookupCharacterByID(playerID)
            else:
                playerID = params[0]
                char = self._lookupCharacterByID(playerID)
                if not char:
                    return IRCResponse(ResponseType.Say,
                                       f"No character found for ID {playerID}, "
                                       f"perhaps you wanted to add by FirstName LastName Server?",
                                       message.replyTo)

            self.storage["chars"][message.user.nick.lower()] = playerID
            char = char['Character']
            return IRCResponse(ResponseType.Say,
                               f"'{char['Name']}' on server '{char['DC']} - {char['Server']}' "
                               f"is now linked to your IRC nick! "
                               f"If this is the wrong character, add by lodestone profile ID. "
                               f"To unlink, use '{self.bot.commandChar}ffxiv forgetme'",
                               message.replyTo)

        elif subCommand == 'forgetme':
            if message.user.nick.lower() not in self.storage["chars"]:
                return IRCResponse(ResponseType.Say,
                                   "You aren't linked to an FFXIV character right now",
                                   message.replyTo)

            playerID = self.storage["chars"][message.user.nick.lower()]
            del self.storage["chars"][message.user.nick.lower()]
            return IRCResponse(ResponseType.Say,
                               f"You are now unlinked from FFXIV profile ID '{playerID}'",
                               message.replyTo)

    jobAbrvMap = {
        1: "GLA", 2: "PGL", 3: "MRD", 4: "LNC", 5: "ARC", 6: "CNJ", 7: "THM",
        8: "CRP", 9: "BSM", 10: "ARM", 11: "GSM", 12: "LTW", 13: "WVR", 14: "ALC",
        15: "CUL", 16: "MIN", 17: "BTN", 18: "FSH", 19: "PLD", 20: "MNK", 21: "WAR",
        22: "DRG", 23: "BRD", 24: "WHM", 25: "BLM", 26: "ACN", 27: "SMN", 28: "SCH",
        29: "ROG", 30: "NIN", 31: "MCH", 32: "DRK", 33: "AST", 34: "SAM", 35: "RDM",
        36: "BLU", 37: "GNB", 38: "DNC",
    }

    def _mapJobAbrvs(self, character):
        jobMap = {}
        for job in character['ClassJobs']:
            jobMap[self.jobAbrvMap[job['Job']['ID']]] = job
            jobMap[self.jobAbrvMap[job['Class']['ID']]] = job
        return jobMap

    jobGroups = {
        "DoW": ["GLA", "PLD", "PGL", "MNK", "MRD", "WAR", "LNC", "DRG", "ARC", "BRD",
                "ROG", "NIN", "MCH", "DRK", "SAM", "GNB", "DNC"],
        "DoM": ["CNJ", "WHM", "THM", "BLM", "ACN", "SMN", "SCH", "AST", "RDM", "BLU"],
        "DoH": ["CRP", "BSM", "ARM", "GSM", "LTW", "WVR", "ALC", "CUL"],
        "DoL": ["MIN", "BTN", "FSH"],
        "DPS": ["PGL", "MNK", "LNC", "DRG", "ARC", "BRD", "ROG", "NIN", "MCH", "SAM", "DNC",
                "THM", "BLM", "ACN", "SMN", "RDM", "BLU"],
        "mDPS": ["PGL", "MNK", "LNC", "DRG", "ROG", "NIN", "SAM"],
        "rpDPS": ["ARC", "BRD", "MCH", "DNC"],
        "rmDPS": ["THM", "BLM", "ACN", "SMN", "BLU", "RDM"],
        "Tank": ["GLA", "PLD", "MRD", "WAR", "DRK", "GNB"],
        "Healer": ["CNJ", "WHM", "SCH", "AST"],
    }

    def _getJobGroups(self, jobAbrv):
        return [group for group, jobs in self.jobGroups.items() if jobAbrv in jobs]

    def _filterJobList(self, jobs, jobMap):
        return [job for job in jobs
                if (jobMap[job]['Class']['ID'] == jobMap[job]['Job']['ID']
                    or (job == self.jobAbrvMap[jobMap[job]['Job']['ID']] and
                        jobMap[job]['Level'] >= 30)
                    or (job == self.jobAbrvMap[jobMap[job]['Class']['ID']] and
                        jobMap[job]['Level'] < 30))
                and jobMap[job]['Level'] > 0]

    def _formatJob(self, jobAbrv, job):
        if job['IsSpecialised']:
            return formatBold(jobAbrv)
        else:
            return jobAbrv

    def _formatLevel(self, job):
        if job['Level'] > 0 and job['ExpLevelMax'] == 0 and job['ExpLevel'] == 0:
            return formatReverse(job['Level'])
        else:
            return job['Level']

    def _formatJobList(self, jobs, jobMap):
        return " ".join([f"{self._formatJob(job, jobMap[job])}:{self._formatLevel(jobMap[job])}"
                         for job in jobs])

    def _lookupCharacterIDByName(self, name, server):
        name = urllib.parse.quote_plus(name)
        lookupURL = f"{self.apiURL}/character/search?name={name}&server={server}"
        print(lookupURL)
        response = self.bot.moduleHandler.runActionUntilValue("fetch-url", lookupURL)
        if not response:
            return None
        response = response.json()
        if not response['Results']:
            return None
        return response['Results'][0]['ID']

    def _lookupCharacterByID(self, ID):
        lookupURL = f"{self.apiURL}/character/{ID}?extended=1&data=FC,CJ"
        print(lookupURL)
        response = self.bot.moduleHandler.runActionUntilValue("fetch-url", lookupURL)
        if not response:
            return None
        response = response.json()
        return response

    def _lookupCharacterByName(self, name, server):
        ID = self._lookupCharacterIDByName(name, server)
        if not ID:
            return None
        return self._lookupCharacterByID(ID)

    def _lookupCharacterByParams(self, params):
        if not params:
            return None
        if len(params) >= 3:
            name = " ".join(params[0:-1])
            server = params[-1]
            return self._lookupCharacterByName(name, server)
        else:
            return self._lookupCharacterByID(params[0])

    def _lookupCharacterByStorage(self, nick):
        if nick.lower() not in self.storage["chars"]:
            return None
        return self._lookupCharacterByID(self.storage["chars"][nick.lower()])

    def _noCharLinked(self):
        return (f"You don't have a FFXIV character linked to your IRC nick. "
                f"Use '{self.bot.commandChar}ffxiv iam FirstName LastName Server' to link")

    def _failedLinkLookup(self, nick):
        return (f"Failed to lookup your linked character ID "
                f"'{self.storage['chars'][nick.lower()]}' (maybe the API timed out)")

    def _failedParamLookup(self, params):
        return f"Failed to find character '{' '.join(params)}' (or the API timed out)"


ffxiv = FFXIV()
