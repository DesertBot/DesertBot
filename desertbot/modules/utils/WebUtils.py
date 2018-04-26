# -*- coding: utf-8 -*-
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

import requests
import json
import re

from builtins import str
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse
from typing import Any, Dict, Optional

from apiclient.discovery import build

from desertbot.utils.api_keys import load_key


class URLResponse(object):
    def __init__(self, response):
        self.domain = urlparse(response.url).netloc
        self._body = None
        self._response = response
        self._responseCloser = response.close
        self.headers = response.headers
        self.responseUrl = response.url

    def __del__(self):
        if self._body is None:
            self._responseCloser()

    @property
    def body(self):
        if self._body is None:
            self._body = self._response.content.decode('utf-8', 'ignore')
            self._responseCloser()
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @body.deleter
    def body(self):
        del self._body


@implementer(IPlugin, IModule)
class WebUtils(BotModule):
    def actions(self):
        return super(WebUtils, self).actions() + [('fetch-url', 1, self.fetchURL),
                                                  ('post-url', 1, self.postURL),
                                                  ('shorten-url', 1, self.shortenGoogl),
                                                  ('search-web', 1, self.googleSearch),
                                                  ('upload-pasteee', 1, self.pasteEE)]

    def fetchURL(self, url: str, params: Any=None, extraHeaders: Optional[Dict[str, str]]=None) -> URLResponse:
        headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
            "Accept": "text/*, "
                      "application/xml, application/xhtml+xml, "
                      "application/rss+xml, application/atom+xml, application/rdf+xml, "
                      "application/json"
        }
        if extraHeaders:
            headers.update(extraHeaders)
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            responseHeaders = response.headers
            pageType = responseHeaders["content-type"]

            # Make sure we don't download any unwanted things
            #              |   text|                       rss feeds and xml|                      json|
            if re.match(r"^(text/.*|application/((rss|atom|rdf)\+)?xml(;.*)?|application/(.*)json(;.*)?)$", pageType):
                urlResponse = URLResponse(response)
                return urlResponse
            else:
                response.close()

        except requests.exceptions.RequestException:
            self.logger.exception("GET from {!r} failed!".format(url))

    # mostly taken directly from Heufneutje's PyHeufyBot
    # https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L43
    def postURL(self, url: str, data: Any=None, json: Any=None, extraHeaders: Optional[Dict[str, str]]=None) -> URLResponse:
        headers = {"User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
                   "Accept": "text/*, "
                             "application/xml, application/xhtml+xml, "
                             "application/rss+xml, application/atom+xml, application/rdf+xml, "
                             "application/json"
        }
        if extraHeaders:
            headers.update(extraHeaders)

        try:
            response = requests.post(url, data=data, json=json, headers=headers, timeout=10)

            urlResponse = URLResponse(response)
            return urlResponse

        except requests.exceptions.RequestException:
            self.logger.exception("POST to {!r} failed!".format(url))

    def shortenGoogl(self, url: str) -> str:
        post = {"longUrl": url}

        googlKey = load_key(u'goo.gl')

        if googlKey is None:
            return "[goo.gl API key not found]"

        apiURL = 'https://www.googleapis.com/urlshortener/v1/url?key={}'.format(googlKey)

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(apiURL, json=post, headers=headers)
            responseJson = response.json()
            if 'error' in responseJson:
                return '[Googl Error: {} {}]'.format(responseJson['error']['message'], post['longUrl'])
            return responseJson['id']

        except requests.exceptions.RequestException:
            self.logger.exception("Goo.gl error")

    def googleSearch(self, query: str) -> Optional[Dict[str, Any]]:
        googleKey = load_key(u'Google')
        if not googleKey:
            return None

        service = build('customsearch', 'v1', developerKey=googleKey)
        res = service.cse().list(
            q = query,
            cx = '002603151577378558984:xiv3qbttad0'
        ).execute()
        return res

    # mostly taken directly from Heufneutje's PyHeufyBot
    # https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L74
    def pasteEE(self, data: str, description: str, expire: int, raw: bool=True) -> str:
        # pasteEEKey = load_key(u'Paste.ee') (Heufneutje, 2018-4-27): Unused?

        values = {u"key": "public",
                  u"description": description,
                  u"paste": data,
                  u"expiration": expire,
                  u"format": u"json"}
        result = self.postURL(u"http://paste.ee/api", values)
        if result:
            jsonResult = json.loads(result.body)
            if jsonResult["status"] == "success":
                linkType = "raw" if raw else "link"
                return jsonResult["paste"][linkType]
            elif jsonResult["status"] == "error":
                return u"An error occurred while posting to Paste.ee, code: {}, reason: {}"\
                    .format(jsonResult["errorcode"], jsonResult["error"])


web = WebUtils()
