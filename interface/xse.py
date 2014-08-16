'''
XSE-style widgets
'''

from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib
import webbrowser

class Toolbar(Gtk.HBox):

    def __init__(self, window):
        super().__init__()

        self.window = window

        self.rom = Gtk.FileChooserButton.new('Load a ROM', Gtk.FileChooserAction.OPEN)

        filt = Gtk.FileFilter()
        filt.add_pattern("*.gba")
        filt.set_name("GBA ROM")
        self.rom.add_filter(filt)

        self.rom.set_tooltip_text('Select a ROM')
        self.rom.connect('file-set', self.open_rom)

        self.pack_start(self.rom, False, False, 0)

        toolbar = Gtk.Toolbar()
        toolbar.add(Gtk.SeparatorToolItem())

        button = Gtk.ToolButton(icon_name='document-new')
        button.set_tooltip_text('New script file')
        button.connect('clicked', self.new_file)
        toolbar.add(button)
        button = Gtk.ToolButton(icon_name='document-open')
        button.set_tooltip_text('Open a script file')
        button.connect('clicked', self.open_file)
        toolbar.add(button)
        button = Gtk.ToolButton(icon_name='document-save')
        button.set_tooltip_text('Save a script file')
        button.connect('clicked', self.save_file)
        toolbar.add(button)

        toolbar.add(Gtk.SeparatorToolItem())

        button = Gtk.ToolButton(icon_name='system-run')
        button.set_tooltip_text('Compile script to ROM')
        button.set_sensitive(False)
        button.connect('clicked', self.compile)
        self.compile = button
        toolbar.add(button)
        button = Gtk.ToolButton(icon_name='edit-clear')
        button.set_tooltip_text('Clear last compile')
        button.connect('clicked', self.clean)
        toolbar.add(button)

        toolbar.add(Gtk.SeparatorToolItem())

        button = Gtk.ToolButton(icon_name='help-contents')
        button.set_tooltip_text('View script command help')
        button.connect('clicked', self.help)
        toolbar.add(button)
        button = Gtk.ToolButton(icon_name='help-about')
        button.connect('clicked', self.about)
        button.set_tooltip_text('About')
        toolbar.add(button)

        self.add(toolbar)

    def open_rom(self, widget, data=None):
        self.compile.set_sensitive(True)
        self.window.rom = widget.get_filename()

    def open_file(self, widget, data=None):
        dialog = Gtk.FileChooserDialog('Open script file', self.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        filt = Gtk.FileFilter()
        filt.add_pattern("*.sub")
        filt.set_name("Subscript file")
        dialog.add_filter(filt)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.window.open(dialog.get_filename())

        dialog.destroy()

    def save_file(self, widget, data=None):
        self.window.save()

    def new_file(self, widget, data=None):
        self.window.new()

    def compile(self, widget, data=None):
        self.window.compile()

    def clean(self, widget, data=None):
        self.window.clean()

    def help(self, widget, data=None):
        webbrowser.open('_build/html/index.html')

    def about(self, widget, data=None):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name('Subscript')
        dialog.set_version('1.0')
        dialog.set_comments('A Pokescript editor with Python syntax.')
        dialog.set_authors(['Touched', 'itari'])
        dialog.add_credit_section('Command Documenters', ['DavidJCobb', 'Spherical Ice'])

        dialog.run()
        dialog.destroy()

