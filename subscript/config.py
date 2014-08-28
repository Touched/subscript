import json
import os

class Config(object):
    '''
    Load settings file. Uses a hard-coded search path to look for the config file.
    Everything reading settings must use this file, so that the mechanism can
    be easily changed.
    '''

    user = os.path.expanduser('~')
    cwd = os.getcwd()

    searchpath = [cwd]

    def __init__(self, path=None):
        '''
        Constructor
        '''
        with open(path) as file:
            self.config = json.load(file)
