import subscript.langtypes as langtypes
import subscript.script as script

registry = {}

def register(f):
    '''
    Decorator that registers its argument to the function list.
    '''
    def function(*args, **kwargs):
        ret =  f(*args, **kwargs)

        if type(ret) == bytes:
            return ret
        elif type(ret) == tuple:
            return script.Command.create(*ret)
        elif type(ret) == list:
            out = []
            for item in ret:
                out.append(script.Command.create(*item))
            return out

    registry[f.__name__] = function
    return function

@register
def lock(lockall=False):
    if lockall:
        return ('lockall',)
    else:
        return ('lock',)

@register
def applymovement(overworld, movements):
    return ('applymovement', overworld, movements.value)

@register
def message(string, keepopen=False):
    out = []
    out.append(('loadpointer', 0, string.value))
    if keepopen:
        out.append(('callstd', 4))
    else:
        out.append(('callstd', 6))
    return out

@register
def msgbox(string, keepopen=False):
    # An alias for message()
    out = []
    out.append(('loadpointer', 0, string.value))
    if keepopen:
        out.append(('callstd', 4))
    else:
        out.append(('callstd', 6))
    return out

@register
def question(string):
    out = []
    out.append(('loadpointer', 0, string.value))
    out.append(('callstd', 5))
    return out

@register
def givepokemon(species, level=5, item=0):
    return ('givepokemon', species, level, item, 0, 0, 0)

@register
def fanfare(sound):
    return ('fanfare', sound)

@register
def waitfanfare():
    return ('waitfanfare',)

@register
def closeonkeypress():
    return ('closeonkeypress',)

@register
def call(pointer):
    return ('call', pointer)

@register
def callstd(func):
    return ('callstd', func)

@register
def pauseevent(a):
    return ('pause', a)

@register
def disappear(b):
    return ('hidesprite', b)

@register
def release(doall=False):
    if doall:
        return ('releaseall',)
    else:
        return ('release',)

@register
def additem(item, quantity=1):
    return ('additem', item, quantity)

@register
def giveitem(item, quantity=1, fanfare=0):
    # The generic giveitem
    out = []
    out.append(('copyvarifnotzero', 0x8000, item))
    out.append(('copyvarifnotzero', 0x8001, quantity))
    if fanfare > 0:
        out.append(('copyvarifnotzero', 0x8002, fanfare))
        out.append(('callstd', 9))
    else:
        out.append(('callstd', 0))
    return out

@register
def givedecoration(decoration):
    out = []
    out.append(('copyvarifnotzero', 0x8000, decoration))
    out.append(('callstd', 7))
    return out

@register
def finditem(item, quantity=1):
    # A Pokeball find item
    out = []
    out.append(('copyvarifnotzero', 0x8000, item))
    out.append(('copyvarifnotzero', 0x8001, quantity))
    out.append(('callstd', 1))
    return out

@register
def battle(species, level=70, helditem=0):
    # Wild Pokemon battle
    return (('setwildbattle', species, level, helditem), ('dowildbattle',))


