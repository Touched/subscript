'''
Basic components for script files.
'''

import collections
import subscript.datatypes
import subscript.config
import json
import inspect

class Script(object):
    '''
    Represents a script - a collection of sections.
    '''

    def __init__(self, start, path):
        '''
        Create a new script.
        '''
        self.rom = path
        self.sections = []
        self.base = start
        Section.counter = 0
        SectionRaw.counter = 0

        # State variables. Functions can store data here
        self._state = {}

        self.config = subscript.config.RomConfig()

        with open(self.rom, 'rb') as file:
            file.seek(0xAC)

            # Code is in ASCII, but UTF-8 is ASCII compatible
            self._code = file.read(4).decode()

    def add(self, value=None):
        '''
        Create a new section and add it to the list.
        '''
        if value == None:
            section = Section(self)
            self.sections.append(section)
            return section
        elif isinstance(value, Section):
            self.sections.append(value)
            return value

    def compile(self):
        for section in self.sections:
            print(section)

    @property
    def code(self):
        '''
        Return the 4 character game code for the GBA ROM that this script is
        attached to.
        '''
        return self._code

    @property
    def language(self):
        '''
        Return the scripting language that this ROM uses. Used to allow for syntax
        or semantic differences in each ROM.
        '''
        return self.config[self._code]['language']

    @property
    def state(self):
        '''
        Private state variable for functions. Only the named function can set
        and read it.
        '''

        # Get the calling function's name
        name = inspect.stack()[1][3]

        try:
            return self._state[name]
        except KeyError:
            return None

    @state.setter
    def state(self, value):
        '''
        Setter for the state property.
        '''

        name = inspect.stack()[1][3]
        self._state[name] = value

class Section(object):
    '''
    Represents a code section - a sequence of commands referenced by a dynamic
    pointer.
    '''
    counter = 0

    def __init__(self, parent):
        '''
        Constructor.
        '''
        self.commands = []
        self._size = 0
        self._parent = parent
        self.name = type(self).__name__ + str(self.__class__.counter)
        self.__class__.counter += 1

    def append(self, command):
        '''
        Add a command to this section.
        '''
        if isinstance(command, collections.Sequence):
            for item in command:
                self.append(item)
        else:
            try:
                self._size += len(command)
            except AttributeError:
                raise TypeError
            self.commands.append(command)

    def last(self):
        '''
        Return the most recent command.
        '''
        return self.commands[-1]

    @property
    def parent(self):
        return self._parent

    @property
    def size(self):
        return self._size

    def __len__(self):
        return self.size

    def dynamic(self, offset=0):
        if offset:
            return subscript.datatypes.RelativePointer(self.parent, self, offset)
        else:
            return subscript.datatypes.DynamicPointer(self.parent, self)

class SectionRaw(Section):
    '''
    Used for appending raw binary data to a script section.
    '''

    def __init__(self, parent, data, debug=None):
        super().__init__(parent)
        self.data = data
        self._size = len(data)
        self.debug = debug if debug else data

    def append(self, command):
        raise NotImplementedError

class Command(object):
    '''
    Represents a single command.
    '''

    # Load command configuration for the whole class
    with open('tables/commands.json') as file:
        commands = json.load(file)

    def __init__(self, name, args):
        self.name = name
        self.args = args

        # Calculate size - Add one for the command byte
        self._size = sum(arg.size for arg in self.args) + 1

    @classmethod
    def create(cls, name, *args):
        try:
            command = cls.commands[name]
            forward = []
            if len(args) != len(command['args']):
                raise TypeError('Script command "{}" requires exactly {} arguments; {} were provided.'.format(name, len(command['args']), len(args)))
            for n, arg in enumerate(args):
                if isinstance(arg, subscript.datatypes.Type):
                    # If they are already datatypes, no conversion need be done
                    # TODO: Verfiy that the correct type is used
                    forward.append(arg)
                else:
                    # Convert the arguments to the appropriate datatype
                    t = subscript.datatypes.Type.create(command['args'][n]['type'], arg)
                    forward.append(t)
            return cls(name, forward)
        except KeyError:
            raise ValueError('Unknown command "{}"'.format(name))

    def compile(self):
        code = self.__class__.commands[self.name]['code']
        out = bytearray()
        out.append(code)
        for arg in self.args:
            out.extend(arg.to_hex())
        return bytes(out)

    @property
    def size(self):
        return self._size

    def __len__(self):
        return self.size

    @classmethod
    def decompile(cls, data):
        found = next((k, v) for k, v in cls.commands.items() if v['code'] == data[0])
        name = found[0]
        spec = found[1]

        # Slice the command byte away
        data = data[1:]

        out = []
        for arg in spec['args']:
            a = subscript.datatypes.Type.create(arg['type'], data)

            # Slice the data you just used
            data = data[a.size:]

            # Add to the arguments list
            out.append(a)

        return cls(name, out)

    def __str__(self):
        out = self.name
        for arg in self.args:
            if str(arg).isdigit():
                a = int(str(arg))
                if a <= 0xFF:
                    out += ' 0x{:02x}'.format(a)
                elif a <= 0xFFFF:
                    out += ' 0x{:04x}'.format(a)
                elif a <= 0xFFFFFF:
                    out += ' 0x{:06x}'.format(a)
                elif a <= 0xFFFFFFFF:
                    out += ' 0x{:08x}'.format(a)
                else:
                    out += ' 0x{:x}'.format(a)
            else:
                out += ' {}'.format(arg)

        return out

    def __repr__(self):
        return 'Command("{}")'.format(str(self))

if __name__ == '__main__':
    c = Command.create('compare', 0x4000, 1)
    print(c.compile(), c.size, Command.decompile(c.compile()))
