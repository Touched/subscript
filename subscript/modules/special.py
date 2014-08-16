# http://www.pokecommunity.com/showthread.php?t=184273
# The special table is located at 0x0815FD60.

register = None

def special(number, variable=None):
    if variable:
        return('special2', variable, number)

    return ('special', number)

@register
def heal():
    return special(0)

@register
def clear():
    return special(1)