import json
import os


class DataStore(object):
    def __init__(self, storagePath="desertbot_data.json"):
        self.storagePath = storagePath
        self.data = None
        self.load()

    def load(self):
        if not os.path.exists(self.storagePath):
            self.data = {}
            self.save()
            return
        with open(self.storagePath) as storageFile:
            self.data = json.load(storageFile)

    def save(self):
        tmpFile = "{}.tmp".format(self.storagePath)
        with open(tmpFile, "w") as storageFile:
            storageFile.write(json.dumps(self.data, indent=4))
        os.rename(tmpFile, self.storagePath)
