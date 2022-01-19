import json
import os

from aqt import mw

path = os.path.join(os.path.dirname(__file__), "config.json")

def saveconfig(func):
    def wrapper(self, *args):
        func(self, args)

        with open(path, 'w') as outfile:
            json.dump(self.data, outfile, indent=4)
    return wrapper

class Config:
    with open(path) as f:
         data = json.load(f)

    def getUseRubyTags(self):
        return self.data['useRubyTags']

    @saveconfig
    def setUseRubyTags(self, isEnabled):
        self.data['useRubyTags'] = isEnabled[0]

    def getIgnoreNumbers(self):
        return self.data['ignoreNumbers']

    @saveconfig
    def setIgnoreNumbers(self, isEnabled):
        self.data['ignoreNumbers'] = isEnabled[0]
