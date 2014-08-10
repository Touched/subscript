import json

class Parser:
    def __init__(self):
        self._output = bytearray()

        self._escape = False
        self._group = ''
        self._special = ''

    def feed(self, inp):
        for c in inp:
            if self._escape:
                self.escape(c)
                self._escape = False
            elif self._group:
                self._group += c
                if c == ']':
                    self.group(self._group[1:-1])
                    self._group = ''
            elif self._special:
                self._special += c
                if c == '}':
                    self.special(self._special[1:-1])
                    self._special = ''
            else:
                if c == '\\':
                    self._escape = True
                elif c == '[':
                    self._group = '['
                elif c == '{':
                    self._special = '{'
                else:
                    self.single(c)

    def single(self, letter):
        raise NotImplementedError

    def group(self, group):
        raise NotImplementedError

    def special(self, group):
        raise NotImplementedError

    def escape(self, char):
        raise NotImplementedError

    @property
    def output(self):
        return bytes(self._output)

class PoketextParser(Parser):
    def __init__(self):
        super().__init__()
        with open('tables/text.json') as table:
            self.table = json.loads(table.read())

    def single(self, letter):
        # Japanese Hiragana/Katakana is unicode between 0x3040 and 0x30FF
        if ord(letter) > 0x303F and ord(letter) < 0x3100:
            self._output.append(self.table['japanese'][letter])
        else:
            self._output.append(self.table['normal'][letter])

    def group(self, group):
        self._output.append(self.table['group'][group])

    def escape(self, group):
        self._output.append(self.table['escape'][group])

    def special(self, group):
        if group == 'black':
            self._output.extend(b'\xFC\x01\x01')

    @property
    def output(self):
        # Sentinel
        return bytes(self._output + b'\xFF')
