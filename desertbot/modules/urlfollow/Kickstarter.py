# -*- coding: utf-8 -*-
"""
Created on Mar 13, 2014

@author: StarlitGhost
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

from desertbot.message import IRCMessage

from bs4 import BeautifulSoup
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

import datetime
from datetime import timezone
import html
import json
import math
import re


@implementer(IPlugin, IModule)
class Kickstarter(BotCommand):
    def actions(self):
        return super(Kickstarter, self).actions() + [('urlfollow', 2, self.follow)]

    def help(self, query):
        return 'Automatic module that follows Kickstarter URLs'

    def follow(self, _: IRCMessage, url: str) -> [str, None]:
        ksMatch = re.search(r'kickstarter\.com/projects/(?P<ksID>[^/]+/[^/&#\?]+)', url)
        if not ksMatch:
            return
        ksID = ksMatch.group('ksID')
        url = 'https://www.kickstarter.com/projects/{}/description'.format(ksID)
        response = self.bot.moduleHandler.runActionUntilValue('fetch-url', url)

        soup = BeautifulSoup(response.content, 'lxml')

        output = []

        state = soup.find(id='main_content')

        pageStructureChanged = '[Kickstarter changed their page structure again :S ({})]'
        if not state:
            return pageStructureChanged.format('#main_content'), None

        if 'Campaign-state-canceled' in state['class']:
            state = 'cancelled'
            campaignState = assembleFormattedText(A.normal[A.fg.red['Cancelled']])
        elif 'Campaign-state-suspended' in state['class']:
            state = 'suspended'
            campaignState = assembleFormattedText(A.normal[A.fg.blue['Suspended']])
        elif 'Campaign-state-failed' in state['class']:
            state = 'failed'
            campaignState = assembleFormattedText(A.normal[A.fg.red['Failed']])
        elif 'Campaign-state-successful' in state['class']:
            state = 'successful'
            campaignState = assembleFormattedText(A.normal[A.fg.green['Successful']])
        elif 'Campaign-state-live' in state['class']:
            state = 'live'
        else:
            return '[Kickstarter state {!r} not recognised]'.format(state['class']), None

        if state in ['live', 'cancelled', 'suspended']:
            data = soup.find(attrs={'data-initial': True})
            if not data:
                return pageStructureChanged.format('{} data-initial'.format(state)), None

            data = json.loads(data['data-initial'])
            data = data['project']

            shorturl = data['projectShortLink']

            title = data['name']
            if data['creator']:
                creator = data['creator']['name']
            else:
                creator = None

            backerCount = int(data['backersCount'])

            pledged = float(data['pledged']['amount'])
            goal = float(data['goal']['amount'])
            currency = data['goal']['currency']
            percentage = float(data['percentFunded'])

            if state == 'live':
                deadline = int(data['deadlineAt'])
                deadline = datetime.datetime.fromtimestamp(deadline, timezone.utc)
                now = datetime.datetime.now(timezone.utc)
                remaining = deadline - now
                remaining = remaining.total_seconds()
                remaining = remaining / 3600

                days = math.floor(remaining/24)
                hours = remaining % 24

                campaignState = 'Duration: {0:.0f} days {1:.1f} hours to go'.format(days, hours)
        else:
            # Successful
            pattern = re.compile(r'\n\s*window\.current_project\s*=\s*"(?P<data>\{.*?\})";\n')
            script = soup.find("script", text=pattern)
            if not script:
                return pageStructureChanged.format('non-live script pattern'), None

            data = pattern.search(script.text).group('data')
            data = html.unescape(data)
            data = json.loads(data)

            shorturl = data['urls']['web']['project_short']

            title = data['name']
            creator = data['creator']['name']

            backerCount = int(data['backers_count'])

            pledged = float(data['pledged'])
            goal = float(data['goal'])
            currency = data['currency']
            percentage = (pledged / goal)

        if creator is not None:
            name = str(assembleFormattedText(A.normal['{}',
                                                      A.fg.gray[' by '],
                                                      '{}'])).format(title,
                                                                     creator)
        else:
            name = title
        output.append(name)

        if backerCount is not None:
            output.append('Backers: {:,d}'.format(backerCount))

        if backerCount > 0:
            pledgePerBacker = pledged / backerCount
        else:
            pledgePerBacker = 0

        if percentage >= 100:
            percentageString = A.fg.green['({2:,.0f}% funded)']
        else:
            percentageString = A.fg.red['({2:,.0f}% funded)']

        pledgePerBackerString = A.fg.gray['{3:,.0f}/backer']

        pledgedString = assembleFormattedText(A.normal['Pledged: {0:,.0f}',
                                                       A.fg.gray['/'],
                                                       '{1:,.0f} {4} ',
                                                       percentageString,
                                                       ' ',
                                                       pledgePerBackerString])
        output.append(pledgedString.format(pledged,
                                           goal,
                                           percentage,
                                           pledgePerBacker,
                                           currency))

        output.append(campaignState)

        graySplitter = assembleFormattedText(A.normal[' ',
                                                      A.fg.gray['|'],
                                                      ' '])
        return graySplitter.join(output), shorturl


kickstarter = Kickstarter()
