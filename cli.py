import subscript.compile
import argparse

parser = argparse.ArgumentParser(description='Pokescript compiler.')

parser.add_argument('script', metavar='script', type=open, help='the script to compile')
parser.add_argument('--raw', metavar='file', dest='out_raw', type=argparse.FileType('wb'), help='write the compiled binary to a raw file')
parser.add_argument('--rom', metavar='file', dest='out_rom', type=argparse.FileType('rb+'), help='write the compiled binary to a ROM')
parser.add_argument('--offset', metavar='offset', dest='offset', type=int, default=0x740000, help='offset for ROM writing')

args = parser.parse_args()

c = subscript.compile.Compile(args.script.read(), args.offset + 0x8000000)

c.output()

data = c.bytecode()

if args.out_raw:
    args.out_raw.write(data)

if args.out_rom:
    args.out_rom.seek(args.offset)
    args.out_rom.write(data)

