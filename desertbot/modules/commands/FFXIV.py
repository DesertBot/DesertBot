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
        return "Commands: ffxiv [char/jobs/job <job abrv>/portrait] <name> <server>"

    def execute(self, message: IRCMessage):
        params = message.parameterList.copy()
        if not params:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)
        elif len(params) == 1:
            # Use the user's linked character name and server as parameters if none were given
            # TODO: lookup user's linked name & server
            params.append()
        elif len(params) < 4:
            return IRCResponse(ResponseType.Say, self.help(None), message.replyTo)

        subCommand = params[0].lower()

        if subCommand == 'char':
            name = " ".join(params[1:-1])
            server = params[-1]
            char = self._lookupCharacterByName(name, server)
            if not char:
                return IRCResponse(ResponseType.Say,
                                   self._noCharFound(name, server),
                                   message.replyTo)
            name = char['Character']['Name']
            title = f"<*{char['Character']['Title']['Name']}*>"
            tPrefix = not char['Character']['TitleTop']
            nameTitle = f"{title+' ' if tPrefix else ''}{name}{' '+title if not tPrefix else ''}"

            FCName = char['FreeCompany']['Name']
            FCTag = char['FreeCompany']['Tag']
            FC = f"FC: {FCName} <{FCTag}>"

            GCName = char['Character']['GrandCompany']['Company']['Name']
            GCRank = char['Character']['GrandCompany']['Rank']['Name']
            GC = f"{GCRank}{formatColour(' of the ', f=c.grey)}{GCName}"

            nameday = f"Nameday: {char['Character']['Nameday']}"

            deity = f"Guardian: {char['Character']['GuardianDeity']['Name']}"

            town = f"Start City: {char['Character']['Town']['Name']}"

            race = char['Character']['Race']['Name']
            tribe = char['Character']['Tribe']['Name']
            gender = {1: '♂', 2: '♀'}[char['Character']['Gender']]
            rcg = f"{race} {tribe} {gender}"

            s = f"{formatColour(' | ', f=c.grey)}"

            return IRCResponse(ResponseType.Say,
                               s.join([nameTitle, rcg, nameday, deity, town, GC, FC]),
                               message.replyTo)

        elif subCommand == 'portrait':
            name = " ".join(params[1:-1])
            server = params[-1]
            char = self._lookupCharacterByName(name, server)
            if not char:
                return IRCResponse(ResponseType.Say,
                                   self._noCharFound(name, server),
                                   message.replyTo)
            return IRCResponse(ResponseType.Say, char['Character']['Portrait'], message.replyTo)

        elif subCommand == 'jobs':
            name = " ".join(params[1:-1])
            server = params[-1]
            char = self._lookupCharacterByName(name, server)
            if not char:
                return IRCResponse(ResponseType.Say,
                                   self._noCharFound(name, server),
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
            jobAbrv = params[1].upper()
            if jobAbrv not in self.jobAbrvMap.values():
                return IRCResponse(ResponseType.Say,
                                   f"'{params[1]}' is not a recognized FFXIV job abbreviation",
                                   message.replyTo)

            name = " ".join(params[2:-1])
            server = params[-1]
            char = self._lookupCharacterByName(name, server)
            if not char:
                return IRCResponse(ResponseType.Say,
                                   self._noCharFound(name, server),
                                   message.replyTo)

            jobMap = self._mapJobAbrvs(char['Character'])
            job = jobMap[jobAbrv]

            jobNames = job['Name'].split(' / ')
            if job['Level'] >= 30:
                jobName = jobNames[1].title()
            else:
                jobName = jobNames[0].title()

            lvl = self._boldIfMaxLevel(job)

            groups = self._getJobGroups(params[1])

            response = f"{jobName} | Categories: {','.join(groups)} | Lvl: {lvl}"

            xpMax = job['ExpLevelMax']
            if xpMax > 0:
                xpCurr = job['ExpLevel']
                xpTogo = job['ExpLevelTogo']
                xpPerc = (xpCurr / xpMax) * 100.0
                response += f" | Exp: {xpCurr:,}/{xpMax:,} {xpPerc:.2f}% ({xpTogo:,} to go)"

            return IRCResponse(ResponseType.Say, response, message.replyTo)

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
        lookupURL = f"{self.apiURL}/character/{ID}?extended=1&data=FC"
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

    def _noCharFound(self, name, server):
        return (f"No character named '{name}' found on FFXIV server '{server}'"
                f" (or the API timed out)")


ffxiv = FFXIV()
