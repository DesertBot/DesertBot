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
    # just hardcode a limit on max messages for now, should limit comic size pretty effecively?
    messageLimit = 8

    def actions(self):
        # define additional actions so all PRIVMSGs and ACTIONs in the channel get handled by storeMessage
        return super(Comic, self).actions() + [("message-channel", 1, self.storeMessage),
                                               ("action-channel", 1, self.storeMessage)]

    def onLoad(self) -> None:
        # messages need to be stored for comics to work, store in a list as (nick, message)
        self.messageStore = []

    def triggers(self):
        return ['comic']

    def help(self, query):
        return 'comic - make a comic'

    def execute(self, message: IRCMessage):
        if len(self.messageStore) != 0:
            comic = self.make_comic(self.messageStore)
            return IRCResponse(ResponseType.Say, self.post_comic(comic), message.replyTo)

    def storeMessage(self, message: IRCMessage):
        """
        Store the message into the messageStore, and prune it to the limit if needed
        """
        # TODO just store the IRCMessage objects, so we can use other things than just the nick and message string
        self.messageStore.append((message.user.nick, message.messageString))
        if len(self.messageStore) > self.messageLimit:
            self.messageStore.pop(0)    # remove the first (oldest) message in the list if we're now above the limit

    def make_comic(self, messages):
        # chars is a set of the "characters" involved, at this point these are message.user.nick
        chars = set()
        # panels is a list of comic "panels", each involving 1-2 "characters", each with a message spoken
        panels = []

        # one "panel" is a list of the (message.user.nick, message.messageString) pairs to be drawn in that panel
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

        # Randomly associate a character image to each user
        filenames = glob.glob('data/comics/chars/*')
        shuffle(filenames)
        charmap = {}
        # by using zip() with a shuffled list of filenames rather than populating with random.choice()
        # it should be impossible for two "chars" to be assigned the same image
        for ch, f in zip(chars, filenames):
            charmap[ch] = Image.open(f)

        # charmap is now a dict of message.user.nick to their randomly picked "character" image

        imgwidth = panelwidth
        imgheight = panelheight * len(panels)

        # this will be the background image for each separate panel
        background = Image.open('data/comics/backgrounds/beach-paradise-beach-desktop.jpg')

        # comicImage is our entire comic, to be filled with our panels
        comicImage = Image.new("RGBA", (imgwidth, imgheight), (0xff, 0xff, 0xff, 0xff))
        font = ImageFont.truetype('data/comics/fonts/ComicRelief.ttf', 14)

        for i, panel in enumerate(panels):
            # for each panel, create an Image object
            panelImage = Image.new("RGBA", (panelwidth, panelheight), (0xff, 0xff, 0xff, 0xff))

            # paste the bg image into our panel Image
            panelImage.paste(background, (0, 0))
            draw = ImageDraw.Draw(panelImage)

            string1width = 0
            string1height = 0
            string2width = 0
            string2height = 0

            # call the wrap function to get a formatted string to be drawn onto the image
            # use 2/3rds panel width as the "max width" for the text
            (string1, (string1width, string1height)) = self.wrap(panel[0][1], font, draw, 2*panelwidth/3.0)
            # then draw that string onto the image at 10 from the top, 10 from the left edge
            self.rendertext(string1, font, draw, (10, 10))

            if len(panel) == 2:
                # if there is a second message in this panel, draw it differently from the first
                # call the wrap function again to get the second string (again with 2/3rds panel width as "max width")
                (string2, (string2width, string2height)) = self.wrap(panel[1][1], font, draw, 2 * panelwidth / 3.0)
                # then draw that string onto the image as close to the right edge as it can fit, 10 below the 1st string
                self.rendertext(string2, font, draw,
                                (panelwidth - 10 - string2width, string1height + 10))

            # calculate the "height" of the text, with some spacing (used for scaling character images?)
            text_height = string1height + 10
            if string2height > 0:
                text_height += string2height + 10 + 5

            # scale the character image for the 1st message and paste it into the panel Image object
            maxch = panelheight - text_height
            char1image = self.fitimg(charmap[panel[0][0]], 2*panelwidth/5.0-10, maxch)
            panelImage.paste(char1image, (10, panelheight-char1image.size[1]), char1image)

            # if there is a second character, also scale and paste that into the panel Image object
            if len(panel) == 2:
                char2image = self.fitimg(charmap[panel[1][0]], 2*panelwidth/5.0-10, maxch)
                char2image = char2image.transpose(Image.FLIP_LEFT_RIGHT)    # flip the character image, so it "faces" the first character image
                panelImage.paste(char2image, (panelwidth-char2image.size[0]-10, panelheight-char2image.size[1]), char2image)

            # draw a small black line at the top? of the panel Image
            draw.line([(0, 0), (0, panelheight-1), (panelwidth-1, panelheight-1), (panelwidth-1, 0), (0, 0)], (0, 0, 0, 0xff))
            del draw

            # paste the panel Image object onto our comic Image object, using the index i to offset height
            comicImage.paste(panelImage, (0, panelheight * i))

        comicByteArray = BytesIO()
        comicImage.save(comicByteArray, format="PNG", quality=85)
        return comicByteArray.getvalue()

    def post_comic(self, comicObject):
        apiUrl = 'https://dbco.link/'
        postData = {'c': ('comic.png', comicObject, 'application/octet-stream')}
        headers = {'Accept': 'application/json'}

        try:
            response = requests.post(apiUrl, files=postData, headers=headers)
            responseJson = response.json()
            return responseJson['url']
        except requests.exceptions.RequestException:
            self.logger.exception("dbco.link POST url error {}"
                                  .format(comicObject))
        except json.decoder.JSONDecodeError:
            self.logger.exception("dbco.link json response decode error, {} (at {})"
                                  .format(response.content, comicObject))

    def wrap(self, messageString, font, draw, maxWidth):
        """
        This function does Weird Shit to wrap/format the string so that it fits in the given width (pixels?)
        It uses the given "draw" object to do this - ImageDraw.Draw()
        """
        messageString = messageString.split()
        wrappedWidth = 0
        wrappedHeight = 0
        ret = []

        while len(messageString) > 0:
            s = 1
            while True and s < len(messageString):
                w, h = draw.textsize(" ".join(messageString[:s]), font=font)
                if w > maxWidth:
                    s -= 1
                    break
                else:
                    s += 1

            if s == 0 and len(messageString) > 0:  # we've hit a case where the current line is wider than the screen
                s = 1

            w, h = draw.textsize(" ".join(messageString[:s]), font=font)
            wrappedWidth = max(wrappedWidth, w)
            wrappedHeight += h
            ret.append(" ".join(messageString[:s]))
            messageString = messageString[s:]

        return ret, (wrappedWidth, wrappedHeight)

    def rendertext(self, messageString, font, draw, position):
        """
        This function renders the given messageString at the given position in the given "draw" object - ImageDraw.Draw()
        """
        ch = position[1]
        for s in messageString:
            w, h = draw.textsize(s, font=font)
            draw.text((position[0], ch), s, font=font, fill=(0xff, 0xff, 0xff, 0xff))
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
