from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib
from gi.repository import GtkClutter
import os
import struct

import emulator
import subscript.compile

class SourceView(Gtk.ScrolledWindow):

    def __init__(self, language, path):
        super().__init__()

        self.manager = GtkSource.LanguageManager.new()
        self.manager.set_search_path(['assets/language-specs'])
        self.language = self.manager.get_language(language)

        self.buffer = GtkSource.Buffer.new_with_language(self.language)
        self.path = path
        if self.path != None:
            with open(self.path) as file:
                self.buffer.set_text(file.read())

        self.buffer.connect("apply-tag", self.tag_logger)
        self.buffer.connect("changed", self.make_dirty)

        style_manager = GtkSource.StyleSchemeManager()
        style_manager.set_search_path(['ssets/styles'])
        scheme = style_manager.get_scheme('kate')

        scheme = self.buffer.set_style_scheme(scheme)

        self.view = GtkSource.View.new_with_buffer(self.buffer)

        self.add(self.view)

        self.dirty = False

        self.view.props.auto_indent = True
        self.view.props.indent_width = 4
        self.view.props.highlight_current_line = True
        self.view.props.insert_spaces_instead_of_tabs = True
        self.view.props.show_line_numbers = True

        self.spelling = GtkSpell.Checker()
        self.spelling.set_language('en_US')
        self.spelling.attach(self.view)

        t = Gtk.TextTag.new('no-spell')
        t.props.underline = 0
        t.props.underline_set = True
        self.buffer.get_tag_table().add(t)

        fontdesc = Pango.FontDescription("Courier Pitch 10")
        self.view.modify_font(fontdesc)

        self.view.set_left_margin(5)
        self.view.set_right_margin(5)

    def tag_logger(self, buffer, tag, start, end, data=None):
        if tag.props.name == 'no-spell':
            return

        if tag.props.name != 'gtkspell-misspelled':
            s = buffer.get_context_classes_at_iter(start)
            t = buffer.get_tag_table().lookup('no-spell')

            # List of context classes to spell check
            types = ['comment', 'string']

            if any(x in s for x in types):
                buffer.remove_tag_by_name('no-spell', start, end)
                return

            if any(x not in s for x in types):
                buffer.apply_tag(t, start, end)
                return

    def make_dirty(self, buffer, data=None):
        if not self.dirty:
            parent = self
            widget = None

            # Find the desired parent
            while type(parent) != SourceTabs:
                widget = parent
                parent = parent.get_parent()

            title = parent.get_tab_label(widget)
            label = title.get_children()[1]
            text = label.get_text()
            label.set_text('*' + text)
            self.dirty = True

    def make_clean(self):
        if self.dirty:
            title = self.get_parent().get_tab_label(self)
            label = title.get_children()[1]
            text = label.get_text()
            label.set_text(text[1:])
            self.dirty = False

class Scripter(Gtk.VBox):

    def __init__(self, path):
        super().__init__()

        self.toolbar = Gtk.Toolbar(icon_size=Gtk.IconSize.MENU)
        button = Gtk.ToolButton(icon_name='system-run')
        button.set_tooltip_text('Compile')
        button.connect('clicked', self.compile)
        self.toolbar.add(button)

        self.pack_start(self.toolbar, False, False, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)

        self.source = SourceView('python3', path)
        self.add(self.source)


    def compile(self, widget):
        buffer = self.source.view.get_buffer()
#         if self.source.dirty:
#             self.confirm_save()
        text = buffer.props.text

        c = subscript.compile.Compile(text, 0x800000)
        #print(c.bytecode())
        out = self.get_parent().console
        out.console.get_buffer().props.text = c.status()

    def confirm_save(self):

        dialog = Gtk.MessageDialog(
                                       None,
                                       0,
                                       Gtk.MessageType.WARNING,
                                       Gtk.ButtonsType.YES_NO,
                                       "Do you want to save?",
                                       )
        dialog.run()
        dialog.destroy()

class SourceTabs(Gtk.Notebook):

    def __init__(self, console):
        super().__init__()
        self.set_size_request(-1, 700)
        self.console = console

    def open(self, path):
        # TODO: Check for duplicate tabs
        name = os.path.split(path)[1]

        ext = os.path.splitext(path)[1]

        if ext == '.sub':
            child = Scripter(path)
        elif ext == '.asm':
            child = SourceView('asm', path)

        if child:
            self.add_page(name, child)
            self.show_all()

    def add_page(self, name, tab, reorder=True):
        label = Gtk.HBox(spacing=5)
        icon = Gtk.Image.new_from_icon_name('text-x-script', Gtk.IconSize.MENU)
        label.add(icon)
        text = Gtk.Label(name)
        label.add(text)

        close = Gtk.Button.new_from_icon_name('window-close', Gtk.IconSize.MENU)
        close.set_relief(Gtk.ReliefStyle.NONE)
        label.add(close)

        self.append_page(tab, label)
        self.set_tab_reorderable(tab, reorder)

        close.connect('clicked', self.close_tab, tab)

        label.show_all()

    def close_tab(self, button, data=None):
        self.remove_page(self.page_num(data))

class Console(Gtk.ScrolledWindow):

    def __init__(self):
        super().__init__()
        self.console = GtkSource.View()

        self.console.props.cursor_visible
        self.console.props.editable = False

        self.set_shadow_type(Gtk.ShadowType.IN)

        # Draw leading spaces
        self.console.set_draw_spaces(GtkSource.DrawSpacesFlags.LEADING | GtkSource.DrawSpacesFlags.SPACE)
        self.console.set_insert_spaces_instead_of_tabs(True)
        self.console.set_tab_width(4)

        self.add(self.console)

class Menu(Gtk.MenuBar):

    def __init__(self):
        super().__init__()

        file = Gtk.MenuItem('File')
        file_menu = Gtk.Menu()
        file_menu.add(Gtk.MenuItem('New'))
        file_menu.add(Gtk.MenuItem('Open'))
        file.set_submenu(file_menu)
        self.add(file)

class Toolbar(Gtk.Toolbar):

    def __init__(self):
        super().__init__()

        button = Gtk.ToolButton(icon_name='document-new')
        self.add(button)
        button = Gtk.ToolButton(icon_name='document-save')
        self.add(button)
        button = Gtk.ToolButton(icon_name='document-open')
        self.add(button)

        self.add(Gtk.SeparatorToolItem())

        button = Gtk.ToolButton(icon_name='system-run')
        self.add(button)
        button = Gtk.ToolButton(icon_name='media-playback-start')
        button = Gtk.ToolButton(icon_name='process-stop')
        self.add(button)



class Explorer(Gtk.ScrolledWindow):

    def __init__(self):
        super().__init__()
        self.store = Gtk.TreeStore(str, str)

        self.set_min_content_width(300)

        self.size_request()

        self.set_shadow_type(Gtk.ShadowType.IN)

        self.tree = Gtk.TreeView(model=self.store)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
#         column_pixbuf = Gtk.TreeViewColumn("", renderer_pixbuf, stock_id=1)
        # column_pixbuf = Gtk.TreeViewColumn("", renderer_pixbuf, icon_name=True)
        # self.tree.append_column(column_pixbuf)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("")
        renderer_pixbuf.set_padding(3, 0)
        column_text.pack_start(renderer_pixbuf, False)
        column_text.pack_start(renderer_text, True)
        column_text.set_attributes(renderer_pixbuf, icon_name=True)
        column_text.set_attributes(renderer_text, text=False)
        self.tree.append_column(column_text)

        # No trailing slash
        self.root = '/home'

        self.tree.set_enable_tree_lines(True)

        self.add(self.tree)
        self.iters = {}
        self.iters[self.root] = None

        self.populate()

        self.tree.connect('row-activated', self.row_click)

    def populate(self):
        for root, folders, files in os.walk(self.root):
            if root == self.root:
                continue

            base, top = root.rsplit('/', 1)
            self.iters[root] = self.store.append(self.iters[base], [top, 'folder'])

            for file in files:
                name, ext = os.path.splitext(file)
                if ext == '.html':
                    icon = 'text-html'
                elif ext in ['.py', '.s']:
                    icon = 'text-x-script'
                else:
                    icon = 'text-x-generic'
                self.iters[os.path.join(root, file)] = self.store.append(self.iters[root], [file, icon])

    def row_click(self, tree, path, column):
        for loc, it in self.iters.items():
            if not it:
                continue
            p = self.store.get_path(it)

            if p == path:
                if os.path.isfile(loc):
                    self.get_toplevel().open_file(loc)
                elif os.path.isdir(loc):
                    if tree.row_expanded(path):
                        tree.collapse_row(path)
                    else:
                        tree.expand_row(path, False)

                break

class Breakpoints(Gtk.ScrolledWindow):

    def __init__(self):
        super().__init__()
        self.store = Gtk.ListStore(bool, str, int)
        self.store.append([True, 'Read/Write', 0x8800000])
        self.store.append([False, 'Read', 0x3456445])

        self.set_shadow_type(Gtk.ShadowType.IN)

        self.tree = Gtk.TreeView(model=self.store)

        # Breakpoint Enabled
        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect('toggled', self.toggle)
        column_toggle = Gtk.TreeViewColumn('Enabled', renderer_toggle, active=0)
        self.tree.append_column(column_toggle)

        # Breakpoint Type
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Type', renderer, text=1)
        self.tree.append_column(column)

        # Address
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Address', renderer, text=2)
        column.set_cell_data_func(renderer, self.format_address)
        self.tree.append_column(column)

        self.add(self.tree)

    def format_address(self, column, renderer, model, iter, dat=None):
        value = model.get_value(iter, 2)
        renderer.props.text = '{:08X}h'.format(value)

    def toggle(self, renderer, path):
        it = self.store.get_iter_from_string(path)
        state = not self.store.get_value(it, 0)
        self.store.set_value(it, 0, state)

class ScriptDebug(Gtk.VBox):
    '''
    A Pokescript debugger. Credit goes to Juan and Mastermind_X for documenting
    the structure in:
     - http://www.pokecommunity.com/showthread.php?t=204934
     - http://sfc.pokefans.net/hitchhikersguide.html
    '''

# struct Script{
#     u8  SubScriptsCount;
#     u8  Continue;
#     u16 ifFlag;
#     u32 THUMBRoutine;
#     u32 NextOffset;
#     u32 ReturnOffsets[20];
#     u32 CommandTablePointer;
#     u32 LastCommandPointer;
#     u32 MemoryBanks[4];
# }

    structure = struct.Struct('<B B H I I 20I I I 4I')
    address = 0x03000EB0  # Fire Red
    # 0x030006A4 - Ruby
    # 0x03000E40 - Emerald

    def __init__(self, emu):
        super().__init__()
        self.emu = emu

        self.connect('draw', self.loop)

        self.props.spacing = 5

        # The call stack
        label = Gtk.Label()
        label.set_markup('<b>Call Stack:</b>')
        self.pack_start(label, False, False, 0)
        self.call_store = Gtk.ListStore(int, int)
        self.call_tree = Gtk.TreeView(model=self.call_store)
        column = Gtk.TreeViewColumn('#', Gtk.CellRendererText(), text=0)
        self.call_tree.append_column(column)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Return Address', renderer, text=1)
        column.set_cell_data_func(renderer, self.format_address)
        self.call_tree.append_column(column)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.call_tree)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        self.add(scrolled)

        # Memory banks
        label = Gtk.Label()
        label.set_markup('<b>Memory Banks:</b>')
        self.pack_start(label, False, False, 0)
        self.bank_store = Gtk.ListStore(int, int)
        self.bank_store.append([1, 0x8800000])
        self.bank_store.append([2, 0x8800000])
        self.bank_store.append([3, 0x8800000])
        self.bank_store.append([4, 0x8800000])
        self.bank_tree = Gtk.TreeView(model=self.bank_store)
        column = Gtk.TreeViewColumn('Bank', Gtk.CellRendererText(), text=0)
        self.bank_tree.append_column(column)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Value', renderer, text=1)
        column.set_cell_data_func(renderer, self.format_address)
        self.bank_tree.append_column(column)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.bank_tree)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        self.add(scrolled)

        # Routine
        box = Gtk.HBox(spacing=5)
        label = Gtk.Label()
        label.set_markup('<b>Thumb Routine:</b>')
        box.pack_start(label, False, False, 0)
        self.routine = Gtk.Entry(editable=False)
        box.add(self.routine)
        self.pack_start(box, False, False, 0)

        # Control stuff
        box = Gtk.HBox(spacing=5)
        label = Gtk.Label()
        label.set_markup('<b>Next Byte:</b>')
        box.pack_start(label, False, False, 0)
        self.next_byte = Gtk.Entry()
        self.next_byte.set_tooltip_text('Offset of the next byte to be executed.')
        self.next_byte.connect('changed', self.set_next)
        box.add(self.next_byte)
        self.execute = Gtk.Switch()
        self.execute.set_tooltip_text('Script running')
        self.execute.connect('notify::active', self.start_script)
        box.pack_start(self.execute, False, False, 0)

        self.ignore = False
        self.update = True
        self.pack_start(box, False, False, 0)

        self._read_struct()

    def set_next(self, widget):
        if self.ignore:
            return

        try:
            value = int(widget.get_text(), base=16)
            widget.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0,0,0,1.0))
            self.emu.write(self.__class__.address + 8, struct.pack('<I', value))
            return True
        except ValueError:
            #widget.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse("green"))
            widget.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.9, 0.1,0.1,1.0))

    def start_script(self, widget, param):
        if self.ignore:
            return

        if widget.get_active():
            self.emu.write(self.__class__.address + 2, struct.pack('<B', 1))
        else:
            self.emu.write(self.__class__.address + 2, struct.pack('<B', 0))

    def format_address(self, column, renderer, model, iter, dat=None):
        value = model.get_value(iter, 1)
        renderer.props.text = '{:08X}'.format(value)

    def loop(self, *args):
        offset = self.emu.read(self.__class__.address, 4)
        o = int.from_bytes(offset, 'little')
        if self.update:
            self._read_struct()

    def _read_struct(self):
        data = self.emu.read(self.__class__.address, self.__class__.structure.size)
        fields = self.__class__.structure.unpack(data)
#
#         self.call_depth.set_markup('{}'.format(fields[0]))
#         self.continue_flag.set_markup('{}'.format('Yes' if fields[1] else 'No'))
#         self.compare_flag = fields[2]
#         self.routine.set_markup()
#         self.next = fields[4]
#         self.stack = fields[5:25]
#         self.table = fields[25]
#         self.last = fields[26]
#         self.banks = fields[27:]

        command_table = fields[25]

        self.emu.write(self.__class__.address + 2, struct.pack('<B', 0))

        self.routine.set_text('{:08X}'.format(fields[3]))
        self.ignore = True
        self.next_byte.set_text('{:08X}'.format(fields[4]))
        self.execute.set_active(bool(fields[1]))
        self.ignore = False

        for i in range(4):
            self.bank_store[i][1] = fields[27 + i]

        for i in range(20):
            if i < fields[0]:
                # There are entries in the call stack
                try:
                    # Replace the current item
                    self.call_store[i][1] = fields[5 + i]
                except IndexError:
                    # We need to append, old list shorter than new one
                    self.call_store.append([i + 1, fields[5 + i]])
            else:
                try:
                    # Remove excess entries
                    it = self.call_store[i].iter
                    self.call_store.remove(it)
                except IndexError:
                    # No more entries, leave the loop
                    break


class Debugger(Gtk.VBox):
    def __init__(self):
        super().__init__()
        self.props.spacing = 5
        self.emu = emulator.Emulator()
        self.emu.load('test.gba')
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        stack = Gtk.Stack()
        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        stack.add_titled(Breakpoints(), "breakpoints", "Breakpoints")
        self.script_debug = ScriptDebug(self.emu)
        stack.add_titled(self.script_debug, "script", "Script Debugger")
        self.pack_start(switcher, False, False, 0)
        self.add(stack)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(self.emu)
        self.pack_start(frame, False, False, 0)
        # self.add(Breakpoints())
        self.connect('destroy', self.quit)

        # Button group
        group = Gtk.HBox(spacing=5)

        button = Gtk.Button.new_from_icon_name('media-playback-start', Gtk.IconSize.MENU)
        button.set_tooltip_text('Start')
        button.connect('clicked', self.start)
        group.add(button)
        button = Gtk.Button.new_from_icon_name('media-playback-stop', Gtk.IconSize.MENU)
        button.set_tooltip_text('Stop')
        button.connect('clicked', self.stop)
        group.add(button)
        button = Gtk.Button.new_from_icon_name('go-next', Gtk.IconSize.MENU)
        button.set_tooltip_text('Next Frame')
        button.connect('clicked', self.next)
        group.add(button)
        button = Gtk.Button.new_from_icon_name('go-down', Gtk.IconSize.MENU)
        button.set_tooltip_text('Step into')
        button.connect('clicked', self.step_into)
        group.add(button)
        button = Gtk.Button.new_from_icon_name('go-jump', Gtk.IconSize.MENU)
        button.set_tooltip_text('Step over')
        button.connect('clicked', self.step_over)
        group.add(button)
        button = Gtk.Button.new_from_icon_name('go-up', Gtk.IconSize.MENU)
        button.set_tooltip_text('Step out')
        button.connect('clicked', self.step_out)
        group.add(button)

        self.connect('key-press-event', self.emu.screen.press)
        self.connect('key-release-event', self.emu.screen.release)

        self.pack_start(group, False, False, 0)
        # self.connect('draw', self.loop)
        self.active = False
        self.pause_on_next = False
        GObject.idle_add(self.loop)
        self.props.can_focus = True

    def start(self, widget):
        self.grab_focus()
        if self.active:
            self.active = False
            widget.set_image(Gtk.Image.new_from_icon_name('media-playback-start', Gtk.IconSize.MENU))
            self.script_debug.update = False
        else:
            self.active = True
            self.script_debug.update = True
            widget.set_image(Gtk.Image.new_from_icon_name('media-playback-pause', Gtk.IconSize.MENU))
            GObject.idle_add(self.loop)

    def stop(self, widget):
        pass

    def next(self, widget):
        self.active = True
        self.pause_on_next = True

    def step_into(self, widget):
        pass

    def step_over(self, widget):
        pass

    def step_out(self, widget):
        pass

    def quit(self, widget):
        self.emu.close()

    def loop(self, *args):
        if self.active:
            # Stops the emulator from losing focus
            self.grab_focus()
            if self.pause_on_next:
                self.active = False
                self.pause_on_next = False
            self.emu.loop()
            GObject.idle_add(self.loop)

class MyWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_default_size(240 * 4, 240 * 4)

        hb = Gtk.HeaderBar()
        hb.props.show_close_button = True
        hb.props.title = 'Test'
        hb.props.subtitle = 'Source'
        self.maximize()

        settings = Gtk.MenuButton()
        settings.set_image(Gtk.Image.new_from_icon_name('emblem-system-symbolic', Gtk.IconSize.MENU))

        hb.pack_end(settings)

        self.set_titlebar(hb)

        self.pane = Gtk.HPaned()
        self.set_border_width(5)

        self.box = Gtk.VBox(False)
        # self.box.pack_start(Menu(), False, False, 0)
        # self.box.pack_start(Toolbar(), False, False, 0)

        self.source = Gtk.VPaned()
        self.console = Console()
        self.tabs = SourceTabs(self.console)
        self.source.add(self.tabs)
        self.source.add(self.console)

        self.pane.add(Explorer())
        self.pane.add(self.source)

        self.hbox = Gtk.HBox(spacing=5)
        self.hbox.add(self.pane)
        self.hbox.pack_start(Debugger(), False, False, 0)

        self.box.add(self.hbox)
        self.box.pack_start(Gtk.Statusbar(), False, False, 0)

        self.add(self.box)

        self.connect('delete-event', Gtk.main_quit)

    def open_file(self, path):
        self.tabs.open(path)

win = MyWindow()
win.show_all()
Gtk.main()
