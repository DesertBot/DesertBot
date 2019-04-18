"""
Created on Apr 18, 2019

@author: lunik1
"""
from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
from zope.interface import implementer

import base64
import requests
import json
import glob
from PIL import Image, ImageDraw, ImageFont
from random import shuffle
from io import BytesIO

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Comic(BotCommand):
    def triggers(self):
        return ['comic']

    def help(self, query):
        return 'comic - make a comic'

    def execute(self, message: IRCMessage):
        messages = self.get_messages()
        comic = self.make_comic(messages)
        return IRCResponse(ResponseType.Say, self.comic(comic), message.replyTo)

    def get_messages(self):
        return [('U1', 'Message 1'), ('U2', 'Message 2'), ('U1', 'Message 3'), ('U3', 'Message 4')]

    def make_comic(self, messages):
        chars = set()
        panels = []

        panel = []
        last_char = None
        for message in messages:
            char = message[0]
            chars.add(char)

            # Start a new panel if the panel is full or the same user speaks twice in a row
            if len(panel) == 2 or len(panel) == 1 and char == last_char:
                panels.append(panel)
                panel = []

            panel.append(message)
            last_char = char
        panels.append(panel)

        panelheight = 300
        panelwidth = 450

        # Randomly associate a charachter to each user
        filenames = glob.glob('data/comics/chars/*')
        shuffle(filenames)
        charmap = {}
        for ch, f in zip(chars, filenames):
            charmap[ch] = Image.open(f)

        imgwidth = panelwidth
        imgheight = panelheight * len(panels)

        bg = Image.open('data/comics/backgrounds/beach-paradise-beach-desktop.jpg')

        im = Image.new("RGBA", (imgwidth, imgheight), (0xff, 0xff, 0xff, 0xff))
        font = ImageFont.truetype('data/comics/fonts/ComicRelief.ttf', 14)

        for i, panel in enumerate(panels):
            pim = Image.new("RGBA", (panelwidth, panelheight), (0xff, 0xff, 0xff, 0xff))
            pim.paste(bg, (0, 0))
            draw = ImageDraw.Draw(pim)

            st1w = 0
            st1h = 0
            st2w = 0
            st2h = 0
            (st1, (st1w, st1h)) = self.wrap(panel[0][1], font, draw, 2*panelwidth/3.0)
            self.rendertext(st1, font, draw, (10, 10))
            if len(panel) == 2:
                (st2, (st2w, st2h)) = self.wrap(panel[1][1], font, draw, 2 * panelwidth / 3.0)
                self.rendertext(st2, font, draw,
                                (panelwidth - 10 - st2w, st1h + 10))
            texth = st1h + 10
            if st2h > 0:
                texth += st2h + 10 + 5

            maxch = panelheight - texth
            im1 = self.fitimg(charmap[panel[0][0]], 2*panelwidth/5.0-10, maxch)
            pim.paste(im1, (10, panelheight-im1.size[1]), im1)

            if len(panel) == 2:
                im2 = self.fitimg(charmap[panel[1][0]], 2*panelwidth/5.0-10, maxch)
                im2 = im2.transpose(Image.FLIP_LEFT_RIGHT)
                pim.paste(im2, (panelwidth-im2.size[0]-10, panelheight-im2.size[1]), im2)

            draw.line([(0, 0), (0, panelheight-1), (panelwidth-1, panelheight-1), (panelwidth-1, 0), (0, 0)], (0, 0, 0, 0xff))
            del draw
            im.paste(pim, (0, panelheight * i))

        comic_bytearray = BytesIO()
        im.save(comic_bytearray, format="PNG", quality=85)
        return comic_bytearray.getvalue()

    def comic(self, comic):
        api_url = 'https://dbco.link/'
        post = {'c': ('comic.png', comic, 'application/octet-stream')}
        headers = {'Accept': 'application/json'}

        try:
            response = requests.post(api_url, files=post, headers=headers)
            p = requests.Request('POST', api_url, files=post).prepare()
            response_json = response.json()
            return response_json['url']
        except requests.exceptions.RequestException:
            self.logger.exception("dbco.link POST url error {}"
                                  .format(comic))
        except json.decoder.JSONDecodeError:
            self.logger.exception("dbco.link json response decode error, {} (at {})"
                                  .format(response.content, comic))

    def wrap(self, st, font, draw, width):
        st = st.split()
        mw = 0
        mh = 0
        ret = []

        while len(st) > 0:
            s = 1
            while True and s < len(st):
                w, h = draw.textsize(" ".join(st[:s]), font=font)
                if w > width:
                    s -= 1
                    break
                else:
                    s += 1

            if s == 0 and len(st) > 0:  # we've hit a case where the current line is wider than the screen
                s = 1

            w, h = draw.textsize(" ".join(st[:s]), font=font)
            mw = max(mw, w)
            mh += h
            ret.append(" ".join(st[:s]))
            st = st[s:]

        return ret, (mw, mh)

    def rendertext(self, st, font, draw, pos):
        ch = pos[1]
        for s in st:
            w, h = draw.textsize(s, font=font)
            draw.text((pos[0], ch), s, font=font, fill=(0xff, 0xff, 0xff, 0xff))
            ch += h

    def fitimg(self, img, width, height):
        scale1 = float(width) / img.size[0]
        scale2 = float(height) / img.size[1]

        l1 = (img.size[0] * scale1, img.size[1] * scale1)
        l2 = (img.size[0] * scale2, img.size[1] * scale2)

        if l1[0] > width or l1[1] > height:
            l = l2
        else:
            l = l1

        return img.resize((int(l[0]), int(l[1])), Image.ANTIALIAS)

comic = Comic()
