import json
import os


class DataStore(object):
    def __init__(self, storagePath, defaultsPath):
        self.storagePath = storagePath
        self.defaultsPath = defaultsPath
        self.data = {}
        self.load()

    def load(self):
        # if a file data/defaults/<module>.json exists, it has priority on load
        if os.path.exists(self.defaultsPath):
            with open(self.defaultsPath) as storageFile:
                self.data = json.load(storageFile)
        # if not, use data/<network>/<module>.json instead
        elif os.path.exists(self.storagePath):
            with open(self.storagePath) as storageFile:
                self.data = json.load(storageFile)

    def save(self):
        # don't save empty files, to keep the data directories from filling up with pointless files
        if len(self.data) != 0:
            tmpFile = "{}.tmp".format(self.storagePath)
            with open(tmpFile, "w") as storageFile:
                storageFile.write(json.dumps(self.data, indent=4))
            os.rename(tmpFile, self.storagePath)

            # if this DataStore has a defaults file, save there aswell
            # ideally, defaults should be synced to github...
            # but this means changes to modules with defaults at runtime aren't overwritten on the server on a reboot
            if os.path.exists(self.defaultsPath):
                tmpFile = "{}.tmp".format(self.defaultsPath)
                with open(tmpFile, "w") as storageFile:
                    storageFile.write(json.dumps(self.data, indent=4))
                os.rename(tmpFile, self.defaultsPath)

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

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def keys(self):
        return self.data.keys()

    def get(self, key, defaultValue=None):
        return self.data.get(key, defaultValue)
