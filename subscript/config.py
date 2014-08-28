import json
import os

class RomConfig(object):
    '''
    Load settings file for a given ROM.
    Everything reading settings must use this class, so that the mechanism can
    be easily changed. Caches lookups to speed up item retrieval.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        with open('../config/roms.json') as file:
            self.config = json.load(file)

        self.cache = {}

    def __getitem__(self, index):
        if index in self.cache:
            return self.cache[index]
        elif index in self.config:
            out = self.config[index]

            child = self.config[index]
            while child['inherits']:
                parent = self.config[child['inherits']]

                # Add all parent keys to the output, unless they already exist
                for key in parent:
                    if key not in out:
                        out[key] = parent[key]

                # Check if parent inherited anything
                child = parent

            # Cache item for faster lookup next time
            self.chache[index] = out
            return out
        else:
            # TODO: Raise a "NotSupported" exception
            raise IndexError("Rom not supported")

c = RomConfig()
c['AXVE']