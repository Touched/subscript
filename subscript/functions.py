import subscript.langtypes as langtypes
import subscript.script as script

registry = {}

def register(f):
    '''
    Decorator that registers its argument to the function list.
    '''
    registry[f.__name__] = f
    return f

@register
def lock(lockall=False):
    if lockall:
        return script.Command.create('lockall')
    else:
        return script.Command.create('lock')

@register
def applymovement(overworld, movements):
    return script.Command.create('applymovement', overworld, movements.value)

@register
def message(string, keepopen=False):
    out = []
    out.append(script.Command.create('loadpointer', 0, string.value))
    if keepopen:
        out.append(script.Command.create('callstd', 4))
    else:
        out.append(script.Command.create('callstd', 6))
    return out

@register
def question(string):
    out = []
    out.append(script.Command.create('loadpointer', 0, string.value))
    out.append(script.Command.create('callstd', 5))
    return out

@register
def givepokemon(species, level=5, item=0):
    return script.Command.create('givepokemon', species, level, item, 0, 0, 0)

@register
def fanfare(sound):
    return script.Command.create('fanfare', sound)

@register
def waitfanfare():
    return script.Command.create('waitfanfare')

@register
def closeonkeypress():
    return script.Command.create('closeonkeypress')

@register
def call(pointer):
    return script.Command.create('call', pointer)

@register
def callstd(func):
    return script.Command.create('callstd', func)

@register
def pauseevent(a):
    return script.Command.create('pause', a)

@register
def disappear(b):
    return script.Command.create('hidesprite', b)

@register
def release(doall=False):
    if doall:
        return script.Command.create('releaseall')
    else:
        return script.Command.create('release')