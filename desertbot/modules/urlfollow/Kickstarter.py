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

        if state == 'live':
            data = soup.find(attrs={'data-initial': True})
            if data is not None:
                data = json.loads(data['data-initial'])
                data = data['project']

                shorturl = data['projectShortLink']

                title = data['name']
                creator = data['creator']['name']

                backerCount = int(data['backersCount'])

                pledged = float(data['pledged']['amount'])
                goal = float(data['goal']['amount'])
                currency = data['goal']['currency']
                percentage = float(data['percentFunded'])

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
                return '[Kickstarter changed their page structure again :S]'
        else:
            shorturl = soup.find(rel='shorturl')['href']
            if shorturl is None:
                shorturl = 'https://www.kickstarter.com/projects/{}/'.format(ksID)

            title = soup.find(property='og:title')
            if title is not None:
                title = title['content'].strip()
                # live projects
                creator = soup.find(attrs={'data-modal-class': 'modal_project_by'})
                # completed projects
                if creator is None or not creator.text:
                    creator = soup.find(class_='green-dark',
                                        attrs={'data-modal-class': 'modal_project_by'})
                if creator is not None:
                    creator = creator.text.strip()

            stats = soup.find(id='stats')
            # projects in progress
            if stats is not None:
                backerCount = soup.find(id='backers_count')
                if backerCount is not None:
                    backerCount = int(backerCount['data-backers-count'])
            # completed projects
            else:
                backerCount = soup.find(class_='NS_campaigns__spotlight_stats')
                if backerCount is not None:
                    backerCount = int(backerCount.b.text.strip().split()[0].replace(',', ''))

            if stats is not None:
                pledgeData = soup.find(id='pledged')
                if pledgeData is not None:
                    pledged = float(pledgeData['data-pledged'])
                    goal = float(pledgeData['data-goal'])
                    percentage = float(pledgeData['data-percent-raised'])
                    percentage = int(percentage * 100)
            else:
                money = soup.select('span.money')
                if money:
                    pledgedString = money[1].text.strip()
                    goalString = money[2].text.strip()
                    pledged = float(re.sub(r'[^0-9.]', u'', pledgedString))
                    goal = float(re.sub(r'[^0-9.]', u'', goalString))
                    percentage = (pledged / goal)
            currency = ""

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
