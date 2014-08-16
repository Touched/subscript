'''
Pokescript command utilities.
'''

import struct

class CommandTable(object):

    table = 0x15F9B4

    def __init__(self, path, count=214):

        self.commands = []

        with open(path, 'rb') as rom:
            rom.seek(self.table)

            for _ in range(count):
                command = struct.unpack('<I', rom.read(4))[0]
                self.commands.append(command - 0x08000000)

    def command(self, number):
        return self.commands[number]


