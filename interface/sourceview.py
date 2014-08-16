from gi.repository import Gtk, Gio, GObject, Gdk, GtkSource, Pango, GtkSpell, Clutter, GLib

class Completion(GtkSource.CompletionWords):

    def __init__(self, **kwargs):
        GObject.Object.__init__(self)

        self.priority = 1

        theme = Gtk.IconTheme.get_default()
        icon = theme.load_icon(Gtk.STOCK_DIALOG_INFO, 16, 0)

        self.proposals = []
        self.proposals.append(GtkSource.CompletionItem.new("Proposal 1", "Proposal 1", icon, "blah 1"))
        self.proposals.append(GtkSource.CompletionItem.new("Proposal 2", "Proposal 2", icon, "blah 2"))
        self.proposals.append(GtkSource.CompletionItem.new("Proposal 3", "Proposal 3", icon, "blah 3"))

    def do_get_name(self):
        return "Test Provider"

    def do_get_priority(self):
        return self.priority

    def do_match(self, context):
        end = context.get_iter()

        # Sample selection of text
        start = end.copy()
        start.backward_word_start()
        text = start.get_text(end)

        print(text)

        return True

    def do_populate(self, context):
        context.add_proposals(self, self.proposals, True)

    def set_priority(self, priority):
        self.priority = priority

class SourceView(Gtk.ScrolledWindow):

    def __init__(self, lang, style, path=None):
        '''
        Constructor
        '''
        super().__init__()

        self.manager = GtkSource.LanguageManager.new()
        self.manager.set_search_path(['assets/language-specs'])
        self.language = self.manager.get_language(lang)

        self.buffer = GtkSource.Buffer.new_with_language(self.language)
        self.path = path
        if self.path != None:
            with open(self.path) as file:
                self.buffer.begin_not_undoable_action()
                self.buffer.set_text(file.read())
                self.buffer.end_not_undoable_action()

        style_manager = GtkSource.StyleSchemeManager()
        style_manager.set_search_path(['assets/styles'])
        scheme = style_manager.get_scheme(style)

        scheme = self.buffer.set_style_scheme(scheme)

        self.view = GtkSource.View.new_with_buffer(self.buffer)

        self.add(self.view)

        self.dirty = False

        self.view.props.auto_indent = True
        self.view.props.indent_width = 4
        self.view.props.highlight_current_line = True
        self.view.props.insert_spaces_instead_of_tabs = True
        self.view.props.show_line_numbers = True

        self.view.connect('draw', self.draw_gutter)

        self.completion = self.view.get_completion()
        provider = Completion(name='Test')
        #provider.register(self.buffer)
        self.completion.add_provider(provider)


        #self.spelling = GtkSpell.Checker()
        #self.spelling.set_language('en_US')
        #self.spelling.attach(self.view)

        #t = Gtk.TextTag.new('no-spell')
        #t.props.underline = 0
        #t.props.underline_set = True
        #self.buffer.get_tag_table().add(t)

        fontdesc = Pango.FontDescription("Courier Pitch 10")
        self.view.modify_font(fontdesc)

        self.view.set_left_margin(5)
        self.view.set_right_margin(5)

        self.formatted = False

    def hex_to_cairo(self, color):
        if len(color) != 7 or color[0] != '#':
            return (0, 0, 0)

        color = color[1:].lower()
        if any(c not in '0123456789abcdef' for c in color):
            return (0, 0, 0)

        out = tuple(int(color[i:i + 2], 16) / 255 for i in range(0, 6, 2))

        return out

    def save(self):
        with open(self.path, 'w') as file:
            file.write(self.buffer.props.text)

    def draw_gutter(self, view, cr):
        '''
        Draws a line on the line number gutter
        '''
        height = view.get_allocated_height()

        width = 0
        x, _ = cr.get_current_point()

        # Calculate the size of the gutter
        while True:
            gutter = view.get_gutter(Gtk.TextWindowType.LEFT)
            renderer = gutter.get_renderer_at_pos(width + x, 0)

            if renderer == None:
                break

            width += renderer.get_size()
            width += renderer.get_padding()[0]
            width += renderer.get_padding()[0] - 1

        cr.set_source_rgb(*self.hex_to_cairo('#b3b3b3'))
        cr.set_line_width(1)
        cr.move_to(width + .5, 0)
        cr.line_to(width + .5, height)
        cr.stroke()

