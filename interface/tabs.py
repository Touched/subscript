from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib
import os
import interface.subscript

class Tabs(Gtk.Notebook):

    def __init__(self, window):
        super().__init__()
        self.set_size_request(-1, 700)
        self.window = window

        self.untitled_count = 0

    def open(self, path):
        # Check for duplicate tabs
        for page in self:
            if path == page.path:
                # The page is already open, set focus to it and leave
                index = self.page_num(page)
                self.set_current_page(index)
                return

        name = os.path.split(path)[1]

        ext = os.path.splitext(path)[1]

        if ext == '.sub':
            child = interface.subscript.SubscriptView(path)

        if child:
            index = self.add_page(name, child)
            self.show_all()

            # Switch focus to new tab
            self.set_current_page(index)

    def new(self, t):
        if t == 'subscript':
            child = interface.subscript.SubscriptView()

        if child:
            self.untitled_count += 1
            name = 'Untitled {}'.format(self.untitled_count)
            index = self.add_page(name, child)
            self.show_all()

            self.set_current_page(index)

    def save(self):
        pass

        n = self.get_current_page()

        if n == -1:
            return

        page = self.get_nth_page(n)

        if page.path == None:
            # Haven't saved yet, show file dialog
            dialog = Gtk.FileChooserDialog('Save script file', self.window, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

            filt = Gtk.FileFilter()
            filt.add_pattern("*.sub")
            filt.set_name("Subscript file")
            dialog.add_filter(filt)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                out = dialog.get_filename()

                _, ext = os.path.splitext(out)

                # Add extension if not present
                if not ext:
                    out += '.sub'
            else:
                # User cancelled save
                dialog.destroy()
                return

            dialog.destroy()
            page.path = out
        else:
            out = page.path

        # Now write to the file
        page.save()

    def add_page(self, name, tab, reorder=True):
        label = Gtk.HBox(spacing=5)
        icon = Gtk.Image.new_from_icon_name('text-x-script', Gtk.IconSize.MENU)
        label.add(icon)
        text = Gtk.Label(name)
        label.add(text)

        close = Gtk.Button.new_from_icon_name('window-close', Gtk.IconSize.MENU)
        close.set_relief(Gtk.ReliefStyle.NONE)
        label.add(close)

        index = self.append_page(tab, label)
        self.set_tab_reorderable(tab, reorder)

        close.connect('clicked', self.close_tab, tab)

        label.show_all()
        return index

    def close_tab(self, button, data=None):
        self.remove_page(self.page_num(data))