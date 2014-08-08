"""
These functions are imported into the global namespace of the script, and can
be called without any module prefix. 
"""

import subscript.langtypes as langtypes
import subscript.script as script
import subscript.registry as registry

functions = registry.Registry('main')

# Begin standard built-in functions:
# These are imported into the global namespace of the script

@functions.register
def lock(lockall=False):
    '''
    If `lockall` is False, and the script was called by a Person event, then
    that Person's movement will cease. Otherwise, the function locks all
    overworlds on-screen in place.

    :param lockall: Lock every overworld if True
    '''
    if lockall:
        return ('lockall',)
    else:
        return ('lock',)

@functions.register
def applymovement(movements, overworld=0xFF):
    '''
    Moves the overworld with Person ID `overworld` with the movement set
    `movements`. The function moves the player by default.

    :param movements: A list of the movements to use.
    :param overworld: The ID of the overworld to apply the movement to.
    '''
    return ('applymovement', overworld, movements.value)

@functions.register
def message(string, keepopen=False):
    out = []
    out.append(('loadpointer', 0, string.value))
    if keepopen:
        out.append(('callstd', 4))
    else:
        out.append(('callstd', 6))
    return out

@functions.register
def msgbox(string, keepopen=False):
    # An alias for message()
    out = []
    out.append(('loadpointer', 0, string.value))
    if keepopen:
        out.append(('callstd', 4))
    else:
        out.append(('callstd', 6))
    return out

@functions.register
def question(string):
    out = []
    out.append(('loadpointer', 0, string.value))
    out.append(('callstd', 5))
    return out

@functions.register
def givepokemon(species, level=5, item=0):
    return ('givepokemon', species, level, item, 0, 0, 0)

@functions.register
def fanfare(sound):
    return ('fanfare', sound)

@functions.register
def waitfanfare():
    return ('waitfanfare',)

@functions.register
def closeonkeypress():
    return ('closeonkeypress',)

@functions.register
def call(pointer):
    return ('call', pointer)

@functions.register
def callstd(func):
    return ('callstd', func)

@functions.register
def pauseevent(a):
    return ('pause', a)

@functions.register
def disappear(b):
    return ('hidesprite', b)

@functions.register
def release(doall=False):
    if doall:
        return ('releaseall',)
    else:
        return ('release',)

@functions.register
def additem(item, quantity=1):
    return ('additem', item, quantity)

@functions.register
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

@functions.register
def givedecoration(decoration):
    out = []
    out.append(('copyvarifnotzero', 0x8000, decoration))
    out.append(('callstd', 7))
    return out

@functions.register
def finditem(item, quantity=1):
    # A Pokeball find item
    out = []
    out.append(('copyvarifnotzero', 0x8000, item))
    out.append(('copyvarifnotzero', 0x8001, quantity))
    out.append(('callstd', 1))
    return out

@functions.register
def battle(species, level=70, helditem=0):
    return [('setwildbattle', species, level, helditem), ('dowildbattle',)]


