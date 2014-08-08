import subscript.script
import subscript.datatypes
import subscript.textparse as textparse
import subscript.codec
import ast

class TypeRegistry(type):
    '''
    Holds information about the available types. Automatic registration of types
    upon subclassing subscript.langtypes.Type. Subscript the Type class to get
    the class tied to that name. e.g. Type['Raw']
    '''

    registry = {}

    def __init__(cls, name, bases, nmspc):
        super(TypeRegistry, cls).__init__(name, bases, nmspc)

        # Add to the registry
        TypeRegistry.registry[cls.__name__] = cls

    @classmethod
    def __getitem__(cls, key):
        return cls.registry[key]

    @classmethod
    def __contains__(cls, key):
        return key in cls.registry

class Type(metaclass=TypeRegistry):
    '''
    Abstract base class for generic types.
    '''

    def __init__(self, script, value):
        self.parent = script
        self._value = value

    @property
    def value(self):
        '''
        Must return an object that is subclassed from subscript.datatypes.Type
        '''
        return self._value

class SectionType(Type):
    '''
    Base class for movements, messages, etc.
    '''
    def __init__(self, script, value):
        self._section = None
        super().__init__(script, value)

    @property
    def value(self):
        '''
        Add this section to the script's sections. Only done when its value is
        requested.
        '''
        if self._section == None:
            self._section = self.section()
            self.parent.add(self._section)

        return self._section.dynamic()

    def section(self):
        '''
        Must return an object subclassed from subscript.script.Section.
        '''
        raise NotImplementedError

class Movement(SectionType):
    '''
    For applymovement style commands.
    '''

    def section(self):
        # Parse movement data here from the self.value property
        data = b'\xFE'
        return subscript.script.SectionRaw(self.parent, data)

class String(SectionType):
    '''
    For messagebox style commands.
    '''

    def section(self):
        # Print escape sequences (repr), and slice the quotes
        value = repr(self._value)[1:-1]
        # Replace double backslashes in the text - for invalid escape sequences
        value = value.replace('\\\\', '\\')
        p = textparse.PoketextParser()
        p.feed(value)
        data = p.output
        return subscript.script.SectionRaw(self.parent, data)

class Raw(SectionType):
    '''
    For applymovement style commands.
    '''

    def section(self):
        if type(self.value) != bytes:
            raise TypeError
        return subscript.script.SectionRaw(self.parent, self.value)

class Flag(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.Flag(self._value)

class Var(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.Variable(self._value)

class Bank(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.Bank(self._value)

class Buffer(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.Buffer(self._value)

class HiddenVar(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.HiddenVar(self._value)

class Pointer(Type):
    '''
    A flag.
    '''

    @property
    def value(self):
        return subscript.datatypes.Pointer(self._value)

class TableLookup():
    '''
    Looks up a string in a table in the ROM.
    '''

    def __init__(self, path, offset, length, count):
        self.table = []
        # Offset of the table
        self.offset = offset
        # The length of an entry
        self.entry = length
        # The number of entries for this type
        self.entries = count

        with open(path, 'rb') as rom:
            rom.seek(self.offset)
            for _ in range(self.entries):
                data = rom.read(self.entry)
                self.table.append(self.handle_entry(data))

    def handle_entry(self, data):
        '''
        Populate the table
        '''
        out = ''
        for b in data:
            if b == 255:
                break
            ch = subscript.codec.decoding_dict[b]
            if ch:
                out += ch
        return out.lower()

    def __getitem__(self, value):
        '''
        Look up a value in the table and return a datatype
        '''
        if type(value) == str:
            try:
                return self.table.index(value.strip().lower())
            except ValueError:
                raise KeyError(value)
        elif type(value) == int:
            return self.table[value]
        else:
            raise TypeError(value)

class Table(Type):
    table = None

    def __init__(self, script, value):
        super().__init__(script, value)

        if type(value) == ast.Str:
            self._value = self.__class__.table[value.s]

    @property
    def value(self):
        return self._value

class Pokemon(Table):
    table = TableLookup('test.gba', 0x245EE0, 0xB, 412)

class Item(Table):
    table = TableLookup('test.gba', 0x3DB028, 0x2C, 375)

class Attack(Table):
    table = TableLookup('test.gba', 0x247094, 0xD, 355)

class File(SectionType):
    '''
    Import mechanics. Allow files from the file system to be loaded as types.
    '''
    def __init__(self, script, value):
        super().__init__(script, value)

    @property
    def value(self):
        return self._value

    def section(self):
        with open(self.value, 'rb') as f:
            data = self.file(f)
            return subscript.script.SectionRaw(self.parent, data)

    def file(self, file):
        raise NotImplementedError

class RawFile(File):
    def file(self, file):
        return file.read()
