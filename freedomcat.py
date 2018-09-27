#!/usr/bin/env python
#
# "THE BEER-WARE LICENSE" (Revision 43~ktjubar)
#
# <maze@pyth0n.org> wrote these files, <ktjubar@vt.edu> modified them.
# As long as you retain this notice you can do whatever you want with
# this stuff. If we meet some day, and you think this stuff is worth it,
# you can buy me a beer in return.

import atexit
import math
import os
import random
import re
import sys
import time

PY3 = sys.version_info >= (3,)

# Reset terminal colors at exit
def reset():
    sys.stdout.write('\x1b[0m')
    sys.stdout.flush()

atexit.register(reset)


STRIP_ANSI = re.compile(r'\x1b\[(\d+)(;\d+)?(;\d+)?[m|K]')
COLOR_ANSI = (
    (0x00, 0x00, 0x00), (0xcd, 0x00, 0x00),
    (0x00, 0xcd, 0x00), (0xcd, 0xcd, 0x00),
    (0x00, 0x00, 0xee), (0xcd, 0x00, 0xcd),
    (0x00, 0xcd, 0xcd), (0xe5, 0xe5, 0xe5),
    (0x7f, 0x7f, 0x7f), (0xff, 0x00, 0x00),
    (0x00, 0xff, 0x00), (0xff, 0xff, 0x00),
    (0x5c, 0x5c, 0xff), (0xff, 0x00, 0xff),
    (0x00, 0xff, 0xff), (0xff, 0xff, 0xff),
)

class FreedomCat(object):
    def __init__(self, mode=256, output=sys.stdout):
        self.mode = mode
        self.output = output

    def _distance(self, rgb1, rgb2):
        return sum(map(lambda c: (c[0] - c[1]) ** 2,
            zip(rgb1, rgb2)))

    def ansi(self, rgb):
        r, g, b = rgb

        if self.mode in (8, 16):
            colors = COLOR_ANSI[:self.mode]
            matches = [(self._distance(c, map(int, rgb)), i) for i, c in enumerate(colors)]
            matches.sort()
            color = matches[0][1]

            return '3%d' % (color,)
        else:
            gray_possible = True
            sep = 2.5

            while gray_possible:
                if r < sep or g < sep or b < sep:
                    gray = r < sep and g < sep and b < sep
                    gray_possible = False

                sep += 42.5

            if gray:
                color = 232 + int(float(sum(rgb) / 33.0))
            else:
                color = sum([16]+[int(6 * float(val)/256) * mod
                    for val, mod in zip(rgb, [36, 6, 1])])

            return '38;5;%d' % (color,)

    def wrap(self, *codes):
        return '\x1b[%sm' % (''.join(codes),)

    # def rainbow(self, freq, i):
    #     r = math.sin(freq * i) * 127 + 128
    #     g = math.sin(freq * i + 2 * math.pi / 3) * 127 + 128
    #     b = math.sin(freq * i + 4 * math.pi / 3) * 127 + 128
    #     return [r, g, b]

    def cat(self, fd, options):
        for line in fd:
            self.println(line, options)

    def println(self, s, options):
        s = s.rstrip()
        if options.force or self.output.isatty():
            s = STRIP_ANSI.sub('', s)

        self.println_plain(s, options)

        self.output.write('\n')
        self.output.flush()

    def println_plain(self, s, options):
        for i, c in enumerate(s if PY3 else s.decode(options.charset_py2, 'replace')):
            # rgb = self.rainbow(options.freq, options.os + i / options.spread)
            rgb = [100, 100, 100]
            self.output.write(''.join([
                self.wrap(self.ansi(rgb)),
                c if PY3 else c.encode(options.charset_py2, 'replace'),
            ]))


def detect_mode(term_hint='xterm-256color'):
    '''
    Poor-mans color mode detection.
    '''
    if 'ANSICON' in os.environ:
        return 16
    elif os.environ.get('ConEmuANSI', 'OFF') == 'ON':
        return 256
    else:
        term = os.environ.get('TERM', term_hint)
        if term.endswith('-256color') or term in ('xterm', 'screen'):
            return 256
        elif term.endswith('-color') or term in ('rxvt',):
            return 16
        else:
            return 256 # optimistic default


def run():
    """Main entry point."""
    import optparse

    parser = optparse.OptionParser(usage=r'%prog [<options>] [file ...]')
    parser.add_option('-f', '--force', action='store_true', default=False,
        help='Force colour even when stdout is not a tty')

    parser.add_option('-3', action='store_const', dest='mode', const=8,
        help='Force 3 bit colour mode')
    parser.add_option('-4', action='store_const', dest='mode', const=16,
        help='Force 4 bit colour mode')
    parser.add_option('-8', action='store_const', dest='mode', const=256,
        help='Force 8 bit colour mode')

    parser.add_option('-c', '--charset-py2', default='utf-8',
            help='Manually set a charset to convert from, for python 2.7')

    options, args = parser.parse_args()
    options.mode = options.mode or detect_mode()

    freedomcat = FreedomCat(mode=options.mode)

    if not args:
        args = ['-']

    for filename in args:
        if filename == '-':
            freedomcat.cat(sys.stdin, options)
        else:
            try:
                with open(filename, 'r') as handle:
                    freedomcat.cat(handle, options)
            except IOError as error:
                sys.stderr.write(str(error) + '\n')

if __name__ == '__main__':
    sys.exit(run())
