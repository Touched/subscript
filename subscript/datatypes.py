'''
Data types for script commands.
'''

import abc
import struct
import subscript.langtypes

class Type(metaclass=abc.ABCMeta):
    '''
    Abstract base class from which all the other data types are derived.
    '''

    @abc.abstractproperty
    def size(self):
        '''
        Return the size (in bytes) of this data type.
        '''

    @abc.abstractproperty
    def value(self):
        '''
        The value of this data type. You may implement getters and setters
        here.
        '''

    @abc.abstractclassmethod
    def from_hex(self, data, offset=0):
        '''
        Create a value of this type from an bytes iterable.
        '''

    @abc.abstractmethod
    def to_hex(self):
        '''
        Create a bytes object from this value.
        '''

    def __int__(self):
        return int(self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '{}(0x{:X})'.format(self.__class__.__name__, self.value)

    def __bytes__(self):
        return self.to_hex()

    @classmethod
    def create(cls, identifier, value):
        '''
        Creates a data type from the script reference spec.
        '''

        # Define the method that will actually do the creation
        if type(value) == int:
            def create_sub(cls):
                return cls(value)
        elif type(value) == bytes:
            def create_sub(cls):
                return cls.from_hex(value)
        elif isinstance(value, subscript.langtypes.Type):
            def create_sub(cls):
                return cls(value.value)
        else:
            raise ValueError(value)

        # Decode the identifier and delegate the creation to the method we made
        # earlier
        if identifier == 'byte':
            return create_sub(Byte)
        elif identifier == 'word':
            return create_sub(Word)
        elif identifier == 'dword':
            return create_sub(Dword)
        elif identifier == 'pointer':
            return create_sub(Pointer)
        elif identifier == 'variable':
            return create_sub(Variable)
        elif identifier == 'flag':
            return create_sub(Flag)
        elif identifier == 'bank':
            return create_sub(Bank)
        elif identifier == 'buffer':
            return create_sub(Buffer)
        elif identifier == 'hidden-variable':
            return create_sub(HiddenVar)
        elif identifier == 'pointer-or-bank':
            try:
                return create_sub(Bank)
            except ValueError:
                return create_sub(Pointer)
        elif identifier == 'pointer-or-bank-0':
            if value == 0:
                return create_sub(Bank)
            return create_sub(Pointer)
        elif identifier == 'flag-or-variable':
            try:
                return create_sub(Variable)
            except ValueError:
                return create_sub(Flag)
        elif identifier == 'word-or-variable':
            try:
                return create_sub(Variable)
            except ValueError:
                return create_sub(Word)
        elif identifier == 'byte-or-variable':
            try:
                return create_sub(Variable)
            except ValueError:
                return create_sub(Byte)
        else:
            raise ValueError('Invalid type identifier "{}"'.format(identifier))

class Byte(Type):
    def __init__(self, val):
        if val < 0 or val > 0xFF:
            raise ValueError('Value out of range')

        self._size = 1
        self._value = val

    @property
    def size(self):
        return self._size

    @property
    def value(self):
        return self._value

    def to_hex(self):
        return struct.pack('<B', self.value)

    @classmethod
    def from_hex(cls, data, offset=0):
        return cls(struct.unpack_from('<B', data, offset)[0])

class Word(Type):
    def __init__(self, val):
        if val < 0 or val > 0xFFFF:
            raise ValueError('Value out of range')

        self._size = 2
        self._value = val

    @property
    def size(self):
        return self._size

    @property
    def value(self):
        return self._value

    def to_hex(self):
        return struct.pack('<H', self.value)

    @classmethod
    def from_hex(cls, data, offset=0):
        return cls(struct.unpack_from('<H', data, offset)[0])

class Dword(Type):
    def __init__(self, val):
        if val < 0 or val > 0xFFFFFFFF:
            raise ValueError('Value out of range')

        self._size = 4
        self._value = val

    @property
    def size(self):
        return self._size

    @property
    def value(self):
        return self._value

    def to_hex(self):
        return struct.pack('<I', self.value)

    @classmethod
    def from_hex(cls, data, offset=0):
        return cls(struct.unpack_from('<I', data, offset)[0])

class Pointer(Dword):
    def __init__(self, val):
        super().__init__(val)

class DynamicPointer(Pointer):
    '''
    Represents a pointer to an undetermined location.
    '''

    def __init__(self, script, section):
        self._size = 4
        # TODO: Type checking
        self.script = script
        self.section = section

    @property
    def value(self):
        # A bit more complicated than a regular value

        target = self.script.sections.index(self.section)
        # TODO: Handle if target == -1 (shouldn't happen though)

        # Set the base pointer
        size = self.script.base

        # Add the size of all the sections before this one
        for i in range(target):
            size += self.script.sections[i].size

        return size

    @classmethod
    def from_hex(cls, data, offset=0):
        return None

    def __str__(self):
        return '@' + self.section.name

class RelativePointer(DynamicPointer):
    '''
    Dynamic pointer with a relative number of bytes.
    '''

    def __init__(self, script, section, offset=0):
        super().__init__(script, section)
        self.offset = offset

    @property
    def value(self):
        val = super().value
        target = self.script.sections.index(self.section)
        # Fix out by one error
        for i in range(self.offset + 1):
            val += self.script.sections[target].commands[i].size
        return val

    def __str__(self):
        return '@' + self.section.name + '+' + str(self.offset)

class Variable(Word):
    def __init__(self, val):
        if val < 0x3FFF:
            raise ValueError('Value out of range')
        # TODO: Warn about unsafe variables
        super().__init__(val)

class Flag(Word):
    def __init__(self, val):
        if val >= 0x900:
            raise ValueError('Value out of range')
        # TODO: Warn about unsafe/used flags
        super().__init__(val)

class Bank(Byte):
    def __init__(self, val):
        if val >= 4:
            raise ValueError('Value out of range')
        super().__init__(val)

class Buffer(Byte):
    def __init__(self, val):
        if val >= 3:
            raise ValueError('Value out of range')
        super().__init__(val)

class HiddenVar(Byte):
    def __init__(self, val):
        if val > 0x33:
            raise ValueError('Value out of range')
        # TODO: Warn about unsafe variables
        super().__init__(val)
