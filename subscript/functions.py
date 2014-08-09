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

# Missing functions
# - callstdif
# - gotostdif

# Functions that should be implemented elsewhere
# Assignment type functions
# - writebytetooffset
# - loadbytefrompointer
# - setfarbyte
# - copyscriptbanks
# - loadpointer
# - setbyte
# - setbyte2
# - setfarbyte
# - copyscriptbanks
# - copybyte
# - setvar
# - addvar
# - subvar
# - copyvar
# - copyvarifnotzero

# Comparison type functions
# - comparebanks
# - comparebanktobyte
# - comparebanktofarbyte
# - comparefarbytetobank
# - comparefarbytetobyte
# - comparefarbytes
# - compare
# - comparevars

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
def goto(destination):
    '''
    Jumps to `destination` and continues script execution from there.

    :param destination: Location to jump to.
    '''
    return ('goto', destination)

@functions.register
def gotostd(func):
    '''
    Jumps to the standard script function and continues execution from there.

    :param func:  The index of the function to call.
    '''
    return ('gotostd', func)

@functions.register
def pause(time):
    '''
    Blocks script execution for ``time``.

    :param time: The number of frame to wait
    '''
    return ('pause', time)

@functions.register
def disappear(sprite):
    '''
    Hides the overworld with ID ``sprite``

    :param sprite: The ID of the overworld to hide.
    '''

    return ('hidesprite', sprite)

@functions.register
def release(doall=False):
    '''
    Reverses the effects of :func:`lock`.

    :param doall: Reverse the effects of :command:`lockall` or :command:`lock`.
    '''
    if doall:
        return ('releaseall',)
    else:
        return ('release',)

@functions.register
def additem(item, quantity=1):
    '''
    Silently add an item to the player's bag.

    :param item: The item to add.
    :param quanity: How many copies of `item` to give. Defaults to ``1``
    '''
    return ('additem', item, quantity)

@functions.register
def giveitem(item, quantity=1, fanfare=0):
    '''
    Gives the player an item, adding to to their bag while displaying a message
    and playing an optional sound.

    :param item: The item to add.
    :param quanity: How many copies of `item` to give. Defaults to ``1``.
    :param fanfare: The sound to play.
    '''
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
    '''
    :command:`nop` in FireRed
    '''
    out = []
    out.append(('copyvarifnotzero', 0x8000, decoration))
    out.append(('callstd', 7))
    return out

@functions.register
def finditem(item, quantity=1):
    '''
    Gives the player an item, adding to to their bag while displaying a message
    saying that they found the item.

    :param item: The item to add.
    :param quanity: How many copies of `item` to give. Defaults to ``1``.
    '''

    out = []
    out.append(('copyvarifnotzero', 0x8000, item))
    out.append(('copyvarifnotzero', 0x8001, quantity))
    out.append(('callstd', 1))
    return out

@functions.register
def battle(species, level=70, item=0):
    '''
    Triggers a prefined wild Pokemon battle. Blocks until the battle finishes.

    :param species: The Pokemon to battle
    :param level: The level of the wild Pokemon. Defaults to 70 (Legendary)
    :param item: The item that the wild Pokemon holds.
    '''

    return [('setwildbattle', species, level, item), ('dowildbattle',)]

@functions.register
def jumpram():
    '''
    Executes a script stored in a default RAM location.
    '''
    return ('jumpram',)

@functions.register
def killscript():
    '''
    Executes a script stored in a default RAM location.
    '''
    return ('killscript',)

@functions.register
def setbyte(byte):
    '''
    Pads the specified value to a dword, and then writes that dword to a
    predefined address (0x0203AAA8).

    :param byte: Value to set
    '''
    return ('setbyte', byte)

@functions.register
def arm(pointer):
    '''
    Calls the ARM assembly routine stored at offset.

    :param pointer: Offset
    '''

    # Unset Thumb mode
    routine = pointer & ~(1)
    return ('callasm', routine)

@functions.register
def thumb(pointer):
    '''
    Calls the Thumb assembly routine stored at offset.

    :param pointer: Offset
    '''

    # Set Thumb mode
    routine = pointer | 1
    return ('callasm', routine)

@functions.registry
def asm(pointer):
    '''
    Calls the assembly routine at the pointer, without setting the mode.

    :param pointer: Offset
    '''
    return ('callasm')


