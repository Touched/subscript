from gi.repository import Gtk, GObject, Gdk
import cairo
import random
import string

class Hex(Gtk.HBox):

    gridlines = GObject.property(type=bool, default=True)
#
#     hadjustment = GObject.property(type=Gtk.Adjustment)
#     vadjustment = GObject.property(type=Gtk.Adjustment)
#     vscroll_policy = GObject.property(type=Gtk.ScrollablePolicy, default=Gtk.ScrollablePolicy.NATURAL)
#     hscroll_policy = GObject.property(type=Gtk.ScrollablePolicy, default=Gtk.ScrollablePolicy.MINIMUM)

    def __init__(self):
        self.data_length = 10000
        self.data = bytearray(random.randint(0, 255) for _ in range(self.data_length))

        super().__init__()

        self.canvas = Gtk.DrawingArea()
        self.canvas.connect('draw', self.draw)
        self.canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON_MOTION_MASK)
        self.canvas.connect('button-press-event', self.click_press)
        self.canvas.connect('button-release-event', self.click_release)
        self.canvas.connect('motion-notify-event', self.move)
        self.add(self.canvas)

        self.scrollbar = Gtk.Scrollbar.new(Gtk.Orientation.VERTICAL, None)
        self.scrollbar.connect('value-changed', self.do_scroll)
        self.adjustment = self.scrollbar.get_adjustment()
        self.adjustment.props.upper = 1.0
        self.adjustment.props.page_size = 0.1
        self.pack_start(self.scrollbar, False, False, 0)

        self.selected = []

        self._gridlines = True
        # self.canvas.set_size_request(-1, 100);

        self.cell_size = 0
        self.cells_per_row = 14
        self.offset_size = 0
        self.text_size = 0
        self.row = 0

        self.top = 0

        self.start_cell = -1

    def coords_to_cell(self, x_rel, y_rel):
        if self.offset_size < x_rel < self.text_size:
            # Clicked a hex byte
            y = y_rel // self.cell_size
            x = (x_rel - self.offset_size) // self.cell_size

            hidden = self.row * (self.cells_per_row + 1)
            skip = y * (self.cells_per_row + 1)
            cell = x + skip + hidden
            return int(cell)
        return -1

    def click_press(self, widget, event, data=None):
        self.start_cell = self.coords_to_cell(event.x, event.y)

    def move(self, widget, event, data=None):
        if self.start_cell == -1:
            return

        cell = self.coords_to_cell(event.x, event.y)

        if cell != -1:
            if cell >= self.start_cell:
                self.selected = range(self.start_cell, cell + 1)
            else:
                self.selected = range(self.start_cell, cell -1, -1)
            self.canvas.queue_draw()
        else:
            self.selected = []

    def click_release(self, widget, event, data=None):
        cell = self.coords_to_cell(event.x, event.y)
        if cell != -1:
            if cell >= self.start_cell:
                self.selected = range(self.start_cell, cell + 1)
            else:
                self.selected = range(self.start_cell, cell -1, -1)
            self.canvas.queue_draw()

    def drag_start(self):
        pass

    def do_scroll(self, *args):
        val = self.adjustment.props.value
        dif = self.adjustment.props.upper

        scrolled_percent = val / dif
        rows = self.data_length / self.cells_per_row
        target = rows * scrolled_percent
        self.row = int(target)

#         self.top = self.top - 1
#         if abs(self.top) >= self.cell_size:
#             self.top = 0
#             #self.row += 1
        self.canvas.queue_draw()

    def draw(self, widget, cr):

        colors = {
                  'selected': (173 / 255, 216 / 255, 230 / 255)
                  }

        cr.select_font_face('monospace')
        font_size = 12
        padding = 5
        cr.set_font_size(font_size)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()

        width = 300
        height = self.get_allocated_height()

        top = self.top

        # Get widths with dummy text
        offsets_width = int(cr.text_extents('00000000')[2]) + padding * 2
        bytes_width = int(cr.text_extents('00')[2]) + padding * 2

        # Calculate the width of the text table
        char_width = int(cr.text_extents('.')[2]) + padding * 2
        text_width = char_width * self.cells_per_row  + padding * 2
        hex_end = width - text_width

        self.offset_size = offsets_width
        self.text_size = hex_end - (hex_end % bytes_width) - padding

        self.cell_size = bytes_width

        # Grid lines
        if self.props.gridlines:
            cr.set_dash([2, 2])
            # cr.set_line_cap(cairo.LINE_CAP_BUTT)
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.set_line_width(1)

            # Horizontal grid lines
            for y in range(0, height, bytes_width):
                cr.move_to(0, y + 0.5 + top)
                cr.line_to(width, y + 0.5 + top)
                cr.stroke()

            # Vertical grid lines
            for x in range(offsets_width , hex_end, bytes_width):
                cr.move_to(x + 0.5, 0 + top)
                cr.line_to(x + 0.5, height + top)
                cr.stroke()

        # Shade offset row
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.rectangle(0, 0, offsets_width, height)
        cr.fill()

        def toggle_color():
            while True:
                yield cr.set_source_rgb(0, 0, 0)
                yield cr.set_source_rgb(0.4, 0.4, 0.4)

        n = -1

        selected = self.selected

        it = enumerate(self.data)
        alternate = toggle_color()

        try:
            # Skip rows
            skipped = 0
            for _ in range(self.row):
                for x in range(offsets_width , hex_end - bytes_width, bytes_width):
                    n, byte = next(it)
                    next(alternate)
                    skipped += 1

            for y in range(0, height + bytes_width, bytes_width):
                cr.set_source_rgb(0, 0, 0)
                cr.move_to(padding, bytes_width - font_size / 2 + y + top)
                cr.show_text('{:08X}'.format(n + 1))

                # Subtract bytes_width to stop bytes being hidden on a small resize
                for x in range(offsets_width , hex_end - bytes_width, bytes_width):

                    # Shade selected
                    if (n + 1) in selected:
                        cr.set_source_rgb(*colors['selected'])
                        cr.rectangle(x, y + top, bytes_width + 1, bytes_width + 1)
                        cr.fill()

                    next(alternate)
                    n, byte = next(it)
                    cr.move_to(x + padding, bytes_width - font_size / 2 + y + top)
                    cr.show_text('{:02X}'.format(byte))

                    # Draw the text byte
                    pos = n % self.cells_per_row * char_width + padding + hex_end
                    cr.move_to(pos, bytes_width - font_size / 2 + y + top)

                    if 0x1F < byte < 0x7F:
                        # If printable ascii
                        cr.show_text(chr(byte))
                    else:
                        cr.show_text('.')
        except StopIteration:
            pass


        # Draw divider
        cr.set_dash([1])
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.move_to(offsets_width + 0.5, 0.5)
        cr.line_to(offsets_width + 0.5, height + 0.5)
        cr.stroke()

        # Draw divider
        cr.set_dash([1])
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.move_to(hex_end - 0.5, 0.5 + top)
        cr.line_to(hex_end - 0.5, height + 0.5)
        cr.stroke()



class MyWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_default_size(240 * 2, 240 * 2)

        hb = Gtk.HeaderBar()
        hb.props.show_close_button = True
        hb.props.title = 'Test'
        hb.props.subtitle = 'Source'

        self.hex = Hex()
        self.add(self.hex)

        self.connect('delete-event', Gtk.main_quit)

win = MyWindow()
win.show_all()
Gtk.main()
