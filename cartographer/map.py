import cartographer.drawing
import cairo
import struct
from gi.repository import Gtk, GObject, Gdk

# static unsafe public bool UnCompress(BinaryReader br, int offset, byte* destination) {
#     br.BaseStream.Position = offset;
#     int size = br.ReadInt32();
#     int uncompPosition = 0;
#
#     if (!((size & 0xFF) == 0x10))
#         return false;
#
#     size >>= 8;
#
#     while ((uncompPosition < size) && (br.BaseStream.Position < br.BaseStream.Length)) {
#         byte isCompressed = br.ReadByte();
#
#         for (int i = 0; i < BlockSize; i++) {
#             if ((isCompressed & 0x80) != 0) {
#                 byte first = br.ReadByte();
#                 byte second = br.ReadByte();
#                 ushort Position = (ushort)((((first << 8) + second) & 0xFFF) + 1);
#                 byte AmountToCopy = (byte)(3 + ((first >> 4) & 0xF));
#
#                 if (Position > uncompPosition)
#                     return false;
#
#                 for (int u = 0; u < AmountToCopy; u++)
#                     *(destination + uncompPosition + u) = *(destination + uncompPosition - Position + (u % Position));
#
#                 uncompPosition += AmountToCopy;
#             }
#             else {
#                 *(destination + uncompPosition++) = br.ReadByte();
#             }
#             if (!(uncompPosition < size) && (br.BaseStream.Position < br.BaseStream.Length))
#                 break;
#
#             isCompressed <<= 1;
#         }
#     }
#     return !(uncompPosition < size);
# }

def uncompress(file):
    size = int.from_bytes(file.read(3), 'little')
    if not size:
        size = int.from_bytes(file.read(4), 'little')

    uncompPosition = 0;

    destination = bytearray(size)

#     if not ((size & 0xFF) == 0x10):
#         return False

    size >>= 8

    while (uncompPosition < size):
        isCompressed = int(file.read(1)[0])

        for _ in range(8):
            if (isCompressed & 0x80) != 0:
                first = int(file.read(1)[0])
                second = int(file.read(1)[0])
                Position = (((first & 0xF) << 8) | second)
                AmountToCopy = (3 + ((first >> 4) & 0xF))

                if Position > uncompPosition:
                    return False

                for u in range(AmountToCopy):
                    destination[uncompPosition + u] = destination[uncompPosition - Position + (u % Position)]
                    uncompPosition += 1

            else:
                destination[uncompPosition] = int(file.read(1)[0])
                uncompPosition += 1
            if not (uncompPosition < size):
                break

            isCompressed <<= 1;
    return destination

class MyWindow(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.set_default_size(240 * 2, 240 * 2)

        self.canvas = Gtk.DrawingArea()
        self.canvas.connect('draw', self.draw)
        self.add(self.canvas)

        self.connect('delete-event', Gtk.main_quit)

    def draw(self, w, cr):
        with open('test.gba', 'rb') as file:
            file.seek(0x297091)
            compressed_type = 0
            data = False
            while compressed_type != 0x10 or not data:
                compressed_type = int(file.read(1)[0])

                data = uncompress(file)

        pixels = bytearray()

        for byte in data:
            first, second = (byte & 0xF), (byte >> 4)
            pixels.extend([first << 4] * 3)
            pixels.extend([second << 4] * 3)

        data = bytes(pixels)

        surface = cartographer.drawing.data_surface(data, cairo.FORMAT_RGB24, 256, 64)
        cr.set_source_surface(surface)
        cr.paint()



win = MyWindow()
win.show_all()
Gtk.main()

