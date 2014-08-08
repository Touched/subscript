from gi.repository import Gtk, Gdk
import atlantis
import threading

class Screen(Gtk.DrawingArea):
    # Key mapping constants
    BUTTON_A = 1
    BUTTON_B = 2
    BUTTON_SELECT = 4
    BUTTON_START = 8
    BUTTON_DPAD_RIGHT = 16
    BUTTON_DPAD_LEFT = 32
    BUTTON_DPAD_UP = 64
    BUTTON_DPAD_DOWN = 128
    BUTTON_R = 256
    BUTTON_L = 512
    BUTTON_SPEED = 1024
    BUTTON_SCREENSHOT = 2048

    # Default key mapping
    keymap = {
       'z': BUTTON_A,
       'x': BUTTON_B,
       'a': BUTTON_L,
       's': BUTTON_R,
       'Up': BUTTON_DPAD_UP,
       'Down': BUTTON_DPAD_DOWN,
       'Left': BUTTON_DPAD_LEFT,
       'Right': BUTTON_DPAD_RIGHT,
       'Return': BUTTON_START,
       'BackSpace': BUTTON_SELECT,
       'space': BUTTON_SPEED,
    }

    def __init__(self, keymap=None):
        super().__init__()

        if keymap:
            self.keymap = keymap
        else:
            self.keymap = self.__class__.keymap
        self.set_size_request(240 * 2, 160 * 2)

        self.connect('draw', atlantis.draw)
        self.connect('key-press-event', self.press)
        self.connect('key-release-event', self.release)

    def press(self, widget, event, user_data=None):
        key = Gdk.keyval_name(event.keyval)
        if key not in self.keymap:
            return

        atlantis.press(self.keymap[key])

    def release(self, widget, event, user_data=None):
        key = Gdk.keyval_name(event.keyval)
        if key not in self.keymap:
            return

        atlantis.release(self.keymap[key])

class Emulator(Gtk.Bin):
    def __init__(self):
        super().__init__()
        self.screen = Screen()
        self.add(self.screen)

    def load(self, path):
        atlantis.init()
        atlantis.load(path)

#         t = threading.Thread(target=self.loop)
#         t.daemon = False
#         t.start()

        return self

    def focus(self, focus=True):
        self.set_can_focus(focus)
        if focus:
            self.grab_focus(self )

    def close(self):
        atlantis.finalize()

    def loop(self):
        return atlantis.iteration()

    def disassemble(self, offset, mode='thumb'):
        if mode == 'thumb':
            return atlantis.disassemble_thumb(offset)
        elif mode == 'arm':
            return atlantis.disassemble_arm(offset)

    def _read(self, address):
        index, view = self._address(address)
        return view[index]

    def _write(self, address, value):
        index, view = self._address(address)
        view[index] = value

    def _address(self, address):

        if 0x0000000 <= address <= 0x0003FFF:
            view = atlantis.bios()
        elif 0x2000000 <= address <= 0x203FFFF:
            view = atlantis.wram()
            address -= 0x2000000
        elif 0x3000000 <= address <= 0x3007FFF:
            view = atlantis.iram()
            address -= 0x3000000
        elif 0x4000000 <= address <= 0x40003FE:
            view = atlantis.io()
            address -= 0x4000000
        elif 0x5000000 <= address <= 0x50003FF:
            view = atlantis.pal()
            address -= 0x5000000
        elif 0x6000000 <= address <= 0x6017FFF:
            view = atlantis.vram()
            address -= 0x6000000
        elif 0x7000000 <= address <= 0x70003FF:
            view = atlantis.oam()
            address -= 0x7000000
        elif 0x8000000 <= address <= 0x9FFFFFF:
            view = atlantis.rom()
            address -= 0x8000000
        elif 0xA000000 <= address <= 0xBFFFFFF:
            view = atlantis.rom()
            address -= 0xA000000
        elif 0xC000000 <= address <= 0xDFFFFFF:
            view = atlantis.rom()
            address -= 0xC000000
        else:
            raise ValueError('Address out of range')

        return address, view

    def read(self, address, length=1):
        out = bytearray()
        for i in range(length):
            out.append(self._read(address + i))
        return bytes(out)

    def write(self, address, data):
        for i in data:
            self._write(address, int(i))
