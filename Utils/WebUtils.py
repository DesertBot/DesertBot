# -*- coding: utf-8 -*-

# somewhat hacky and I forget what this is solving
import socket

origGetAddrInfo = socket.getaddrinfo

def getAddrInfoWrapper(host, port, _=0, socktype=0, proto=0, flags=0):
    return origGetAddrInfo(host, port, socket.AF_INET, socktype, proto, flags)

socket.getaddrinfo = getAddrInfoWrapper

from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode

import requests
import json
import re
import time

from apiclient.discovery import build

from Data.api_keys import load_key


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
            self._body = self._response.content
            self._responseCloser()
        return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @body.deleter
    def body(self):
        del self._body


def fetchURL(url, extraHeaders=None):
    """
    @type url: unicode
    @type extraHeaders: list[tuple]
    @rtype: URLResponse
    """
    headers = {"User-agent", "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0"}
    if extraHeaders:
        headers.update(extraHeaders)
    try:
        response = requests.get(url, headers=headers, stream=True)
        responseHeaders = response.headers
        #print '{} headers: {}'.format(urlparse(response.geturl()).hostname, responseHeaders)
        pageType = responseHeaders["content-type"]

        # Make sure we don't download any unwanted things
        #              |   text|                       rss feeds and xml|                      json|
        if re.match(r"^(text/.*|application/((rss|atom|rdf)\+)?xml(;.*)?|application/(.*)json(;.*)?)$", pageType):
            urlResponse = URLResponse(response)
            return urlResponse

    except requests.exceptions.RequestException as e:
        today = time.strftime("[%H:%M:%S]")
        reason = str(e)
        print("{} *** ERROR: Fetch from \"{}\" failed: {}".format(today, url, reason))


# mostly taken directly from Heufneutje's PyHeufyBot
# https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L43
def postURL(url, values, extraHeaders=None):
    """
    @type url: unicode
    @type values: dict[unicode, T]
    @type extraHeaders: dict[unicode, unicode]
    @rtype: URLResponse
    """
    headers = {"User-agent": "Mozilla/5.0"}
    if extraHeaders:
        for header in extraHeaders:
            headers[header] = extraHeaders[header]

    # urlencode only take str objects, so encode our unicode values first
    for k, v in values.iteritems():
        values[k] = unicode(v).encode('utf-8')
    data = urlencode(values)

    try:
        request = Request(url, data, headers)
        response = urlopen(request)
        responseHeaders = response.info().dict
        pageType = responseHeaders["content-type"]

        # Make sure we don't download any unwanted things
        #              |   text|                       rss feeds and xml|                      json|
        if re.match(r"^(text/.*|application/((rss|atom|rdf)\+)?xml(;.*)?|application/(.*)json(;.*)?)$", pageType):
            urlResponse = URLResponse(response)
            return urlResponse
        else:
            response.close()

    except URLError as e:
        today = time.strftime("[%H:%M:%S]")
        reason = None
        if hasattr(e, "reason"):
            reason = "We failed to reach the server, reason: {}".format(e.reason)
        elif hasattr(e, "code"):
            reason = "The server couldn't fulfill the request, code: {}".format(e.code)
        print("{} *** ERROR: Post to \"{}\" failed: {}".format(today, url, reason))


def shortenGoogl(url):
    """
    @type url: unicode
    @rtype: unicode
    """
    post = '{{"longUrl": "{}"}}'.format(url)

    googlKey = load_key(u'goo.gl')

    if googlKey is None:
        return "[goo.gl API key not found]"

    apiURL = 'https://www.googleapis.com/urlshortener/v1/url?key={}'.format(googlKey)

    headers = {"Content-Type": "application/json"}

    try:
        request = Request(apiURL, post, headers)
        response = json.loads(urlopen(request).read())
        return response['id']

    except Exception as e:
        print("Goo.gl error: {}".format(e))


def googleSearch(query):
    """
    @type query: unicode
    @rtype: dict[unicode, T]
    """
    googleKey = load_key(u'Google')
    
    service = build('customsearch', 'v1', developerKey=googleKey)
    res = service.cse().list(
        q = query,
        cx = '002603151577378558984:xiv3qbttad0'
    ).execute()
    return res


# mostly taken directly from Heufneutje's PyHeufyBot
# https://github.com/Heufneutje/PyHeufyBot/blob/eb10b5218cd6b9247998d8795d93b8cd0af45024/pyheufybot/utils/webutils.py#L74
def pasteEE(data, description, expire, raw=True):
    """
    @type data: unicode
    @type description: unicode
    @type expire: int
    @type raw: bool
    @rtype: unicode
    """
    values = {u"key": u"public",
              u"description": description,
              u"paste": data,
              u"expiration": expire,
              u"format": u"json"}
    result = postURL(u"http://paste.ee/api", values)
    if result:
        jsonResult = json.loads(result.body)
        if jsonResult["status"] == "success":
            linkType = "raw" if raw else "link"
            return jsonResult["paste"][linkType]
        elif jsonResult["status"] == "error":
            return u"An error occurred while posting to Paste.ee, code: {}, reason: {}"\
                .format(jsonResult["errorcode"], jsonResult["error"])
