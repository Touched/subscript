import interface.observer
from gi.repository import Gtk

class MyWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_default_size(240 * 2, 240 * 2)

        data = bytearray(100)

        self.w = interface.observer.Observer(data)
        self.add(self.w)

        self.connect('delete-event', Gtk.main_quit)

    def open_file(self, path):
        self.tabs.open(path)

win = MyWindow()
win.show_all()
Gtk.main()