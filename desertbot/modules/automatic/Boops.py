from twisted.plugin import IPlugin
from desertbot.moduleinterface import IModule, BotModule
from zope.interface import implementer

import random
import re

from desertbot.message import IRCMessage
from desertbot.response import IRCResponse, ResponseType


@implementer(IPlugin, IModule)
class Boops(BotModule):

    boop_urls = [
                    "http://bit.ly/zA2bUY",             # i boop ur noes
                    "http://i.imgur.com/B2vDpq0.png",   # hey cat, imma boop ur head, lol
                    "http://bit.ly/ACbm0J",             # Iz gunna boop yer nose, k?
                    "http://bit.ly/qNyEZk",             # what do you think mr t is daydreaming about?
                    "http://bit.ly/zJrjGF",             # jeans kitty boop
                    "http://goo.gl/d054n",              # This is called "aversion therapy."
                    "http://goo.gl/6IoB0",              # my grumpy button, ur pushin' it
                    "http://imgur.com/O61oxTc.jpg",     # colonel goggie in the hallway with the nose boop
                    "http://bit.ly/yODbYA",             # You may go, but first I must boop your nose
                    "http://goo.gl/1Xu0LK",             # fluttershy & rainbow dash
                    "http://i.imgur.com/vC5gy.jpg",     # dog in car boop
                    "http://i.imgur.com/xmzLY.gifv",    # cat lap booping dog
                    "http://i.imgur.com/NSAKo.jpg",     # orange cat perma-booping dog on bed
                    "http://i.imgur.com/jpcKLuy.png",   # pinkie pie and twilight sparkle boop
                    "http://i.imgur.com/qeNvd.png",     # elephant boop
                    "http://i.imgur.com/wtK1T.jpg",     # jet booping tanker truck
                    "http://goo.gl/JHBKUb",             # real men head boop with kittens
                    "http://i.imgur.com/hlCm7aA.png",   # sweetie belle booping apple bloom
                    "http://i.imgur.com/BLQoL61.gifv",  # darting boop
                    "http://i.imgur.com/3b2lSjd.gifv",  # pounce boops
                    "http://i.imgur.com/P83UL.gifv",    # reciprocated cat boop
                    "http://i.imgur.com/H7iNX8R.jpg",   # white cat nose boop
                    "http://i.imgur.com/NoYdYtU.jpg",   # Lil Retriever Learns How To Boop
                    "http://i.imgur.com/jWMdZ.jpg",     # black & white kitten boop
                    "http://i.imgur.com/dz81Dbs.jpg",   # puppy picnic boop
                    "http://i.imgur.com/0KWKb.gifv",    # spinspinspin BOOP!
                    "http://i.imgur.com/UaNm6fv.gif",   # boop to turn off kitten
                    "http://i.imgur.com/QmVjLNQ.png",   # snow leopard boop
                    "http://i.imgur.com/HaAovQK.gifv",  # darting bed boop
                    "http://i.imgur.com/Le4lOKX.gifv",  # kitten gonna get him boop
                    "http://i.imgur.com/P7Ca5Si.gifv",  # shibe pikachu boop
                    "http://i.imgur.com/yvlmyNI.gifv",  # quick run up boop walk away (NewClassic)
                    "http://goo.gl/9FTseh",             # Fluttershy & Pinkie Pie boop
                    "http://i.imgur.com/yexMjOl.gifv",  # Archer boop
                    "http://goo.gl/l3lwH9",             # Cat boops a butt
                    "http://i.imgur.com/zOZvmTW.gifv",  # Bunny bumper cars
                    "http://i.imgur.com/P0a8dU2.gifv",  # Kitten beach boop loop
                    "http://i.imgur.com/LXFYmPU.gifv",  # Nose-booped cat retreats under blanket
                    "http://i.imgur.com/6ZJLftO.gifv",  # Cat booping a bunny's nose repeatedly
                    "http://i.imgur.com/MGKpBSE.gifv",  # Guillermo Del Toro pats Mana on the head, and they bow to each other
                    "http://i.imgur.com/lFhgLP8.gifv",  # Dolphin nose-boops a cat, who paws at it vaguely
                    "http://i.imgur.com/yEKxpSc.jpg",   # 2 Red Pandas nose-booping
                    "http://goo.gl/7YUnJF",             # pony gift boop?
                    "http://goo.gl/7yMb1y",             # Neil deGrasse Tyson science boop
                    "http://i.imgur.com/8VFggj4.gifv",  # What's in the boop box? (it's kittens)
                    "http://i.imgur.com/2dqTNoQ.gifv",  # Sheep and Cow charge boop
                    "http://i.imgur.com/h1TAtur.gifv",  # Young deer head boop
                    "http://i.imgur.com/zHrQoMT.gifv",  # run-by cat boop
                    "http://i.imgur.com/RKzPhan.gifv",  # kitteh using every kind of boop for attention
                    "http://i.imgur.com/CqTlFaX.gifv",  # snow leopard boops a cat, then flees
                    "http://i.imgur.com/oMDVg1b.gifv",  # mantis shrimp boops an octopus
                    "https://imgur.com/r/aww/Ih2NvGP",  # dog boops another dog with its paw "The hoomins do it all the time"
                    "http://i.imgur.com/gFcKWDM.gifv",  # fish jump-boops a bear
                    "http://i.imgur.com/kgPiK.jpg",     # pony with a small human riding it boops a horse
                    "http://goo.gl/S8LUk4",             # kitten boops a puppy, puppy tries to return it but falls over
                    "http://i.imgur.com/SkBaRNR.gifv",  # horse and cat boop and then facerub on the wall of a stable
                    "http://i.imgur.com/kc4SQIz.gifv",  # dog boops itself, paws ensue
                    "http://i.imgur.com/ddiNHHz.jpg",   # cartoon wolf boop, pass it on!
                    "http://i.imgur.com/6QPFAkO.gifv",  # monkey flings itself between trees, messing with a bunch of tiger cubs
                    "http://i.imgur.com/mncYpu5.gifv",  # hockey goalkeeper ass-boops another hockey player into a wall
                    "http://i.imgur.com/NZRxzNe.gifv",  # sneaky cupboard cat boops another cat
                    "http://i.imgur.com/1jMYf8U.gifv",  # a couple of guinea pigs boop a cat
                    "http://i.imgur.com/k6YicPf.gifv",  # dog gets booped on nose with a toy, then cat runs up and boops its back. dog is very confuse
                    "https://i.imgur.com/m67qRsQ.gifv", # lamb repeatedly boops its face into a dog's paw, dog doesn't care
                    "http://i.imgur.com/32H1kkw.gifv",  # HD BBC nature show boop
                    "http://i.imgur.com/pcksMNP.gifv",  # Kitten sitting on its back legs boops a doge (Corgi?) with its front legs
                    "https://i.imgur.com/8TKVJ63.gifv", # Goat stands on its back legs to boop with a horse
                    "http://i.imgur.com/1AgMAbK.gifv",  # cat runs out of a dark room, eyes glowing, and leaps into the camera
                    "http://i.imgur.com/i7J5VHI.gifv",  # kitten on a sofa jumps around and boops a dog peering up at it on the nose
                    "http://i.imgur.com/XTuRoOs.gifv",  # bunny boop triforce
                    "http://i.imgur.com/FkVNWlc.gifv",  # cat reaches up to grab and boop the camera with its nose
                    "http://i.imgur.com/lVxFUGF.gifv",  # secret bag cat boops other cat on bed
                    "http://i.imgur.com/bLIBH6J.gifv",  # orange kitten eyes up another kitten, then pounces. En Garde!
                    "http://i.imgur.com/V35yPa0.gifv",  # 2 dogs boop their snoots in an expert manner
                    "http://i.imgur.com/ihS28BF.gifv",  # dog boops a cat standing on the edge of a bath into it
                    "https://i.imgur.com/GBniOtO.gifv", # touch lamp cat gets booped on the nose
                    "http://www.gfycat.com/FarflungTeemingAtlasmoth",   # one cat boops another sitting in a bag, while another in a basket looks on
                    "https://i.imgur.com/NHCSPxj.jpg",  # 2 bunnies boop noses on a towel
                    "https://i.imgur.com/8tZ9wBy.gifv", # a red koala walks up to another and boops it on the nose
                    "http://imgur.com/dkLJLrt.mp4",     # corgi is wiggle nose booped, then turns to camera with tongue out
                    "https://i.imgur.com/JOwvswE.gifv", # finger pokes frog in the head until frog has had enough of that shit
                    "http://i.imgur.com/li9KPAD.gifv",  # corgi butt finger boops
                    "http://i.imgur.com/IciHp73.gifv",  # cat lying on its back gets a nose-boop, wiggles paws (image title: Excessive reaction to a booping)
                    "https://i.imgur.com/tMIW18y.jpg",  # dog on a swing boops another dog's nose, like Michelangelo's Creation of Adam (image title: the creashun of pupper)
                    "https://media.giphy.com/media/y1yTg5UheAqXK/giphy.gif", # iz safe? iz nottt! (cat pokes head out of sofa cushions, is booped and retreats)
                    "https://i.imgur.com/QkozEpp.gifv", # corgi lying on someone's lap in a car is booped (title: In case you had a bad day :))
                    "http://i.imgur.com/hP7RMSo.gifv",  # snek is booped, was not prepared (hello, *boop*, oh heck, i was not prepare)
                    "https://i.imgur.com/zZle0Sw.gifv", # horse in paddock is booped, sticks out tongue
                    "https://i.imgur.com/PxzCKCO.gifv", # toy robot approaches dog, dog boops it over
                    "http://hats.retrosnub.uk/DesertBus10/db10_penelope_boop_ian.gif", # Penelope boops Ian on the nose at DBX
                    "http://i.imgur.com/ECkZI3F.gifv",  # cat and puppy boop each other's noses with their paws
                    "https://i.imgur.com/FmMNIPy.mp4",  # dog boops the shadow of a pen being waggled
                    "http://i.imgur.com/Iipr2lg.png",   # red panda getting booped on the forehead
                    "http://i.imgur.com/WmRnfbX.png",   # can you smash my sadness? / *boop* / :)
                    "https://i.imgur.com/1R2dOmJ.gifv", # labrador aggressively boops other dog to steal their treat
                    "https://giant.gfycat.com/ElasticAdventurousCottontail.webm", # parrot gets booped from off-screen
                    "https://i.imgur.com/8mMGnA1.gifv", # cat boops dog, then escapes under a couch
                    "https://i.imgur.com/v13xyjM.gifv", # cat runs in, tentatively boops dog, then flees. dog is confused
                    "https://i.imgur.com/byR8SQY.gifv", # cat gently boops sleepy human's nose with their paw
                    ]

    def actions(self):
        return super(Boops, self).actions() + [('message-channel', 1, self.respond),
                                               ('message-user', 1, self.respond),
                                               ('action-channel', 1, self.respond),
                                               ('action-user', 1, self.respond)]

    def help(self, arg):
        return 'Responds to boops.'

    def respond(self, message: IRCMessage) -> IRCResponse:
        match = re.search('(^|[^\w])b[o0]{2,}ps?([^\w]|$)', message.messageString, re.IGNORECASE)
        if match:
            return IRCResponse(ResponseType.Say, f"Boop! {random.choice(self.boop_urls)}", message.replyTo)


boop = Boops()
