from subscript.script import Command
import functools
import inspect

class Registry(object):
    '''
    Registers module functions.
    '''

    def __init__(self, name):
        self.registry = {}
        self.name = name

    def register(self, f):
        @functools.wraps(f)
        def function(script, *args, **kwargs):
            ret = f(script, *args, **kwargs)

            if type(ret) == bytes:
                return ret
            elif type(ret) == tuple:
                return Command.create(*ret)
            elif type(ret) == list:
                out = []
                for item in ret:
                    out.append(Command.create(*item))
                return out

        function.inner = f

        self.registry[f.__name__] = function
        return function

    def __iter__(self):
        return iter(self.registry)

    def __getitem__(self, index):
        return self.registry[index]