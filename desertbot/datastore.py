import json
import os


class DataStore(object):
    def __init__(self, storagePath="desertbot_data.json"):
        self.storagePath = storagePath
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.storagePath):
            self.save()
            return
        with open(self.storagePath) as storageFile:
            self.data = json.load(storageFile)

    def save(self):
        tmpFile = "{}.tmp".format(self.storagePath)
        with open(tmpFile, "w") as storageFile:
            storageFile.write(json.dumps(self.data, indent=4))
        os.rename(tmpFile, self.storagePath)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, item):
        return self.data[item]
