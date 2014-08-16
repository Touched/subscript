import interface.tabs
import interface.xse
import subscript.compile
from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib

class MyWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_border_width(5)

        self.set_default_size(240 * 4, 240 * 4)

        self.set_title('Subscript')
        #self.maximize()

        self.box = Gtk.VBox()

        # Toolbar

        tb = interface.xse.Toolbar(self)
        self.box.pack_start(tb, False, False, 0)

        # Tab view
        #path = '/home/james/here/code/test.sub'
        self.tabs = interface.tabs.Tabs(self)
        self.box.add(self.tabs)
        #self.tabs.open(path)

        self.last_compile = None

        self.add(self.box)

        self.connect('delete-event', Gtk.main_quit)
        self.rom = None

    def load(self, rom):
        self.rom = rom

    def open(self, file):
        self.tabs.open(file)

    def save(self):
        self.tabs.save()

    def new(self):
        self.tabs.new('subscript')

    def clean(self):
        if self.last_compile != None:
            with open(self.rom, 'rb+') as rom:
                rom.seek(self.last_compile[0])
                wipe = bytes(0xFF for _ in range(len(self.last_compile[1])))
                rom.write(wipe)

    def compile(self):
        index = self.tabs.get_current_page()
        page = self.tabs.get_nth_page(index)

        start = 0x800000

        text = page.buffer.props.text
        script = subscript.compile.Compile(text, 0xDEADBEEF)
        size = len(script.bytecode())

        with open(self.rom, 'rb') as rom:
            rom.seek(start)
            for chunk in iter(lambda: rom.read(size), b''):
                if all(byte == 0xFF for byte in chunk) and len(chunk) == size:
                    break
            else:
                # We reached the end of file, throw error
                dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "No free space")
                dialog.format_secondary_text("Subscript could not find enough free space to insert your script.")
                dialog.run()

                dialog.destroy()
                return

            offset = rom.tell() - size

        script.script.base = offset + 0x08000000
        data = script.bytecode()

        with open(self.rom, 'rb+') as rom:
            rom.seek(offset)
            rom.write(data)

            self.last_compile = (offset, data)

            dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "Success!")
            dialog.format_secondary_text("Inserted your script at 0x{:6x}.".format(offset))
            dialog.run()
            dialog.destroy()

win = MyWindow()
win.show_all()
Gtk.main()
