import subscript.compile
import argparse
import time

parser = argparse.ArgumentParser(description='Pokescript compiler.')

parser.add_argument('script', metavar='script', type=open, help='the script to compile')
parser.add_argument('--raw', metavar='file', dest='out_raw', type=argparse.FileType('wb'), help='write the compiled binary to a raw file')
parser.add_argument('--rom', metavar='file', dest='out_rom', type=argparse.FileType('rb+'), help='write the compiled binary to a ROM')
parser.add_argument('--offset', metavar='offset', dest='offset', type=int, default=0x740000, help='offset for ROM writing')

args = parser.parse_args()

times = []

tests = 100
for i in range(tests):
    start_time = time.process_time()
    c = subscript.compile.Compile(args.script.read(), args.offset + 0x8000000)
    end_time = time.process_time()
    times.append(end_time - start_time)

    # Seek to beginning of file to redo test
    args.script.seek(0)

mean = sum(times) / len(times)
print('Compiled {tests} times, mean compile time is {mean}'.format(tests=tests, mean=mean))
c.output()

data = c.bytecode()

if args.out_raw:
    args.out_raw.write(data)

if args.out_rom:
    args.out_rom.seek(args.offset)
    args.out_rom.write(data)

