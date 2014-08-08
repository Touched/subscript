import collections
import math
from pprint import pprint
import struct
import cartographer.pathfinder as pathfinder


maps_table = 0x5524C
banks_count = 0x2B
maps_count = [5, 123, 60, 66, 4, 6, 8, 10, 6, 8, 20, 10, 8, 2, 10, 4, 2, 2, 2, 1, 1, 2, 2, 3, 2, 3, 2, 1, 1, 1, 1, 7, 5, 5, 8, 8, 5, 5, 1, 1, 1, 2, 1]

def read_pointer(rom):
    return struct.unpack('<I', rom.read(4))[0] & 0x1FFFFFF

def read_int(rom):
    return struct.unpack('<I', rom.read(4))[0]

def read_byte(rom):
    return struct.unpack('B', rom.read(1))[0]

def load_maps(rom):
    rom.seek(maps_table)
    rom.seek(read_pointer(rom))

    pointers = []
    banks = []

    for bank in range(banks_count):
        pointers.append(read_pointer(rom))

    for bank, pointer in enumerate(pointers):
        rom.seek(pointer)
        maps = []
        for _ in range(maps_count[bank]):
            maps.append(read_pointer(rom))
        banks.append(maps)

    return banks

def print_perm(num):
    ch = ' '

    if num == 0x1:
        ch = 'X'
    elif num in range(4, 8):
        ch = '~'
    else:
        ch = '.'

    print(ch, end=' ')

# NPC: bPerson, hSprite, hX, hY, hUnknown, bBehaviour, bUnknown, bBehaviour,
#   bTrainer, bUnknown, hLOS, pScript, hFlag, hUnknown
# Exit: hX, hY, bUnknown, bWarp, bMap, bBank
# Trap: hX, hY, hUnknown, hVariable, hValue, hUnknown, pScript
# Sign: hX, hY, bLevel, bType, bUnknown, bUnknown, pScript

class Element(object):
    def __init__(self, data):
        for field, item in zip(self.__class__.fields.split(), data):
            setattr(self, field, item)

    @classmethod
    def create(cls, fp):
        try:
            cls.struct
        except AttributeError:
            cls.struct = struct.Struct(cls.format)

        data = fp.read(cls.struct.size)

        return cls(cls.struct.unpack(data))

class Person(Element):
    #format = '<BHHHxxBxBBxHIHxx'
    format = '<BHxBxBxxBxBBxHIHxx'
    fields = 'id sprite x y behaviour movement trainer radius script flag'

class Warp(Element):
    format = '<HHxBBB'
    fields = 'x y warp map bank'

class Trigger(Element):
    format = '<HHxxHHxxI'
    fields = 'x y flag value script'

class Sign(Element):
    format = '<HHBBxxI'
    fields = 'x y level kind script'

def load_map(rom, map_offset, sprites_offset):
    # https://github.com/shinyquagsire23/MEH/blob/master/src/us/plxhack/MEH/IO/MapData.java
    store = rom.tell()

    # Seek to the map
    rom.seek(map_offset)

    # Read the dimensions
    width, height = read_int(rom), read_int(rom)

    # Read the map tile data
    _ = read_pointer(rom) # Border tiles, but we don't care
    map_tiles = read_pointer(rom)
    rom.seek(map_tiles)

    movements = []
    tiles = []

    for y in range(height):
        move_row = []
        tile_row = []
        for x in range(width):
            raw = struct.unpack('<H', rom.read(2))[0]

            # Extract the data from the tile
            id, perm = (raw & 0x3FF), (raw & 0xFC00) >> 10

            move_row.append(perm)
            tile_row.append(id)
        movements.append(move_row)
        tiles.append(tile_row)

    elements = []

    # Seek to the sprites
    rom.seek(sprites_offset)

    # Tuples for instantiation
    counts = tuple(read_byte(rom) for _ in range(4))
    data = tuple(read_pointer(rom) for _ in range(4))
    types = [Person, Warp, Trigger, Sign]

    for ptr, count, cls in zip(data, counts, types):
        rom.seek(ptr)
        for item in range(count):
            element = cls.create(rom)
            elements.append(element)

    rom.seek(store)

    return (width, height, tiles, movements, elements)

def find(x, y, elements):
    result = []
    for element in elements:
        if element.x == x and element.y == y:
            result.append(element)
    return tuple(result)

def make_path(data):
    '''
    Create a path from the map
    '''
    result = []

    for y in range(data[1]):
        row = []
        for x in range(data[0]):
            move = data[3][y][x]
            res = find(x, y, data[4])

            # Movement permission, change the
            ch = move

            # Person event
            if len(res):
                el = res[0] # Only one per block, maybe sort?

                if type(el) == Warp:
                    pass
                elif type(el) == Sign:
                    pass
                elif type(el) == Trigger:
                    pass
                elif type(el) == Person:
                    ch = 0xFF

            row.append(ch)

        result.append(row)
    return result

def walk(path, start, end):
    x, y = start
    x2, y2 = end

    finder = pathfinder.Pathfinder(path, start, end)

    route = finder.output

    for y, row in enumerate(path):
        for x, item in enumerate(row):
            if item == 1:
                ch = 'X'
            elif item == 12:
                ch = ' '
            else:
                ch = ' '

            if (x, y) in route:
                ch ='.'

            print(ch, end='')
        print()



with open('test.gba', 'rb') as rom:
    table = load_maps(rom)
    bank, map_ = 3, 1

    pointer = table[bank][map_]

    # Seek to map header
    rom.seek(pointer)
    map_ptr = read_pointer(rom)
    sprites_ptr = read_pointer(rom)
    data = load_map(rom, map_ptr, sprites_ptr)
    data = make_path(data)
    walk(data, (0x8, 0x5), (0x1A, 0x1B))
    #width, heigth = read_pointer(rom), read_pointer(rom)

    #rom.seek(pointer)