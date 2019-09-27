import json
import os


class DataStore(object):
    def __init__(self, storagePath="desertbot_data.json"):
        self.storagePath = storagePath
        self.data = {}
        self.load()

    def load(self):
        if not os.path.exists(self.storagePath):
            with open(os.path.join("desertbot", "datastore_default.json")) as templateFile:
                self.data = json.load(templateFile)
            self.save()
            return
        with open(self.storagePath) as storageFile:
            self.data = json.load(storageFile)
        self.checkDefaults()

    def checkDefaults(self):
        """
        If data exists, we still wanna make sure we load in things from defaults if there's things in the defaults that aren't in our actual data
        """
        with open(os.path.join("desertbot", "datastore_default.json")) as templateFile:
            defaultData = json.load(templateFile)
        for key, data in defaultData.items():
            if key not in self.data:
                self.data[key] = data

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

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()
    
    def __contains__(self, key):
        return key in self.data
