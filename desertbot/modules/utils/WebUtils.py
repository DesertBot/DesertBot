"""
Created on Mar 5, 2018

@author: StarlitGhost
"""
import html
import ipaddress
import json
import re
import socket
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from apiclient.discovery import build
from bs4 import BeautifulSoup
from requests import Response
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.moduleinterface import IModule, BotModule


@implementer(IPlugin, IModule)
class WebUtils(BotModule):
    def actions(self):
        return super(WebUtils, self).actions() + [('is-public-url', 1, self.isPublicURL),
                                                  ('fetch-url', 1, self.fetchURL),
                                                  ('post-url', 1, self.postURL),
                                                  ('get-html-title', 1, self.getPageTitle),
                                                  ('shorten-url', 1, self.shortenURL),
                                                  ('search-web', 1, self.googleSearch),
                                                  ('upload-pasteee', 1, self.pasteEE),
                                                  ('upload-dbco', 1, self.pasteDBCO)]

    def onLoad(self):
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/88.0"
        self.accept = ("text/*, "
                       "application/xml, application/xhtml+xml, "
                       "application/rss+xml, application/atom+xml, application/rdf+xml, "
                       "application/json")
        self.lang = "en-US"

    def isPublicURL(self, url: str) -> bool:
        parsed = urlparse(url)
        host = socket.gethostbyname(parsed.hostname)
        ip = ipaddress.ip_address(host)
        return ip.is_global

    def fetchURL(self, url: str,
                 params: Any=None,
                 extraHeaders: Optional[Dict[str, str]]=None,
                 handleErrors: bool=True) -> Optional[Response]:
        # check the requested url is public
        if not self.isPublicURL(url):
            self.logger.info(f'non-public url {url} ignored')
            return

        headers = {
            "User-agent": self.ua, 
            "Accept": self.accept, 
            "Accept-Language": self.lang,
            "Cache-Control": "no-cache"
        }
        # Make sure we don't download any unwanted things
        check = (r"^("
                 r"text/.*|"  # text
                 r"application/((rss|atom|rdf)\+)?xml(;.*)?|"  # rss/xml
                 r"application/(.*)json(;.*)?"  # json
                 r")$")
        check = re.compile(check)
        if extraHeaders:
            headers.update(extraHeaders)
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if 'content-type' in response.headers:
                pageType = response.headers["content-type"]
            else:
                pageType = 'text/nothing'

            if check.match(pageType):
                return response
            else:
                response.close()

        except requests.exceptions.RequestException as e:
            self.logger.exception("GET from {!r} failed!".format(url))
            if not handleErrors:
                raise e

    # mostly taken directly from Heufneutje's PyHeufyBot
    # https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L43
    def postURL(self, url: str,
                data: Any=None,
                json: Any=None,
                extraHeaders: Optional[Dict[str, str]]=None) -> Optional[Response]:
        # check the requested url is public
        if not self.isPublicURL(url):
            self.logger.info(f'non-public url {url} ignored')
            return

        headers = {"User-agent": self.ua, "Accept": self.accept}
        if extraHeaders:
            headers.update(extraHeaders)

        try:
            response = requests.post(url, data=data, json=json, headers=headers, timeout=10)

            return response

        except requests.exceptions.RequestException:
            self.logger.exception("POST to {!r} failed!".format(url))

    def getPageTitle(self, webpage: str) -> Optional[str]:
        def cleanTitle(title: str) -> str:
            title = re.sub('[\r\n]+', '', title)  # strip any newlines
            title = title.strip()  # strip all whitespace either side
            title = ' '.join(title.split())  # replace multiple whitespace with single space
            title = html.unescape(title)  # unescape html entities

            # Split on the first space before 300 characters, and replace the rest with '...'
            if len(title) > 300:
                title = title[:300].rsplit(' ', 1)[0] + " ..."

            return title

        soup = BeautifulSoup(webpage, 'lxml')
        # look for an h1 inside an article tag first, this should be the actual title on the page
        article = soup.find('article')
        if article:
            title = article.find('h1')
            if title:
                return cleanTitle(title.text)
        # look for a meta title next, it will probably be more relevant if there is one
        title = soup.find('meta', {'property': 'og:title'})
        if title:
            return cleanTitle(title['content'])
        # fall back to the html title tag
        title = soup.title
        if title:
            return cleanTitle(title.text)

        return

    def shortenURL(self, url: str) -> str:
        apiURL = 'https://dbco.link/u'
        post = {'content': url}
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}

        try:
            response = requests.post(apiURL, json=post, headers=headers)
            responseJson = response.json()
            return responseJson['url']
        except requests.exceptions.RequestException:
            self.logger.exception("dbco.link POST url error {}".format(url))
            return url
        except json.decoder.JSONDecodeError:
            self.logger.exception("dbco.link json response decode error, {} (at {})".format(response.content, url))
            return url

    def googleSearch(self, query: str) -> Optional[Dict[str, Any]]:
        googleKey = self.bot.moduleHandler.runActionUntilValue('get-api-key', 'Google')
        if not googleKey:
            return None

        service = build('customsearch', 'v1', developerKey=googleKey)
        res = service.cse().list(
            q=query,
            cx='002603151577378558984:xiv3qbttad0'
        ).execute()
        return res

    # mostly taken directly from Heufneutje's PyHeufyBot
    # https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L74
    def pasteEE(self, data: str, description: str="", expire: int=None, raw: bool=True) -> str:
        # pasteEEKey = load_key('Paste.ee') (Heufneutje, 2018-4-27): Unused?

        values = {"key": "public",
                  "description": description,
                  "paste": data,
                  "expiration": expire,
                  "format": "json"}
        result = self.postURL("http://paste.ee/api", values)
        if result:
            jsonResult = result.json()
            if jsonResult["status"] == "success":
                linkType = "raw" if raw else "link"
                return jsonResult["paste"][linkType]
            elif jsonResult["status"] == "error":
                return ("An error occurred while posting to Paste.ee, code: {}, reason: {}"
                        .format(jsonResult["errorcode"], jsonResult["error"]))

    def pasteDBCO(self, data: str, expire: int=0, vanity: str=None) -> str:
        apiURL = 'https://dbco.link/'
        post = {"content": data,
                "sunset": expire}
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        if vanity:
            apiURL += f"~{vanity}"

        try:
            response = requests.post(apiURL, json=post, headers=headers)
            responseJson = response.json()
            return responseJson['url']
        except requests.exceptions.RequestException:
            self.logger.exception("dbco.link POST paste error {}"
                                  .format(data))
        except json.decoder.JSONDecodeError:
            self.logger.exception("dbco.link json response decode error, {} (at {})"
                                  .format(response.content, data))


web = WebUtils()
