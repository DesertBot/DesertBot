"""
Created on Apr 18, 2019

@author: lunik1
"""
import glob
import json
from io import BytesIO
from random import sample

import requests
from PIL import Image, ImageDraw, ImageFont
from twisted.plugin import IPlugin
from zope.interface import implementer

from desertbot.message import IRCMessage
from desertbot.moduleinterface import IModule
from desertbot.modules.commandinterface import BotCommand
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
        # keys are channel names, as each channel kinda should have its own messages
        self.messageStore = {}

    def triggers(self):
        return ['comic']

    def help(self, query):
        return 'comic - make a comic'

    def execute(self, message: IRCMessage):
        messages = self.getMessages(message.replyTo)
        if len(messages) != 0:
            comic = self.makeComic(messages)
            return IRCResponse(ResponseType.Say, self.post_comic(comic), message.replyTo)

    def getMessages(self, channel: str):
        """
        Get the messages for the given channel
        Returns [] if there are no messages for that channel yet
        """
        return self.messageStore.get(channel, [])

    def storeMessage(self, message: IRCMessage):
        """
        Store the message into the messageStore, and prune it to the limit if needed
        """
        # TODO just store the IRCMessage objects, so we can use other things than just the nick and message string
        if message.command.lower() == "comic":
            # don't store the command that triggers a comic to be made
            return

        # fetch the message list for the channel this message belongs to and append the message data
        messages = self.getMessages(message.replyTo)
        if message.type == "ACTION":
            messages.append((message.user.nick, "*{}*".format(message.messageString)))
        else:
            messages.append((message.user.nick, message.messageString))

        if len(messages) > self.messageLimit:
            messages.pop(0)     # remove the first (oldest) message in the list if we're now above the limit

        # store the new message list into the messageStore
        self.messageStore[message.replyTo] = messages

    def post_comic(self, comicObject):
        apiUrl = 'https://dbco.link/'
        postData = {'c': ('comic.png', comicObject, 'application/octet-stream')}
        headers = {'Accept': 'application/json'}

        try:
            response = requests.post(apiUrl, files=postData, headers=headers)
            responseJson = response.json()
            return responseJson['url']
        except requests.exceptions.RequestException:
            self.logger.exception("dbco.link POST url error {}".format(comicObject))
        except json.decoder.JSONDecodeError:
            self.logger.exception("dbco.link json response decode error, {} (at {})".format(
                response.content, comicObject))

    @staticmethod
    def makeComic(messages):
        chars = set()  # chars is a set of the "characters" involved, at this point these are message.user.nick
        panels = []  # panels is a list of comic "panels", each involving 1-2 "characters", each with a message spoken
        panelHeight = 300
        panelWidth = 450

        # one "panel" is a list of the (message.user.nick, message.messageString) pairs to be drawn in that panel
        panel = []
        lastChar = None
        for message in messages:
            char = message[0]
            chars.add(char)

            # Start a new panel if the panel is full or the same user speaks twice in a row
            if len(panel) == 2 or len(panel) == 1 and char == lastChar:
                panels.append(panel)
                panel = []

            panel.append(message)
            lastChar = char
        panels.append(panel)

        # Randomly associate a character image to each user
        filenames = glob.glob('data/comics/chars/*')
        charmap = {ch: Image.open(f).convert("RGBA") for ch, f in zip(chars, sample(filenames, len(chars)))}
        # charmap is now a dict of message.user.nick to their randomly picked "character" image

        # How big is the whole comic?
        imgWidth = panelWidth
        imgHeight = panelHeight * len(panels)

        # this will be the background image for each separate panel
        background = Image.open('data/comics/backgrounds/beach-paradise-beach-desktop.jpg').convert("RGBA")

        # comicImage is our entire comic, to be filled with our panels
        comicImage = Image.new("RGBA", (imgWidth, imgHeight), (0xff, 0xff, 0xff, 0xff))
        font = ImageFont.truetype('data/comics/fonts/ComicRelief.ttf', 14)

        for i, panel in enumerate(panels):
            # paste the panel Image object onto our comic Image object, using the index i to offset height
            comicImage.paste(Comic.makePanel(panel, panelWidth, panelHeight, charmap, background, font),
                             (0, panelHeight * i))

        comicByteArray = BytesIO()
        comicImage.save(comicByteArray, format="PNG", quality=85)
        return comicByteArray.getvalue()

    @staticmethod
    def makePanel(panel, panelWidth, panelHeight, charmap, background, font):
        # for each panel, create an Image object
        panelImage = Image.new("RGBA", (panelWidth, panelHeight), (0xff, 0xff, 0xff, 0xff))

        # paste the bg image into our panel Image
        panelImage.paste(background, (0, 0))
        draw = ImageDraw.Draw(panelImage)

        # call the wrap function to get a formatted string to be drawn onto the image
        # use 2/3rds panel width as the "max width" for the text
        (lines, (_, string1Height)) = Comic.wrap(panel[0][1], font, draw, 2 * panelWidth / 3)
        # then draw that string onto the image at 10 from the top, 10 from the left edge
        Comic.rendertext(lines, font, draw, (10, 10))

        string2Height = 0
        if len(panel) == 2:
            # if there is a second message in this panel, draw it differently from the first
            # call the wrap function again to get the second string (again with 2/3rds panel width as "max width")
            (string2, (string2Width, string2Height)) = Comic.wrap(panel[1][1], font, draw, 2 * panelWidth / 3.0)
            # then draw that string onto the image as close to the right edge as it can fit, 10 below the 1st string
            Comic.rendertext(string2, font, draw, (panelWidth - 10 - string2Width, string1Height + 10))

        # calculate the "height" of the text, with some spacing (used for scaling character images?)
        textHeight = string1Height + 10
        if string2Height > 0:
            textHeight += string2Height + 10 + 5

        # scale the character image for the 1st message and paste it into the panel Image object
        maxch = panelHeight - textHeight
        char1Image = Comic.fitimg(charmap[panel[0][0]], 2 * panelWidth / 5.0 - 10, maxch)
        panelImage.paste(char1Image, (10, panelHeight - char1Image.size[1]), char1Image)

        # if there is a second character, also scale and paste that into the panel Image object
        if len(panel) == 2:
            char2Image = Comic.fitimg(charmap[panel[1][0]], 2 * panelWidth / 5.0 - 10, maxch)
            char2Image = char2Image.transpose(
                Image.FLIP_LEFT_RIGHT)  # flip the character image, so it "faces" the first character image
            panelImage.paste(char2Image, (panelWidth - char2Image.size[0] - 10, panelHeight - char2Image.size[1]),
                             char2Image)

        # draw a small black line at the top? of the panel Image
        draw.line([(0, 0), (0, panelHeight - 1), (panelWidth - 1, panelHeight - 1), (panelWidth - 1, 0), (0, 0)],
                  (0, 0, 0, 0xff))

        return panelImage

    @staticmethod
    def wrap(message, font, draw, maxWidth):
        """
        Work out how much space `message` will take up on the image. Returns a list of strings representing each line
        of the message split into lines after wrapping and the wrapped width and height as a tuple
        """
        messageWords = message.split()
        wrappedWidth = 0
        wrappedHeight = 0
        lines = []

        while messageWords:
            numWords = 1
            while numWords < len(messageWords):
                # Try fitting the next numWords words on the line
                width, _ = draw.textsize(" ".join(messageWords[:numWords]), font=font)
                if width > maxWidth:
                    numWords -= 1
                    break
                else:
                    # There's still space, try another word
                    numWords += 1

            if numWords == 0 and messageWords:  # we've hit a case where the current word is wider than the screen
                numWords = 1

            # How big is this line?
            lineWidth, lineHeight = draw.textsize(" ".join(messageWords[:numWords]), font=font)

            wrappedWidth = max(wrappedWidth, lineWidth)  # wrappedWidth should be the length of the longest line
            wrappedHeight += lineHeight

            lines.append(" ".join(messageWords[:numWords]))
            messageWords = messageWords[numWords:]  # drop the words wrapped so far and continue

        return lines, (wrappedWidth, wrappedHeight)

    @staticmethod
    def rendertext(lines, font, draw, position):
        """
        This function renders the given `lines` at the given position in the given "draw" object - ImageDraw.Draw()
        """
        ch = position[1]
        for line in lines:
            _, h = draw.textsize(line, font=font)
            draw.text((position[0], ch), line, font=font, fill=(0xff, 0xff, 0xff, 0xff))
            ch += h

    @staticmethod
    def fitimg(img, width, height):
        """
        Scale img proprotionally so that it's new width is `width` or height is `height`, whichever comes first.
        """

        # Calculate required scale factor to match width
        sf = width / img.size[0]
        # if this would make the image taller than the desired height, instead use the scale factor to match height
        if img.size[1] * sf > height:
            sf = height / img.size[1]

        # Resize image, round pixel count to nearest integer
        return img.resize((int(sf * img.size[0] + 0.5), int(sf * img.size[1] + 0.5)), Image.LANCZOS)


comic = Comic()
