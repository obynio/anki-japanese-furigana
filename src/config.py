import json
import os
from aqt.utils import showInfo

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

    def getBracketNotation(self):
        return self.data['UseBracketNotation']

    @saveconfig
    def setBracketNotation(self, isEnabled):
        self.data['UseBracketNotation'] = isEnabled[0]