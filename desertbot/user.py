# -*- coding: utf-8 -*-


class IRCUser(object):
    def __init__(self, user: str):
        self.user = None
        self.hostmask = None

        if '!' in user:
            userArray = user.split('!')
            self.name = userArray[0]
            if len(userArray) > 1:
                userArray = userArray[1].split('@')
                self.user = userArray[0]
                self.hostmask = userArray[1]
            self.string = "{}!{}@{}".format(self.name, self.user, self.hostmask)
        else:
            self.name = user
            self.string = "{}!{}@{}".format(self.name, None, None)
