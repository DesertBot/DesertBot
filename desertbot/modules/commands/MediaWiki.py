"""
@date: 2021-02-06
@author: HelleDaryd
"""
from twisted.plugin import IPlugin
from twisted.words.protocols.irc import assembleFormattedText as colour, attributes as A
from zope.interface import implementer

from bs4 import BeautifulSoup
from furl import furl
from json import JSONDecodeError
import regex

import mediawiki as mw
from mediawiki.exceptions import MediaWikiAPIURLError, MediaWikiBaseException
from mediawiki.exceptions import PageError, DisambiguationError

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from desertbot.response import IRCResponse

USER_AGENT = 'DesertBot'
STRIP_PARENTHESIS = regex.compile(r"(\((?:[^()]++|(?1))*\))")
SEARCH_RETURNED_RESULTS = 12
SUMMARY_LENGTH = 350


def _strip_parenthesis(string):
    return STRIP_PARENTHESIS.sub("", string)


class URIError(ValueError):
    pass


@implementer(IPlugin, IModule)
class MediaWiki(BotCommand):
    wikihandlers = {}

    # We explicitely implement the wiki alias for en.wikipedia.org, so it has a
    # help, etc which it would lack if it was handled only via .alias
    def triggers(self):
        return ["mediawiki", "wiki"]

    def actions(self):
        return super(MediaWiki, self).actions() + [('wikipedia', 1, self.wikipedia)]

    def onLoad(self):
        self.wikihandlers["en.wikipedia.org"] = mw.MediaWiki(user_agent=USER_AGENT)

    def help(self, query):
        """
        Media command syntax:
        .mediawiki <wiki> <term>
        .mediawiki <wiki> search <term>
        .mediawiki <wiki> random
        .wiki <term>
        .wiki search <term>
        .wiki random
        """
        cchar = self.bot.commandChar
        help_dict = {
            "wiki": {
                "search": f"{cchar} wiki search <term> - Search Wikipedia for the term given, returning the list of results",
                "random": f"{cchar} wiki random - Return a random page from Wikipedia",
                "<term>": f"{cchar} wiki <term> - Attempt to find the term on Wikipedia, or give the closest search results",
                None: f"{cchar} wiki <term>/search/random - Find information on the English language Wikipedia."
                      f" Use {cchar}help wiki <subcommand> for more help"
            },
            "mediawiki": {
                "search": f"{cchar} mediawiki <wiki> search <term> - Search the wiki <wiki> for the term given, returning the list of results",
                "random": f"{cchar} mediawiki <wiki> random - Return a random page from the wiki <wiki>",
                "<term>": f"{cchar} mediawiki <wiki> <term> - Attempt to find the term on the wiki <wiki>, or give the closest search results",
                None: f"{cchar} mediawiki <wiki> <term>/search/random - Find information on the any MediaWiki site with the API enabled."
                      f" <wiki> is the hostname or base URL for the wiki you want to query."
                      f" Use {cchar}help mediawiki <subcommand> for more help."
            }
        }
        if len(query) == 1:
            return help_dict[query[0]][None]
        else:
            if query[1].lower() in help_dict[query[0]]:
                return help_dict[query[0]][query[1].lower()]
            else:
                return f"{query[1]} is not a valid subcommand, use {cchar}help {query[0]} for a list of subcommands"

    def execute(self, message: IRCMessage):
        try:
            if message.command == "wiki":
                wiki = "en.wikipedia.org"
            else:
                wiki = message.parameterList.pop(0)

            response = None
            if len(message.parameterList) >= 1:
                if message.parameterList[0] == "random":
                    response = self.random(wiki=wiki)
                elif message.parameterList[0] == "search" and len(message.parameterList) > 1:
                    response = self.search(wiki=wiki, query=message.parameterList[1:])
                else:
                    response = self.divine_results(wiki=wiki, query=message.parameterList[0:])

            if response:
                return IRCResponse(response, message.replyTo)
            return False

        except URIError:
            return IRCResponse("Not a valid MediaWiki URL specified", message.replyTo)
        except (MediaWikiAPIURLError, JSONDecodeError, ConnectionError):
            return IRCResponse("Not a valid MediaWiki API at the URL specified", message.replyTo)
        except MediaWikiBaseException as error:
            return IRCResponse("MediaWiki query failed with {}".format(error), message.replyTo)

    def wikipedia(self, title):
        wiki = self.wikihandlers["en.wikipedia.org"]

        try:
            page = wiki.page(title, preload=False, auto_suggest=False, redirect=True)
            return self._format_page(wiki, page, link=False)
        except DisambiguationError as disambiguation:
            return self._format_disambiguation(wiki, disambiguation, link=False)
        except PageError:
            return

    def random(self, *, wiki):
        wiki = self._get_or_create_wiki_handler(wiki)
        return self._format_page(wiki, wiki.page(wiki.random(pages=1)))

    def search(self, *, wiki, query):
        wiki = self._get_or_create_wiki_handler(wiki)
        query = " ".join(query)
        search = wiki.search(query, results=SEARCH_RETURNED_RESULTS * 2)
        if search:
            return self._format_search(wiki, search)
        else:
            return self._format_wiki(wiki) + "No pages found"

    # The logic for chosing what result to give is complex
    # Try it as an actual page, then a suggestion, then a search result
    # If it is a disambiguation page, avoid it and proceed to the next
    # level of checking. Hence, divination
    def divine_results(self, *, wiki, query):
        wiki = self._get_or_create_wiki_handler(wiki)
        query = " ".join(query)

        try:
            page = wiki.page(query, preload=False, auto_suggest=False, redirect=True)
            return self._format_page(wiki, page)
        except PageError:
            disambiguation = False
        except DisambiguationError:
            disambiguation = True


        search = wiki.search(query, results=SEARCH_RETURNED_RESULTS * 2)

        if disambiguation:
            search = [item for item in search if item.lower() != query.lower()]
        if not search:
            return self._format_wiki(wiki) + "No pages found"
        elif len(search) == 1:
            try:
                page = wiki.page(search[0], preload=False, auto_suggest=False, redirect=True)
                return self._format_page(wiki, page)
            except DisambiguationError as disambiguation:
                return self._format_search(wiki, disambiguation.options)

        return self._format_search(wiki, search)

    def _get_or_create_wiki_handler(self, uri_string):
        try:
            url = furl(uri_string)
        except ValueError:
            raise URIError("Cannot make sense of this URL")

        if not url.netloc and url.path:
            url.netloc = str(url.path)
            url.path.set('')

        if url.netloc in self.wikihandlers:
            return self.wikihandlers[url.netloc]

        if not url.scheme:
            url.scheme = 'https'

        if url.scheme != 'https' and url.scheme != 'http':
            raise URIError("Bad scheme given")

        if not self.bot.moduleHandler.runActionUntilValue("is-public-url", str(url)):
            raise URIError("Not a public URL")

        # API can either be under /api.php or /w/api.php
        url.path.add("api.php")

        try:
            self.wikihandlers[url.netloc] = mw.MediaWiki(url=str(url))
        except (MediaWikiAPIURLError, JSONDecodeError):
            url.path.segments.insert(0, "w")
            self.wikihandlers[url.netloc] = mw.MediaWiki(url=str(url))

        return self.wikihandlers[url.netloc]

    def _format_page(self, wiki, page, link=True):
        title = page.title

        # We need to clean up the summary a bit to make it more useful on IRC
        # parenthesis get removed to get rid of pronounciation, etc, then clean
        # up some oddities that this leaves behind and just quirks and limit
        # length. Also handle cases where summary or text extensions are not
        # installed.
        summary = page.summarize(chars=SUMMARY_LENGTH * 2)
        if not summary:
            try:
                summary = page.content
            except MediaWikiBaseException:
                pass

        if not summary:
            soup = BeautifulSoup(page.html, 'lxml')
            for tag in soup.find_all(class_=["toc", "infobox", regex.compile("^mw-")]):
                tag.clear()
            summary = soup.get_text()

        if not summary:
            summary = ""

        summary_length = len(summary)
        summary = _strip_parenthesis(summary)
        summary = summary.replace("\n", " ")
        summary = regex.sub("\s+", " ", summary)
        summary = summary.replace(" ,", ",")
        summary = summary[0:SUMMARY_LENGTH].rstrip(" ,")
        summary = summary.strip()

        if len(summary) < summary_length:
            summary += "..."

        response = self._format_wiki(wiki)

        if title.lower() in summary.lower():
            title_pos = summary.lower().index(title.lower())
            response += summary[0:title_pos]
            response += colour(A.normal[A.bold[summary[title_pos:title_pos + len(title)]], ""])
            response += summary[title_pos + len(title):]
        else:
            response += colour(A.normal[A.bold[f"{title}"], f": {summary}"])

        if link:
            response += " - " + self.bot.moduleHandler.runActionUntilValue("shorten-url", page.url)
        return response

    def _format_disambiguation(self, wiki, disambiguation, link=False):
        response = self._format_wiki(wiki)
        response += colour(A.normal[A.bold[disambiguation.title], ": "])
        response += "; ".join(disambiguation.options[0:SEARCH_RETURNED_RESULTS])
        if len(disambiguation.options) > SEARCH_RETURNED_RESULTS:
            response += " and others"

        if link:
            response += " - " + self.bot.moduleHandler.runActionUntilValue("shorten-url", disambiguation.url)

        return response

    def _format_search(self, wiki, results):
        response = self._format_wiki(wiki)

        response += "Search results: "
        response += "; ".join(results[0:SEARCH_RETURNED_RESULTS])

        if len(results) > (SEARCH_RETURNED_RESULTS * 2 - 2):
            response += " and many more"
        elif len(results) > (SEARCH_RETURNED_RESULTS):
            response += " and some others"

        return response

    def _format_wiki(self, wiki):
        name = furl(wiki.base_url).netloc
        if name == "en.wikipedia.org":
            name = "Wikipedia"
        return colour(A.normal[A.fg.gray[A.bold["[", A.fg.white[f"{name}"], "]"]], A.normal[" "]])


mediawiki = MediaWiki()
