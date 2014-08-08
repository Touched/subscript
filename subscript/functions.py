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
    If `lockall` is ``False``, and the script was called by a Person event, then
    that Person's movement will cease. Otherwise, the function locks all
    overworlds on-screen in place.

    :param lockall: Lock every overworld if ``True``
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
    '''
    Displays message with text `string` in a message box. If `keepopen` is ``True``,
    the box will not close until :func:`closeonkeypress` is called.

    :param string: The message to display
    :param keepopen: Whether the box will stay open or close when the player presses a key
    '''
    out = []
    out.append(('loadpointer', 0, string.value))
    if keepopen:
        out.append(('callstd', 4))
    else:
        out.append(('callstd', 6))
    return out

@functions.register
def msgbox(string, keepopen=False):
    '''
    Alias for :func:`message`
    '''
    # An alias for message()
    return message.inner(string, keepopen)

@functions.register
def question(string):
    '''
    Displays `string` in a message box, and then displays a Yes/No selection box.
    If the player cancels or selects No, ``LASTRESULT`` is set to ``0``. Otherwise
    it is set to ``1``.

    :param string: The question to ask.
    '''
    out = []
    out.append(('loadpointer', 0, string.value))
    out.append(('callstd', 5))
    return out

@functions.register
def givepokemon(species, level=5, item=0):
    '''
    Add the Pokemon given by `species` to the player's party. If it is full,
    it is sent to the PC.

    :param species: The Pokemon to give.
    :param level: The level of the Pokmeon. Defaults to ``5``
    :param item: The item it will hold. Defaults to nothing.
    '''
    return ('givepokemon', species, level, item, 0, 0, 0)

@functions.register
def fanfare(sound):
    '''
    Plays the specified fanfare. Non-blocking.

    :param sound: The sound to play
    '''
    return ('fanfare', sound)

@functions.register
def waitfanfare():
    '''
    Blocks until function :func:`fanfare` has finished.
    '''
    return ('waitfanfare',)

@functions.register
def closeonkeypress():
    '''
    Closes a message that had the `keepopen` parameter set to ``True``.
    '''
    return ('closeonkeypress',)

@functions.register
def call(pointer):
    '''
    Jumps to destination and continues script execution from there.
    The location of the calling script is remembered and can be returned to later.

    The maximum script depth (that is, the maximum nested calls you can make) is
    20. When this limit is reached, the game starts treating call as goto

    :param pointer: The pointer to jump to
    '''
    return ('call', pointer)

@functions.register
def callstd(func):
    '''
    Calls a standard script function.

    :param func: The index of the function to call.
    '''
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


