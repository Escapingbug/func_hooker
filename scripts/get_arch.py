import sys
from elftools.elf.elffile import ELFFile

def main():
    if len(sys.argv) < 2:
        print('Usage: {} binfile')
        return 0

    with open(sys.argv[1], 'rb') as f:
        elf = ELFFile(f)
        if elf.elfclass == 32:
            print('x86')
        else:
            print('x86_64')


if __name__ == '__main__':
    main()