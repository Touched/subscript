from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib
import struct

class Observer(Gtk.ScrolledWindow):
    '''
    classdocs
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
        super().__init__()

        self.store = Gtk.TreeStore(int, str, int, str)

        self.set_shadow_type(Gtk.ShadowType.IN)

        self.tree = Gtk.TreeView(model=self.store)

        self.append(12323, 'II3I')

        # Address
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Address', renderer, text=0)
        column.set_cell_data_func(renderer, self.format_address)
        self.tree.append_column(column)

        # Address
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Type', renderer, text=1)
        self.tree.append_column(column)

        # Address
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Size', renderer, text=2)
        self.tree.append_column(column)

        # Address
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Value', renderer, text=3)
        self.tree.append_column(column)

        self.add(self.tree)

    def format_address(self, column, renderer, model, it, dat=None):
        value = model.get_value(it, 0)
        renderer.props.text = '{:08X}h'.format(value)

    def append(self, address, fmt):
        s = struct.Struct(fmt)
        print(s)

        it = self.store.append(None, [address, 'struct', 36, '...'])

        self.store.append(it, [address, 'struct', 36, '...'])

