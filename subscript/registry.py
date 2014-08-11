import subscript.script as script
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
        def function(*args, **kwargs):
            ret = f(*args, **kwargs)

            if type(ret) == bytes:
                return ret
            elif type(ret) == tuple:
                return script.Command.create(*ret)
            elif type(ret) == list:
                out = []
                for item in ret:
                    out.append(script.Command.create(*item))
                return out

        function.inner = f
        function.state = {}

        self.registry[f.__name__] = function
        return function

    def __iter__(self):
        return iter(self.registry)

    def __getitem__(self, index):
        return self.registry[index]

def function_name():
    '''
    Gets the name of the decorated function that this was called from.
    '''
    return inspect.stack()[1][3]